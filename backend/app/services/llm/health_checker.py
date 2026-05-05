"""
LLM健康检查器

定期检查LLM服务的可用性，包括API连接、认证状态和配额情况
"""

import json
import time
from typing import Dict, Optional
from urllib import error, parse, request

from ...env_loader import load_env_file


class LLMHealthStatus:
    """LLM健康状态"""

    def __init__(
        self,
        is_healthy: bool,
        is_responsive: bool = False,
        is_authenticated: bool = False,
        has_quota: bool = False,
        error_message: Optional[str] = None,
        latency_ms: Optional[float] = None,
        checked_at: Optional[float] = None
    ):
        self.is_healthy = is_healthy
        self.is_responsive = is_responsive
        self.is_authenticated = is_authenticated
        self.has_quota = has_quota
        self.error_message = error_message
        self.latency_ms = latency_ms
        self.checked_at = checked_at or time.time()

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'is_healthy': self.is_healthy,
            'is_responsive': self.is_responsive,
            'is_authenticated': self.is_authenticated,
            'has_quota': self.has_quota,
            'error_message': self.error_message,
            'latency_ms': self.latency_ms,
            'checked_at': self.checked_at
        }


class LLMHealthChecker:
    """
    LLM健康检查器

    定期检查LLM服务的可用性，缓存检查结果
    """

    def __init__(
        self,
        cache_ttl: int = 5,
        timeout: float = 5.0
    ):
        """
        初始化健康检查器

        Args:
            cache_ttl: 健康状态缓存时间（秒）
            timeout: 健康检查超时时间（秒）
        """
        self.cache_ttl = cache_ttl
        self.timeout = timeout
        self._cached_status: Optional[LLMHealthStatus] = None
        self._last_check_time: float = 0

    def check_health(
        self,
        base_url: str,
        api_key: str,
        model: str,
        force: bool = False
    ) -> LLMHealthStatus:
        """
        检查LLM服务健康状态

        Args:
            base_url: API基础URL
            api_key: API密钥
            model: 模型名称
            force: 是否强制刷新缓存

        Returns:
            LLMHealthStatus: 健康状态
        """
        # 检查缓存
        if not force and self._is_cache_valid():
            return self._cached_status

        # 执行健康检查
        status = self._perform_health_check(base_url, api_key, model)

        # 更新缓存
        self._cached_status = status
        self._last_check_time = time.time()

        return status

    def _is_cache_valid(self) -> bool:
        """检查缓存是否有效"""
        if self._cached_status is None:
            return False

        elapsed = time.time() - self._last_check_time
        return elapsed < self.cache_ttl

    def _perform_health_check(
        self,
        base_url: str,
        api_key: str,
        model: str
    ) -> LLMHealthStatus:
        """
        执行健康检查

        Args:
            base_url: API基础URL
            api_key: API密钥
            model: 模型名称

        Returns:
            LLMHealthStatus: 健康状态
        """
        if not api_key:
            return LLMHealthStatus(
                is_healthy=False,
                is_responsive=False,
                is_authenticated=False,
                has_quota=False,
                error_message="API密钥未配置"
            )

        # 发送测试请求
        start_time = time.time()

        try:
            # 构建测试请求（简单的模型列表请求）
            endpoint = parse.urljoin(base_url.rstrip("/") + "/", "/models")
            req = request.Request(
                endpoint,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                method="GET"
            )

            with request.urlopen(req, timeout=self.timeout) as response:
                content = response.read().decode("utf-8")
                latency_ms = (time.time() - start_time) * 1000

                # 解析响应
                data = json.loads(content)

                # 检查模型是否可用
                available_models = [m.get("id") for m in data.get("data", [])]
                model_available = model in available_models

                return LLMHealthStatus(
                    is_healthy=True,
                    is_responsive=True,
                    is_authenticated=True,
                    has_quota=True,
                    latency_ms=latency_ms
                )

        except error.HTTPError as exc:
            latency_ms = (time.time() - start_time) * 1000

            if exc.code == 401:
                return LLMHealthStatus(
                    is_healthy=False,
                    is_responsive=True,
                    is_authenticated=False,
                    has_quota=False,
                    error_message="API密钥无效或已过期",
                    latency_ms=latency_ms
                )
            elif exc.code == 429:
                return LLMHealthStatus(
                    is_healthy=False,
                    is_responsive=True,
                    is_authenticated=True,
                    has_quota=False,
                    error_message="API调用频率超限或配额不足",
                    latency_ms=latency_ms
                )
            else:
                return LLMHealthStatus(
                    is_healthy=False,
                    is_responsive=True,
                    is_authenticated=True,
                    has_quota=True,
                    error_message=f"HTTP错误: {exc.code}",
                    latency_ms=latency_ms
                )

        except error.URLError as exc:
            return LLMHealthStatus(
                is_healthy=False,
                is_responsive=False,
                is_authenticated=False,
                has_quota=False,
                error_message=f"网络连接失败: {exc.reason}"
            )

        except Exception as exc:
            return LLMHealthStatus(
                is_healthy=False,
                is_responsive=False,
                is_authenticated=False,
                has_quota=False,
                error_message=f"健康检查异常: {str(exc)}"
            )

    def get_cached_status(self) -> Optional[LLMHealthStatus]:
        """获取缓存的健康状态"""
        if self._is_cache_valid():
            return self._cached_status
        return None

    def clear_cache(self):
        """清除缓存"""
        self._cached_status = None
        self._last_check_time = 0
