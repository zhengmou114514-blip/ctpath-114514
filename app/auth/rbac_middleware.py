"""
RBAC权限验证中间件

基于角色的访问控制中间件，验证所有API请求的权限
"""

import json
import logging
from typing import Optional, Callable
from datetime import datetime

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .role_definitions import Role, get_role_by_name, validate_role
from .permission_registry import PERMISSION_REGISTRY


logger = logging.getLogger(__name__)


class RBACMiddleware(BaseHTTPMiddleware):
    """
    RBAC权限验证中间件

    拦截所有请求，验证用户角色是否有权限访问API
    """

    def __init__(self, app, excluded_paths: Optional[set] = None):
        """
        初始化中间件

        Args:
            app: FastAPI应用
            excluded_paths: 排除的路径集合（不需要权限验证）
        """
        super().__init__(app)
        self.excluded_paths = excluded_paths or {
            "/api/login",
            "/api/register",
            "/health",
            "/metrics",
            "/docs",
            "/openapi.json",
            "/redoc"
        }

    async def dispatch(self, request: Request, call_next: Callable):
        """
        处理请求

        Args:
            request: 请求对象
            call_next: 下一个中间件

        Returns:
            Response: 响应对象
        """
        # 获取请求路径和方法
        path = request.url.path
        method = request.method

        # 检查是否为排除路径
        if self._is_excluded_path(path):
            return await call_next(request)

        # 获取用户角色
        role = self._get_user_role(request)

        if role is None:
            # 未认证
            return self._unauthorized_response("未提供认证信息")

        # 验证权限
        if not PERMISSION_REGISTRY.is_allowed(path, method, role):
            # 记录审计日志
            self._log_access_denied(request, role, path, method)

            # 返回403
            return self._forbidden_response(role, path, method)

        # 记录审计日志
        self._log_access_granted(request, role, path, method)

        # 继续处理请求
        return await call_next(request)

    def _is_excluded_path(self, path: str) -> bool:
        """
        检查路径是否被排除

        Args:
            path: 请求路径

        Returns:
            bool: 是否排除
        """
        # 精确匹配
        if path in self.excluded_paths:
            return True

        # 前缀匹配（用于静态文件等）
        for excluded in self.excluded_paths:
            if path.startswith(excluded):
                return True

        return False

    def _get_user_role(self, request: Request) -> Optional[Role]:
        """
        从请求中获取用户角色

        Args:
            request: 请求对象

        Returns:
            Optional[Role]: 用户角色，如果未认证则返回None
        """
        # 从请求状态中获取（由认证中间件设置）
        if hasattr(request.state, "user_role"):
            role_str = request.state.user_role
            if validate_role(role_str):
                return get_role_by_name(role_str)

        # 从请求头中获取（备选方案）
        role_header = request.headers.get("X-User-Role")
        if role_header and validate_role(role_header):
            return get_role_by_name(role_header)

        return None

    def _unauthorized_response(self, message: str) -> JSONResponse:
        """
        返回401未认证响应

        Args:
            message: 错误消息

        Returns:
            JSONResponse: 401响应
        """
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "detail": message,
                "error_code": "UNAUTHORIZED"
            },
            headers={"WWW-Authenticate": "Bearer"}
        )

    def _forbidden_response(
        self,
        role: Role,
        path: str,
        method: str
    ) -> JSONResponse:
        """
        返回403禁止访问响应

        Args:
            role: 用户角色
            path: 请求路径
            method: 请求方法

        Returns:
            JSONResponse: 403响应
        """
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "detail": f"角色'{role.value}'无权限访问{method} {path}",
                "error_code": "FORBIDDEN",
                "role": role.value,
                "path": path,
                "method": method
            }
        )

    def _log_access_granted(
        self,
        request: Request,
        role: Role,
        path: str,
        method: str
    ):
        """
        记录访问允许日志

        Args:
            request: 请求对象
            role: 用户角色
            path: 请求路径
            method: 请求方法
        """
        logger.info(
            f"Access granted: role={role.value}, method={method}, path={path}, "
            f"client={request.client.host if request.client else 'unknown'}"
        )

    def _log_access_denied(
        self,
        request: Request,
        role: Role,
        path: str,
        method: str
    ):
        """
        记录访问拒绝日志

        Args:
            request: 请求对象
            role: 用户角色
            path: 请求路径
            method: 请求方法
        """
        logger.warning(
            f"Access denied: role={role.value}, method={method}, path={path}, "
            f"client={request.client.host if request.client else 'unknown'}"
        )


def require_role(*allowed_roles: Role):
    """
    角色验证装饰器

    Args:
        allowed_roles: 允许的角色列表

    Returns:
        装饰器函数
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 从kwargs中获取request
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if request is None:
                request = kwargs.get("request")

            if request is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="无法获取请求对象"
                )

            # 获取用户角色
            role_str = getattr(request.state, "user_role", None)
            if not role_str:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未提供认证信息"
                )

            try:
                role = get_role_by_name(role_str)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="无效的角色"
                )

            # 检查角色是否允许
            if role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"角色'{role.value}'无权限执行此操作"
                )

            return await func(*args, **kwargs)

        return wrapper
    return decorator


def require_permission(*required_permissions):
    """
    权限验证装饰器

    Args:
        required_permissions: 所需权限列表

    Returns:
        装饰器函数
    """
    from .role_definitions import has_permission

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 从kwargs中获取request
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if request is None:
                request = kwargs.get("request")

            if request is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="无法获取请求对象"
                )

            # 获取用户角色
            role_str = getattr(request.state, "user_role", None)
            if not role_str:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未提供认证信息"
                )

            try:
                role = get_role_by_name(role_str)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="无效的角色"
                )

            # 检查是否拥有所有所需权限
            for permission in required_permissions:
                if not has_permission(role, permission):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"缺少权限: {permission.value}"
                    )

            return await func(*args, **kwargs)

        return wrapper
    return decorator
