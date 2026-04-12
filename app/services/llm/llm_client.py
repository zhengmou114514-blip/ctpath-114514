"""
增强版LLM客户端

整合健康检查、重试、降级、验证等功能，提供稳定的LLM服务
"""

import json
import time
import hashlib
from typing import List, Optional, Dict
from urllib import parse, request

from ...env_loader import load_env_file
from ...schemas import (
    AdviceMeta,
    AdviceResponse,
    EvidenceSummary,
    PatientQuadruple,
    PatientUpsertRequest,
    PredictionItem,
)

from .health_checker import LLMHealthChecker, LLMHealthStatus
from .retry_handler import LLMRetryHandler, RetryConfig, is_retryable_error
from .fallback_engine import FallbackEngine
from .response_validator import LLMResponseValidator


class EnhancedLLMClient:
    """
    增强版LLM客户端

    整合健康检查、重试、降级、验证等功能
    """

    def __init__(self):
        """初始化客户端"""
        # 加载配置
        self._load_config()

        # 初始化组件
        self.health_checker = LLMHealthChecker(cache_ttl=5, timeout=5.0)
        self.retry_handler = LLMRetryHandler(RetryConfig(
            max_retries=3,
            base_delay=1.0,
            max_delay=30.0
        ))
        self.fallback_engine = FallbackEngine()
        self.response_validator = LLMResponseValidator()

        # 缓存
        self._cache: Dict[str, tuple] = {}
        self._cache_ttl = 300

        # 统计
        self._stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'fallback_requests': 0,
            'cache_hits': 0
        }

    def _load_config(self):
        """加载配置"""
        load_env_file(override=True)

        self.enabled = self._env_flag("CTPATH_LLM_ENABLED", False)
        self.provider = os.getenv("CTPATH_LLM_PROVIDER", "deepseek")
        self.model = os.getenv("CTPATH_LLM_MODEL", "deepseek-chat")
        self.base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self.api_key = os.getenv("DEEPSEEK_API_KEY", "")
        self.timeout = self._env_float("CTPATH_LLM_TIMEOUT", 40.0)

    def _env_flag(self, name: str, default: bool = False) -> bool:
        value = os.getenv(name)
        if value is None:
            return default
        return value.strip().lower() in {"1", "true", "yes", "on"}

    def _env_float(self, name: str, default: float) -> float:
        value = os.getenv(name)
        if value is None:
            return default
        try:
            return float(value)
        except ValueError:
            return default

    def generate_advice(
        self,
        patient: PatientUpsertRequest,
        quadruples: List[PatientQuadruple],
        predictions: List[PredictionItem],
        evidence: EvidenceSummary,
        path_explanation: List[str]
    ) -> AdviceResponse:
        """
        生成建议

        Args:
            patient: 患者信息
            quadruples: 四元组列表
            predictions: 预测结果
            evidence: 证据摘要
            path_explanation: 路径解释

        Returns:
            AdviceResponse: 建议响应
        """
        self._stats['total_requests'] += 1

        # 1. 检查缓存
        cache_key = self._build_cache_key(
            patient, quadruples, predictions, evidence
        )
        cached = self._get_cached(cache_key)
        if cached:
            self._stats['cache_hits'] += 1
            return cached

        # 2. 检查是否启用LLM
        if not self.enabled or not self.api_key:
            return self._fallback_response(
                patient, quadruples, predictions, evidence, path_explanation,
                "LLM服务未启用或API密钥未配置"
            )

        # 3. 健康检查
        health = self.health_checker.check_health(
            self.base_url, self.api_key, self.model
        )

        if not health.is_healthy:
            return self._fallback_response(
                patient, quadruples, predictions, evidence, path_explanation,
                f"LLM服务不健康: {health.error_message}"
            )

        # 4. 调用LLM（带重试）
        try:
            response = self._call_llm_with_retry(
                patient, quadruples, predictions, evidence, path_explanation
            )

            # 缓存结果
            self._set_cached(cache_key, response)

            self._stats['successful_requests'] += 1
            return response

        except Exception as exc:
            self._stats['failed_requests'] += 1

            return self._fallback_response(
                patient, quadruples, predictions, evidence, path_explanation,
                f"LLM调用失败: {str(exc)}"
            )

    def _call_llm_with_retry(
        self,
        patient: PatientUpsertRequest,
        quadruples: List[PatientQuadruple],
        predictions: List[PredictionItem],
        evidence: EvidenceSummary,
        path_explanation: List[str]
    ) -> AdviceResponse:
        """调用LLM（带重试）"""
        payload = self._build_request_payload(
            patient, quadruples, predictions, evidence, path_explanation
        )

        def call_llm():
            return self._call_deepseek_api(payload)

        result = self.retry_handler.execute_with_retry(
            call_llm,
            should_retry=is_retryable_error
        )

        if not result.success:
            raise result.error

        # 验证响应
        validation = self.response_validator.validate(result.result)

        if not validation.is_valid:
            raise ValueError(f"响应验证失败: {', '.join(validation.errors)}")

        # 清理响应
        sanitized = self.response_validator.sanitize_response(validation.data)

        # 构建建议列表
        advice = self._extract_advice(sanitized)

        meta = AdviceMeta(
            provider=self.provider,
            model=self.model,
            source="deepseek",
            configured=True,
            connected=True,
            note="建议由DeepSeek生成"
        )

        return AdviceResponse(advice=advice, adviceMeta=meta)

    def _call_deepseek_api(self, payload: Dict) -> str:
        """调用DeepSeek API"""
        endpoint = parse.urljoin(
            self.base_url.rstrip("/") + "/",
            "/chat/completions"
        )

        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        req = request.Request(
            endpoint,
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            method="POST"
        )

        with request.urlopen(req, timeout=self.timeout) as response:
            content = response.read().decode("utf-8")

        parsed = json.loads(content)
        message = parsed.get("choices", [{}])[0].get("message", {}).get("content", "")

        if not message:
            raise ValueError("DeepSeek返回内容为空")

        return message

    def _build_request_payload(
        self,
        patient: PatientUpsertRequest,
        quadruples: List[PatientQuadruple],
        predictions: List[PredictionItem],
        evidence: EvidenceSummary,
        path_explanation: List[str]
    ) -> Dict:
        """构建请求payload"""
        context = {
            "patient": patient.model_dump(),
            "quadruples": [item.model_dump() for item in quadruples],
            "predictions": [item.model_dump() for item in predictions],
            "evidence": evidence.model_dump(),
            "pathExplanation": path_explanation
        }

        return {
            "model": self.model,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "你是慢性病辅助诊疗建议生成助手。"
                        "基于患者档案、时序四元组、模型预测结果和证据摘要，"
                        "输出医生可读的风险提示、处置建议和随访建议。"
                        "输出必须是JSON对象，包含risk_summary、care_plan、follow_up三个字段。"
                    )
                },
                {
                    "role": "user",
                    "content": json.dumps(context, ensure_ascii=False)
                }
            ]
        }

    def _fallback_response(
        self,
        patient: PatientUpsertRequest,
        quadruples: List[PatientQuadruple],
        predictions: List[PredictionItem],
        evidence: EvidenceSummary,
        path_explanation: List[str],
        reason: str
    ) -> AdviceResponse:
        """生成降级响应"""
        self._stats['fallback_requests'] += 1

        advice = self.fallback_engine.generate_fallback_advice(
            patient, quadruples, predictions, evidence, path_explanation, reason
        )

        meta = AdviceMeta(
            provider=self.provider,
            model=self.model,
            source="fallback",
            configured=bool(self.api_key),
            connected=False,
            note=f"使用规则引擎生成建议: {reason}"
        )

        return AdviceResponse(advice=advice, adviceMeta=meta)

    def _extract_advice(self, data: Dict) -> List[str]:
        """提取建议列表"""
        advice = []

        for key in ['risk_summary', 'care_plan', 'follow_up']:
            value = data.get(key, [])

            if isinstance(value, list):
                for item in value:
                    if isinstance(item, str) and item.strip():
                        advice.append(item.strip())
            elif isinstance(value, str) and value.strip():
                advice.append(value.strip())

        # 去重
        deduped = []
        for item in advice:
            if item not in deduped:
                deduped.append(item)

        return deduped[:6]

    def _build_cache_key(
        self,
        patient: PatientUpsertRequest,
        quadruples: List[PatientQuadruple],
        predictions: List[PredictionItem],
        evidence: EvidenceSummary
    ) -> str:
        """构建缓存键"""
        data = {
            'patient_id': patient.patientId,
            'quadruples': len(quadruples),
            'predictions': [p.label for p in predictions],
            'support': evidence.supportLevel
        }

        body = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(body.encode("utf-8")).hexdigest()

    def _get_cached(self, key: str) -> Optional[AdviceResponse]:
        """获取缓存"""
        if key not in self._cache:
            return None

        created_at, response = self._cache[key]

        if time.time() - created_at > self._cache_ttl:
            del self._cache[key]
            return None

        return response

    def _set_cached(self, key: str, response: AdviceResponse):
        """设置缓存"""
        self._cache[key] = (time.time(), response)

        # 清理过期缓存
        now = time.time()
        expired = [
            k for k, (t, _) in self._cache.items()
            if now - t > self._cache_ttl
        ]
        for k in expired:
            del self._cache[k]

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self._stats.copy()

    def get_health_status(self) -> Optional[LLMHealthStatus]:
        """获取健康状态"""
        return self.health_checker.get_cached_status()


# 导入os模块
import os
