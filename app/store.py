from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from . import demo_store
from .model_service import MODEL_SERVICE
from .schemas import (
    DoctorPublic,
    ExperimentMetric,
    ModelMetricsResponse,
    PatientCase,
    PatientEventCreateRequest,
    PatientUpsertRequest,
    TimelineEvent,
)

try:
    from sqlalchemy import create_engine, text
except Exception:  # pragma: no cover
    create_engine = None
    text = None


DB_URL = os.getenv("CTPATH_DB_URL", "")
TOKENS: Dict[str, str] = {}
STORE = None


class MySQLStore:
    def __init__(self, db_url: str) -> None:
        if not create_engine or not text:
            raise RuntimeError("sqlalchemy is not installed")
        self.engine = create_engine(db_url, pool_pre_ping=True, future=True)

    def _fetch_all(self, query: str, **params: Any) -> List[Dict[str, Any]]:
        with self.engine.connect() as conn:
            rows = conn.execute(text(query), params).mappings().all()
        return [dict(row) for row in rows]

    def _fetch_one(self, query: str, **params: Any) -> Optional[Dict[str, Any]]:
        rows = self._fetch_all(query, **params)
        return rows[0] if rows else None

    def _execute(self, query: str, **params: Any) -> None:
        with self.engine.begin() as conn:
            conn.execute(text(query), params)

    def authenticate(self, username: str, password: str) -> Optional[DoctorPublic]:
        row = self._fetch_one(
            """
            SELECT username, password_hash, name, title, department
            FROM doctor_users
            WHERE username = :username
            """,
            username=username,
        )
        if not row or row["password_hash"] != password:
            return None
        return DoctorPublic(
            username=row["username"],
            name=row["name"],
            title=row["title"],
            department=row["department"],
        )

    def list_patients(self) -> List[dict]:
        return self._fetch_all(
            """
            SELECT patient_id AS patientId,
                   name,
                   age,
                   gender,
                   primary_disease AS primaryDisease,
                   current_stage AS currentStage,
                   risk_level AS riskLevel,
                   DATE_FORMAT(last_visit, '%Y-%m-%d') AS lastVisit,
                   summary,
                   data_support AS dataSupport
            FROM patients
            ORDER BY last_visit DESC, patient_id ASC
            """
        )

    def get_patient_row(self, patient_id: str) -> Optional[Dict[str, Any]]:
        return self._fetch_one(
            """
            SELECT patient_id AS patientId,
                   name,
                   age,
                   gender,
                   primary_disease AS primaryDisease,
                   current_stage AS currentStage,
                   risk_level AS riskLevel,
                   DATE_FORMAT(last_visit, '%Y-%m-%d') AS lastVisit,
                   summary,
                   data_support AS dataSupport
            FROM patients
            WHERE patient_id = :patient_id
            """,
            patient_id=patient_id,
        )

    def get_events(self, patient_id: str) -> List[dict]:
        return self._fetch_all(
            """
            SELECT id, event_time, relation, object_value, note, source
            FROM patient_events
            WHERE patient_id = :patient_id
            ORDER BY event_time ASC, id ASC
            """,
            patient_id=patient_id,
        )

    def save_patient(self, payload: PatientUpsertRequest) -> dict:
        self._execute(
            """
            INSERT INTO patients (
              patient_id, name, gender, age, primary_disease, current_stage,
              risk_level, last_visit, summary, data_support
            ) VALUES (
              :patient_id, :name, :gender, :age, :primary_disease, :current_stage,
              :risk_level, :last_visit, :summary, :data_support
            )
            ON DUPLICATE KEY UPDATE
              name = VALUES(name),
              gender = VALUES(gender),
              age = VALUES(age),
              primary_disease = VALUES(primary_disease),
              current_stage = VALUES(current_stage),
              risk_level = VALUES(risk_level),
              last_visit = VALUES(last_visit),
              summary = VALUES(summary),
              data_support = VALUES(data_support)
            """,
            patient_id=payload.patientId,
            name=payload.name,
            gender=payload.gender,
            age=payload.age,
            primary_disease=payload.primaryDisease,
            current_stage=payload.currentStage,
            risk_level=payload.riskLevel,
            last_visit=payload.lastVisit,
            summary=payload.summary,
            data_support=payload.dataSupport,
        )
        return self.get_patient_row(payload.patientId) or payload.model_dump()

    def add_event(self, patient_id: str, payload: PatientEventCreateRequest) -> None:
        self._execute(
            """
            INSERT INTO patient_events (
              patient_id, event_time, relation, object_value, note, source
            ) VALUES (
              :patient_id, :event_time, :relation, :object_value, :note, :source
            )
            """,
            patient_id=patient_id,
            event_time=payload.eventTime,
            relation=payload.relation,
            object_value=payload.objectValue,
            note=payload.note,
            source=payload.source,
        )


