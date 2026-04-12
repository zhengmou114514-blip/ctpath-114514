from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import datetime, timezone
from typing import Iterable, List
from urllib import error, parse, request

from ..env_loader import load_env_file
from ..schemas import (
    AdviceMeta,
    AdviceResponse,
    EvidenceSummary,
    MedicationPlanItem,
    MedicationPlanResponse,
    PatientQuadruple,
    PatientUpsertRequest,
    PredictionItem,
)


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _dedupe_text(items: Iterable[str], *, limit: int | None = None) -> List[str]:
    result: List[str] = []
    for item in items:
        text = str(item).strip()
        if not text:
            continue
        if text in result:
            continue
        result.append(text)
        if limit is not None and len(result) >= limit:
            break
    return result


class LLMAdviceService:
    def __init__(self) -> None:
        self._cache: dict[str, tuple[float, AdviceResponse]] = {}
        self._medication_cache: dict[str, tuple[float, MedicationPlanResponse]] = {}
        self._patient_last_remote: dict[str, float] = {}
        self._patient_last_cache_key: dict[str, str] = {}
        self._refresh_settings()

    def _refresh_settings(self) -> None:
        self.provider = os.getenv("CTPATH_LLM_PROVIDER", "deepseek").strip() or "deepseek"
        self.model = os.getenv("CTPATH_LLM_MODEL", "deepseek-chat").strip() or "deepseek-chat"
        self.base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").strip() or "https://api.deepseek.com"
        self.chat_path = os.getenv("DEEPSEEK_CHAT_PATH", "/chat/completions").strip() or "/chat/completions"
        self.api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
        self.enabled = _env_flag("CTPATH_LLM_ENABLED", default=False)
        self.timeout = _env_float("CTPATH_LLM_TIMEOUT", 40.0)
        self.cache_ttl = _env_int("CTPATH_LLM_CACHE_TTL", 300)
        self.min_interval = _env_int("CTPATH_LLM_MIN_INTERVAL", 30)
        self.max_cache_items = _env_int("CTPATH_LLM_CACHE_MAX_ITEMS", 256)

    def _reload_runtime_config(self) -> None:
        load_env_file(override=True)
        self._refresh_settings()

    def _should_call_remote(self) -> bool:
        return self.enabled and self.provider.lower() == "deepseek" and bool(self.api_key)

    def _cache_key(self, payload: dict) -> str:
        body = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(body.encode("utf-8")).hexdigest()

    def _evict_expired_cache(self, cache: dict) -> None:
        if self.cache_ttl <= 0:
            cache.clear()
            return
        now = time.time()
        expired = [key for key, (created_at, _response) in cache.items() if now - created_at > self.cache_ttl]
        for key in expired:
            cache.pop(key, None)

    def _trim_cache(self, cache: dict) -> None:
        self._evict_expired_cache(cache)
        if len(cache) <= self.max_cache_items:
            return
        ordered = sorted(cache.items(), key=lambda item: item[1][0])
        remove_count = max(0, len(cache) - self.max_cache_items)
        for key, _value in ordered[:remove_count]:
            cache.pop(key, None)

    def _call_deepseek(self, payload: dict) -> str:
        endpoint = parse.urljoin(self.base_url.rstrip("/") + "/", self.chat_path.lstrip("/"))
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = request.Request(
            endpoint,
            data=body,
            headers={
                "Authorization": "Bearer {0}".format(self.api_key),
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                content = response.read().decode("utf-8")
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError("HTTP {0}: {1}".format(exc.code, detail or exc.reason)) from exc
        except error.URLError as exc:
            raise RuntimeError("DeepSeek network error: {0}".format(exc.reason)) from exc

        parsed = json.loads(content)
        message = parsed.get("choices", [{}])[0].get("message", {}).get("content", "")
        if not message:
            raise RuntimeError("DeepSeek returned empty content")
        return message

    def _parse_message_content(self, message: str) -> dict:
        try:
            return json.loads(message)
        except json.JSONDecodeError:
            start = message.find("{")
            end = message.rfind("}")
            if start == -1 or end == -1 or end <= start:
                raise RuntimeError("DeepSeek did not return valid JSON")
            return json.loads(message[start : end + 1])

    def build_request_payload(
        self,
        patient: PatientUpsertRequest,
        quadruples: List[PatientQuadruple],
        predictions: List[PredictionItem],
        evidence: EvidenceSummary,
        path_explanation: List[str],
    ) -> dict:
        context = {
            "patient": patient.model_dump(),
            "quadruples": [item.model_dump() for item in quadruples],
            "predictions": [item.model_dump() for item in predictions],
            "evidence": evidence.model_dump(),
            "pathExplanation": path_explanation,
        }
        return {
            "model": self.model,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "你是慢病门诊医生助手。请基于患者信息输出 JSON，字段必须包含："
                        "risk_summary, care_plan, follow_up。每个字段是字符串数组，"
                        "每条建议要可执行、可落地、且避免绝对化医疗结论。"
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(context, ensure_ascii=False),
                },
            ],
        }

    def generate_advice(
        self,
        patient: PatientUpsertRequest,
        quadruples: List[PatientQuadruple],
        predictions: List[PredictionItem],
        evidence: EvidenceSummary,
        path_explanation: List[str],
    ) -> AdviceResponse:
        self._reload_runtime_config()
        payload = self.build_request_payload(
            patient=patient,
            quadruples=quadruples,
            predictions=predictions,
            evidence=evidence,
            path_explanation=path_explanation,
        )
        cache_key = self._cache_key(payload)
        cached = self._get_cached_response(cache_key)
        if cached is not None:
            return self._clone_response(cached, note="复用缓存建议，未重复调用 DeepSeek。")

        if self._should_call_remote():
            limited = self._rate_limit_response(patient.patientId)
            if limited is not None:
                return limited
            try:
                response = self._generate_with_deepseek(payload=payload)
                self._remember_remote_result(patient.patientId, cache_key, response)
                return response
            except Exception as exc:
                return self._placeholder_response(
                    patient=patient,
                    quadruples=quadruples,
                    predictions=predictions,
                    evidence=evidence,
                    path_explanation=path_explanation,
                    note="DeepSeek 调用失败，已回退本地建议：{0}".format(str(exc)),
                    configured=bool(self.api_key),
                )

        return self._placeholder_response(
            patient=patient,
            quadruples=quadruples,
            predictions=predictions,
            evidence=evidence,
            path_explanation=path_explanation,
            note="当前未启用外部模型调用。请设置 CTPATH_LLM_ENABLED=true 与 DEEPSEEK_API_KEY。",
            configured=bool(self.api_key),
        )

    def generate_medication_plan(
        self,
        patient: PatientUpsertRequest,
        current_medications: List[str],
        allergies: List[str],
        care_goals: List[str],
        clinical_notes: str,
    ) -> MedicationPlanResponse:
        self._reload_runtime_config()
        payload = self._build_medication_payload(
            patient=patient,
            current_medications=current_medications,
            allergies=allergies,
            care_goals=care_goals,
            clinical_notes=clinical_notes,
        )
        cache_key = self._cache_key(payload)
        cached = self._get_cached_medication_response(cache_key)
        if cached is not None:
            copied = cached.model_copy(deep=True)
            copied.adviceMeta.note = "复用缓存用药建议，未重复调用 DeepSeek。"
            return copied

        if self._should_call_remote():
            try:
                response = self._generate_medication_with_deepseek(
                    patient=patient,
                    payload=payload,
                    current_medications=current_medications,
                    allergies=allergies,
                    care_goals=care_goals,
                    clinical_notes=clinical_notes,
                )
                self._remember_medication_result(cache_key, response)
                return response
            except Exception as exc:
                response = self._placeholder_medication_plan(
                    patient=patient,
                    current_medications=current_medications,
                    allergies=allergies,
                    care_goals=care_goals,
                    clinical_notes=clinical_notes,
                    note="DeepSeek 调用失败，已回退本地用药建议：{0}".format(str(exc)),
                    configured=bool(self.api_key),
                )
                self._remember_medication_result(cache_key, response)
                return response

        response = self._placeholder_medication_plan(
            patient=patient,
            current_medications=current_medications,
            allergies=allergies,
            care_goals=care_goals,
            clinical_notes=clinical_notes,
            note="当前未启用外部模型调用。请设置 CTPATH_LLM_ENABLED=true 与 DEEPSEEK_API_KEY。",
            configured=bool(self.api_key),
        )
        self._remember_medication_result(cache_key, response)
        return response

    def _build_medication_payload(
        self,
        patient: PatientUpsertRequest,
        current_medications: List[str],
        allergies: List[str],
        care_goals: List[str],
        clinical_notes: str,
    ) -> dict:
        context = {
            "patient": patient.model_dump(),
            "current_medications": _dedupe_text(current_medications, limit=10),
            "allergies": _dedupe_text(allergies, limit=10),
            "care_goals": _dedupe_text(care_goals, limit=10),
            "clinical_notes": clinical_notes.strip(),
        }
        return {
            "model": self.model,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "你是慢病门诊用药管理助手。请输出 JSON，字段必须包含："
                        "medications, monitoring, education, disclaimer。"
                        "medications 是数组，每项包含 name,purpose,dosage,frequency,route,duration,cautions。"
                        "不要给出绝对化结论，不要替代医生处方。"
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(context, ensure_ascii=False),
                },
            ],
        }

    def _clone_response(self, response: AdviceResponse, note: str | None = None) -> AdviceResponse:
        meta = response.adviceMeta.model_copy()
        if note:
            meta.note = note
        return AdviceResponse(advice=list(response.advice), adviceMeta=meta)

    def _get_cached_response(self, cache_key: str) -> AdviceResponse | None:
        self._evict_expired_cache(self._cache)
        item = self._cache.get(cache_key)
        if item is None:
            return None
        _created_at, response = item
        return response

    def _remember_remote_result(self, patient_id: str, cache_key: str, response: AdviceResponse) -> None:
        now = time.time()
        self._cache[cache_key] = (now, response)
        self._patient_last_remote[patient_id] = now
        self._patient_last_cache_key[patient_id] = cache_key
        self._trim_cache(self._cache)

    def _rate_limit_response(self, patient_id: str) -> AdviceResponse | None:
        if self.min_interval <= 0:
            return None
        now = time.time()
        last_remote = self._patient_last_remote.get(patient_id)
        if last_remote is None or now - last_remote >= self.min_interval:
            return None
        remaining = max(1, int(self.min_interval - (now - last_remote)))
        last_cache_key = self._patient_last_cache_key.get(patient_id)
        if last_cache_key:
            cached = self._get_cached_response(last_cache_key)
            if cached is not None:
                return self._clone_response(
                    cached,
                    note="触发调用间隔限制，复用最近 DeepSeek 建议；约 {0} 秒后可再次调用。".format(remaining),
                )
        return AdviceResponse(
            advice=["当前触发调用间隔限制，请稍后再次获取远程建议。"],
            adviceMeta=AdviceMeta(
                provider=self.provider,
                model=self.model,
                source="placeholder",
                configured=bool(self.api_key),
                connected=False,
                note="调用过于频繁，约 {0} 秒后可再次调用 DeepSeek。".format(remaining),
            ),
        )

    def _generate_with_deepseek(self, payload: dict) -> AdviceResponse:
        message = self._call_deepseek(payload)
        advice_payload = self._parse_message_content(message)
        advice = self._merge_advice_payload(advice_payload)
        return AdviceResponse(
            advice=advice,
            adviceMeta=AdviceMeta(
                provider="deepseek",
                model=self.model,
                source="deepseek",
                configured=True,
                connected=True,
                note="建议由 DeepSeek 基于当前档案生成。",
            ),
        )

    def _merge_advice_payload(self, payload: dict) -> List[str]:
        advice: List[str] = []
        for key in ["risk_summary", "care_plan", "follow_up"]:
            value = payload.get(key, [])
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        advice.append(item)
            elif isinstance(value, str):
                advice.append(value)
        deduped = _dedupe_text(advice, limit=6)
        if not deduped:
            raise RuntimeError("DeepSeek 返回 JSON 中未包含有效建议字段")
        return deduped

    def _placeholder_response(
        self,
        patient: PatientUpsertRequest,
        quadruples: List[PatientQuadruple],
        predictions: List[PredictionItem],
        evidence: EvidenceSummary,
        path_explanation: List[str],
        note: str,
        configured: bool,
    ) -> AdviceResponse:
        advice = self._build_placeholder_advice(patient, quadruples, predictions, evidence, path_explanation)
        return AdviceResponse(
            advice=advice,
            adviceMeta=AdviceMeta(
                provider=self.provider,
                model=self.model,
                source="placeholder",
                configured=configured,
                connected=False,
                note=note,
            ),
        )

    def _build_placeholder_advice(
        self,
        patient: PatientUpsertRequest,
        quadruples: List[PatientQuadruple],
        predictions: List[PredictionItem],
        evidence: EvidenceSummary,
        path_explanation: List[str],
    ) -> List[str]:
        advice: List[str] = []
        top_prediction = predictions[0] if predictions else None
        if top_prediction:
            advice.append("当前模型最关注的后续状态为“{0}”，建议优先安排复核与随访。".format(top_prediction.label))

        if evidence.supportLevel == "minimal" or patient.dataSupport == "low":
            advice.append("当前结构化数据支持较弱，建议补充关键事件后再确认风险变化。")
        elif evidence.relationCount < 3:
            advice.append("知识关系覆盖偏少，建议补录近期门诊检查与依从性事件。")

        disease = patient.primaryDisease.lower()
        if "diabetes" in disease:
            advice.append("建议重点关注血糖控制、用药依从性与并发症筛查。")
        elif "alzheimer" in disease:
            advice.append("建议结合认知评估与家庭照护记录，评估近期照护压力变化。")
        elif "parkinson" in disease:
            advice.append("建议重点核查步态波动、跌倒风险与药效时窗变化。")
        else:
            advice.append("建议按门诊标准流程复核风险、治疗计划与随访节奏。")

        if quadruples:
            latest = quadruples[-1]
            advice.append("最近事件提示“{0}: {1}”，建议在下次接诊时重点复核。".format(latest.relationLabel, latest.objectValue))
        if path_explanation:
            advice.append("建议结合路径解释中的关键关系，核对预测依据与实际病程一致性。")
        return _dedupe_text(advice, limit=5)

    def _get_cached_medication_response(self, cache_key: str) -> MedicationPlanResponse | None:
        self._evict_expired_cache(self._medication_cache)
        item = self._medication_cache.get(cache_key)
        if item is None:
            return None
        _created_at, response = item
        return response

    def _remember_medication_result(self, cache_key: str, response: MedicationPlanResponse) -> None:
        self._medication_cache[cache_key] = (time.time(), response)
        self._trim_cache(self._medication_cache)

    def _generate_medication_with_deepseek(
        self,
        patient: PatientUpsertRequest,
        payload: dict,
        current_medications: List[str],
        allergies: List[str],
        care_goals: List[str],
        clinical_notes: str,
    ) -> MedicationPlanResponse:
        message = self._call_deepseek(payload)
        parsed = self._parse_message_content(message)

        medications_raw = parsed.get("medications", [])
        if not isinstance(medications_raw, list):
            medications_raw = []

        medications: List[MedicationPlanItem] = []
        for row in medications_raw:
            if not isinstance(row, dict):
                continue
            name = str(row.get("name") or row.get("drug") or "").strip()
            if not name:
                continue
            cautions = row.get("cautions", [])
            if not isinstance(cautions, list):
                cautions = [str(cautions)]
            medications.append(
                MedicationPlanItem(
                    name=name,
                    purpose=str(row.get("purpose") or "治疗目标待临床复核").strip(),
                    dosage=str(row.get("dosage") or "请按医嘱调整").strip(),
                    frequency=str(row.get("frequency") or "请按医嘱调整").strip(),
                    route=str(row.get("route") or "口服").strip(),
                    duration=str(row.get("duration") or "请结合病程动态调整").strip(),
                    cautions=_dedupe_text([str(item) for item in cautions], limit=6),
                )
            )

        if not medications:
            medications = self._build_placeholder_medication_items(
                patient=patient,
                current_medications=current_medications,
                allergies=allergies,
                care_goals=care_goals,
                clinical_notes=clinical_notes,
            )

        monitoring = parsed.get("monitoring", [])
        education = parsed.get("education", [])
        monitoring_items = _dedupe_text(monitoring if isinstance(monitoring, list) else [str(monitoring)], limit=6)
        education_items = _dedupe_text(education if isinstance(education, list) else [str(education)], limit=6)
        disclaimer = str(parsed.get("disclaimer") or "").strip() or "本建议由 AI 生成，仅供临床医生决策参考，不可替代处方。"

        return MedicationPlanResponse(
            patientId=patient.patientId,
            generatedAt=datetime.now(timezone.utc).isoformat(),
            medications=medications[:6],
            monitoring=monitoring_items,
            education=education_items,
            disclaimer=disclaimer,
            adviceMeta=AdviceMeta(
                provider="deepseek",
                model=self.model,
                source="deepseek",
                configured=True,
                connected=True,
                note="用药建议由 DeepSeek 生成，请结合门诊实际处方复核。",
            ),
        )

    def _placeholder_medication_plan(
        self,
        patient: PatientUpsertRequest,
        current_medications: List[str],
        allergies: List[str],
        care_goals: List[str],
        clinical_notes: str,
        note: str,
        configured: bool,
    ) -> MedicationPlanResponse:
        medications = self._build_placeholder_medication_items(
            patient=patient,
            current_medications=current_medications,
            allergies=allergies,
            care_goals=care_goals,
            clinical_notes=clinical_notes,
        )
        monitoring = [
            "启动/调整治疗后 1-2 周复核关键症状与生命体征。",
            "记录不良反应与依从性变化，必要时提前复诊。",
        ]
        if "diabetes" in patient.primaryDisease.lower():
            monitoring.append("建议复核空腹血糖与 HbA1c，并与家庭监测记录比对。")
        education = [
            "提醒患者与家属勿自行增减药，异常症状请及时就诊。",
            "尽量固定服药时点并记录漏服情况，便于门诊复核。",
        ]
        return MedicationPlanResponse(
            patientId=patient.patientId,
            generatedAt=datetime.now(timezone.utc).isoformat(),
            medications=medications,
            monitoring=_dedupe_text(monitoring, limit=6),
            education=_dedupe_text(education, limit=6),
            disclaimer="本建议为系统生成的临时参考，不替代医生面诊与处方。",
            adviceMeta=AdviceMeta(
                provider=self.provider,
                model=self.model,
                source="placeholder",
                configured=configured,
                connected=False,
                note=note,
            ),
        )

    def _build_placeholder_medication_items(
        self,
        patient: PatientUpsertRequest,
        current_medications: List[str],
        allergies: List[str],
        care_goals: List[str],
        clinical_notes: str,
    ) -> List[MedicationPlanItem]:
        cautions_base = []
        if allergies:
            cautions_base.append("已记录过敏史：{0}，开药前请再次核对。".format("、".join(_dedupe_text(allergies, limit=5))))
        if care_goals:
            cautions_base.append("本次目标：{0}。".format("；".join(_dedupe_text(care_goals, limit=3))))
        if clinical_notes.strip():
            cautions_base.append("备注：{0}".format(clinical_notes.strip()))

        meds: List[MedicationPlanItem] = []
        for item in _dedupe_text(current_medications, limit=4):
            meds.append(
                MedicationPlanItem(
                    name=item,
                    purpose="既往在用药物，建议核对疗效与依从性后决定是否续用。",
                    dosage="按既往处方",
                    frequency="按既往处方",
                    route="按既往处方",
                    duration="本次门诊复核后确定",
                    cautions=cautions_base or ["请核对药名、剂量与禁忌。"],
                )
            )

        if meds:
            return meds

        disease = patient.primaryDisease.lower()
        if "diabetes" in disease:
            meds = [
                MedicationPlanItem(
                    name="二甲双胍（示例）",
                    purpose="控制空腹与餐后血糖波动。",
                    dosage="起始小剂量，逐步调整",
                    frequency="每日 1-2 次（随餐）",
                    route="口服",
                    duration="建议 2-4 周后复核调整",
                    cautions=cautions_base or ["结合肾功能评估调整，注意胃肠道反应。"],
                )
            ]
        elif "parkinson" in disease:
            meds = [
                MedicationPlanItem(
                    name="左旋多巴/苄丝肼（示例）",
                    purpose="改善运动迟缓与肌强直表现。",
                    dosage="按症状分次小剂量调整",
                    frequency="每日分次",
                    route="口服",
                    duration="建议 1-2 周随访评估药效时窗",
                    cautions=cautions_base or ["警惕体位性低血压与异动症，必要时调整给药时点。"],
                )
            ]
        elif "alzheimer" in disease:
            meds = [
                MedicationPlanItem(
                    name="多奈哌齐（示例）",
                    purpose="用于认知症状管理。",
                    dosage="低剂量起始，耐受后调整",
                    frequency="每日 1 次",
                    route="口服",
                    duration="建议 2-4 周复核疗效与耐受",
                    cautions=cautions_base or ["关注心率与睡眠变化，联合家属观察记录。"],
                )
            ]
        else:
            meds = [
                MedicationPlanItem(
                    name="门诊用药复核（示例）",
                    purpose="基于当前病程先完成用药核对，再决定处方优化。",
                    dosage="以既往处方为准",
                    frequency="以既往处方为准",
                    route="以既往处方为准",
                    duration="建议 1-2 周内复诊调整",
                    cautions=cautions_base or ["避免患者自行改药，请由门诊医师统一评估。"],
                )
            ]
        return meds


LLM_ADVICE_SERVICE = LLMAdviceService()
