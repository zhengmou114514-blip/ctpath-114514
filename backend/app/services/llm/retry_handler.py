"""
LLM重试处理器

实现指数退避重试策略，处理临时性错误
"""

import time
import random
from typing import Callable, TypeVar, Optional
from functools import wraps

T = TypeVar('T')


class RetryConfig:
    """重试配置"""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        """
        初始化重试配置

        Args:
            max_retries: 最大重试次数
            base_delay: 基础延迟时间（秒）
            max_delay: 最大延迟时间（秒）
            exponential_base: 指数基数
            jitter: 是否添加随机抖动
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter


class RetryResult:
    """重试结果"""

    def __init__(
        self,
        success: bool,
        result: Optional[T] = None,
        error: Optional[Exception] = None,
        attempts: int = 0,
        total_delay: float = 0.0
    ):
        self.success = success
        self.result = result
        self.error = error
        self.attempts = attempts
        self.total_delay = total_delay


class LLMRetryHandler:
    """
    LLM重试处理器

    实现指数退避重试策略
    """

    def __init__(self, config: Optional[RetryConfig] = None):
        """
        初始化重试处理器

        Args:
            config: 重试配置
        """
        self.config = config or RetryConfig()

    def execute_with_retry(
        self,
        func: Callable[[], T],
        should_retry: Optional[Callable[[Exception], bool]] = None
    ) -> RetryResult[T]:
        """
        执行函数并在失败时重试

        Args:
            func: 要执行的函数
            should_retry: 判断是否应该重试的函数

        Returns:
            RetryResult: 重试结果
        """
        attempts = 0
        total_delay = 0.0
        last_error: Optional[Exception] = None

        while attempts <= self.config.max_retries:
            try:
                result = func()
                return RetryResult(
                    success=True,
                    result=result,
                    attempts=attempts + 1,
                    total_delay=total_delay
                )

            except Exception as exc:
                last_error = exc
                attempts += 1

                # 判断是否应该重试
                if should_retry and not should_retry(exc):
                    return RetryResult(
                        success=False,
                        error=exc,
                        attempts=attempts,
                        total_delay=total_delay
                    )

                # 检查是否还有重试机会
                if attempts > self.config.max_retries:
                    break

                # 计算延迟时间
                delay = self._calculate_delay(attempts)
                total_delay += delay

                # 等待
                time.sleep(delay)

        return RetryResult(
            success=False,
            error=last_error,
            attempts=attempts,
            total_delay=total_delay
        )

    def _calculate_delay(self, attempt: int) -> float:
        """
        计算延迟时间

        Args:
            attempt: 当前尝试次数

        Returns:
            float: 延迟时间（秒）
        """
        # 指数退避
        delay = self.config.base_delay * (self.config.exponential_base ** (attempt - 1))

        # 限制最大延迟
        delay = min(delay, self.config.max_delay)

        # 添加随机抖动
        if self.config.jitter:
            delay = delay * (0.5 + random.random())

        return delay


def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    should_retry: Optional[Callable[[Exception], bool]] = None
):
    """
    重试装饰器

    Args:
        max_retries: 最大重试次数
        base_delay: 基础延迟时间
        should_retry: 判断是否应该重试的函数

    Returns:
        装饰器函数
    """
    config = RetryConfig(max_retries=max_retries, base_delay=base_delay)
    handler = LLMRetryHandler(config)

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            result = handler.execute_with_retry(
                lambda: func(*args, **kwargs),
                should_retry
            )

            if result.success:
                return result.result
            else:
                raise result.error

        return wrapper

    return decorator


def is_retryable_error(error: Exception) -> bool:
    """
    判断错误是否可重试

    Args:
        error: 异常对象

    Returns:
        bool: 是否可重试
    """
    # 网络错误可重试
    error_str = str(error).lower()

    # 临时性错误
    if any(keyword in error_str for keyword in [
        'timeout',
        'connection',
        'network',
        'temporarily',
        'rate limit',
        '429',
        '503',
        '502'
    ]):
        return True

    # 认证错误不重试
    if any(keyword in error_str for keyword in [
        '401',
        'unauthorized',
        'invalid api key',
        'authentication'
    ]):
        return False

    # 默认不重试
    return False