def _current_store() -> Optional[MySQLStore]:
    global STORE
    if STORE is not None:
        return STORE
    if not DB_URL:
        return None
    try:
        STORE = MySQLStore(DB_URL)
        return STORE
    except Exception:
        return None


def _issue_token(username: str) -> str:
    token = "ctpath-{0}-{1}".format(username, datetime.now(timezone.utc).timestamp())
    TOKENS[token] = username
    return token


def _relation_label(relation: str) -> str:
    mapping = {
        "stage": "阶段变化",
        "has_disease": "疾病诊断",
        "med_adherence": "服药依从性",
        "medical_history": "病史记录",
        "support_system": "家庭支持",
        "sleep_hours_bin": "睡眠状态",
        "mood_bin": "情绪状态",
        "bp_sys_bin": "血压分档",
        "bmi_bin": "BMI 分档",
        "cholesterol_bin": "血脂分档",
    }
    return mapping.get(relation, relation)


def _relation_type(relation: str) -> str:
    if relation in {"has_disease", "stage", "medical_history"}:
        return "diagnosis"
    if relation in {"med_adherence"}:
        return "medication"
    if relation in {"support_system", "sleep_hours_bin", "mood_bin", "bp_sys_bin", "bmi_bin", "cholesterol_bin"}:
        return "risk"
    return "visit"


def _build_timeline(events: List[Dict[str, Any]]) -> List[TimelineEvent]:
    timeline: List[TimelineEvent] = []
    for item in events:
        event_time = item["event_time"]
        event_date = event_time.strftime("%Y-%m-%d") if hasattr(event_time, "strftime") else str(event_time)[:10]
        detail = item.get("note") or "{0} -> {1}".format(_relation_label(item["relation"]), item["object_value"])
        timeline.append(
            TimelineEvent(
                date=event_date,
                type=_relation_type(item["relation"]),
                title="{0}: {1}".format(_relation_label(item["relation"]), item["object_value"]),
                detail=detail,
            )
        )
    return timeline


def _build_stats(events: List[Dict[str, Any]]) -> List[dict]:
    latest: Dict[str, Dict[str, Any]] = {}
    for item in events:
        latest[item["relation"]] = item

    stat_fields = [
        ("stage", "阶段"),
        ("med_adherence", "服药依从性"),
        ("support_system", "家庭支持"),
        ("bp_sys_bin", "血压分档"),
        ("bmi_bin", "BMI 分档"),
        ("cholesterol_bin", "血脂分档"),
    ]

    stats = []
    for relation, label in stat_fields:
        if relation in latest:
            stats.append(
                {
                    "label": label,
                    "value": str(latest[relation]["object_value"]),
                    "trend": "来自最近一次结构化事件",
                }
            )
    return stats[:4]


def _build_followups(patient: Dict[str, Any]) -> List[dict]:
    if patient["riskLevel"] == "高风险":
        return [
            {"title": "7 天内安排复诊", "owner": "专病门诊", "dueDate": str(patient["lastVisit"]), "priority": "high"},
            {"title": "补充连续监测记录", "owner": "慢病管理护士", "dueDate": str(patient["lastVisit"]), "priority": "high"},
            {"title": "同步生活方式干预", "owner": "健康管理师", "dueDate": str(patient["lastVisit"]), "priority": "medium"},
        ]
    return [
        {"title": "14 天内复查关键指标", "owner": "门诊医生", "dueDate": str(patient["lastVisit"]), "priority": "medium"},
        {"title": "补齐家庭监测记录", "owner": "患者本人", "dueDate": str(patient["lastVisit"]), "priority": "medium"},
        {"title": "准备下次宣教材料", "owner": "健康管理师", "dueDate": str(patient["lastVisit"]), "priority": "low"},
    ]


def _build_similar_cases(patient: Dict[str, Any]) -> List[dict]:
    return [
        {
            "caseId": "SIM-{0}".format(patient["patientId"]),
            "disease": patient["primaryDisease"],
            "matchScore": 0.84,
            "summary": "历史相似患者在强化随访后风险下降。",
            "suggestion": "优先补齐关键指标的连续时间事件。",
        }
    ]


def _patient_case_from_db(store: MySQLStore, patient_id: str) -> Optional[PatientCase]:
    patient = store.get_patient_row(patient_id)
    if not patient:
        return None
    events = store.get_events(patient_id)
    timeline = _build_timeline(events)
    recommendation_mode = "similar-case" if patient["dataSupport"] == "low" else "model"
    return PatientCase(
        **patient,
        stats=_build_stats(events),
        timeline=timeline,
        predictions=[],
        pathExplanation=["{0} -> {1}".format(item.date, item.title) for item in timeline[-3:]],
        followUps=_build_followups(patient),
        recommendationMode=recommendation_mode,
        careAdvice=[
            "优先完善最近一次就诊后的连续事件记录。",
            "确保患者时间线和结构化关系同步更新。",
            "对高风险患者缩短随访周期。",
        ],
        similarCases=_build_similar_cases(patient),
    )


def authenticate(username: str, password: str) -> Optional[DoctorPublic]:
    store = _current_store()
    if store:
        doctor = store.authenticate(username, password)
        if doctor:
            return doctor
    return demo_store.authenticate(username, password)


def issue_token(username: str) -> str:
    return _issue_token(username)


def is_token_valid(token: Optional[str]) -> bool:
    return bool(token and token in TOKENS)


def list_patients() -> List[dict]:
    store = _current_store()
    if store:
        return store.list_patients()
    return demo_store.list_patients()


def get_timeline(patient_id: str) -> Optional[List[TimelineEvent]]:
    store = _current_store()
    if store:
        patient = store.get_patient_row(patient_id)
        if not patient:
            return None
        return _build_timeline(store.get_events(patient_id))
    return demo_store.get_timeline(patient_id)


def get_patient(patient_id: str) -> Optional[PatientCase]:
    store = _current_store()
    if store:
        return _patient_case_from_db(store, patient_id)
    return demo_store.get_patient(patient_id)


def save_patient(payload: PatientUpsertRequest) -> Optional[PatientCase]:
    store = _current_store()
    if store:
        store.save_patient(payload)
        return _patient_case_from_db(store, payload.patientId)
    return demo_store.save_patient(payload)


def add_patient_event(patient_id: str, payload: PatientEventCreateRequest) -> Optional[PatientCase]:
    store = _current_store()
    if store:
        if not store.get_patient_row(patient_id):
            return None
        store.add_event(patient_id, payload)
        return _patient_case_from_db(store, patient_id)
    return demo_store.add_event(patient_id, payload)


def predict_for_patient(patient_id: str, topk: int) -> Optional[dict]:
    patient = get_patient(patient_id)
    if patient is None:
        return None

    model_predictions = []
    if patient.recommendationMode == "model":
        model_predictions = MODEL_SERVICE.predict_patient(
            patient_id=patient.patientId,
            primary_disease=patient.primaryDisease,
            timestamp=patient.lastVisit,
            topk=topk,
        )

    if model_predictions:
        return {
            "patientId": patient.patientId,
            "mode": "model",
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "topk": model_predictions,
            "advice": patient.careAdvice,
            "pathExplanation": patient.pathExplanation,
            "similarCases": patient.similarCases,
        }

    fallback = demo_store.predict_for_patient(patient_id, topk)
    if fallback:
        return fallback

    return {
        "patientId": patient.patientId,
        "mode": "similar-case",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "topk": [
            {
                "label": "建议继续观察 {0}".format(patient.primaryDisease),
                "score": 0.52,
                "reason": "当前样本不足，先返回规则和案例辅助建议。",
            }
        ],
        "advice": patient.careAdvice,
        "pathExplanation": patient.pathExplanation,
        "similarCases": patient.similarCases,
    }


def get_model_metrics() -> ModelMetricsResponse:
    return ModelMetricsResponse(
        dataset="CHRONIC",
        currentModel=ExperimentMetric(
            model="TKGR-GPRSCL / CTpath",
            status="done",
            mrr=0.3441,
            hits1=0.2294,
            hits3=0.4489,
            hits10=0.5163,
            note="已在 CHRONIC 数据集上跑通训练与测试，可用于复试演示与论文主结果。",
        ),
        comparisons=[
            ExperimentMetric(
                model="静态知识图谱基线",
                status="todo",
                note="任务书要求需要补充对比实验，用于证明时序推理优于静态知识图谱。",
            ),
            ExperimentMetric(
                model="去路径表示模块",
                status="todo",
                note="建议作为消融实验，验证最大熵路径采样与路径表示的增益。",
            ),
            ExperimentMetric(
                model="去监督对比学习模块",
                status="todo",
                note="建议作为消融实验，验证监督对比学习对预测精度的提升。",
            ),
        ],
    )
