"""
权限注册表

注册所有API端点的权限要求
"""

from typing import Dict, List, Set, Optional, Tuple
from .role_definitions import Role, Permission, ROLE_PERMISSIONS


class APIPermission:
    """API权限配置"""

    def __init__(
        self,
        path: str,
        method: str,
        required_permissions: Set[Permission],
        allowed_roles: Optional[Set[Role]] = None,
        description: str = ""
    ):
        """
        初始化API权限配置

        Args:
            path: API路径
            method: HTTP方法
            required_permissions: 所需权限集合
            allowed_roles: 允许的角色集合（可选，如果不指定则根据权限推断）
            description: API描述
        """
        self.path = path
        self.method = method.upper()
        self.required_permissions = required_permissions
        self.description = description

        # 如果未指定允许角色，则根据权限推断
        if allowed_roles is None:
            self.allowed_roles = self._infer_allowed_roles(required_permissions)
        else:
            self.allowed_roles = allowed_roles

    def _infer_allowed_roles(self, permissions: Set[Permission]) -> Set[Role]:
        """根据权限推断允许的角色"""
        allowed = set()

        for role, role_perms in ROLE_PERMISSIONS.items():
            # 如果角色拥有所有所需权限，则允许
            if permissions.issubset(role_perms):
                allowed.add(role)

        return allowed

    def is_role_allowed(self, role: Role) -> bool:
        """
        检查角色是否被允许

        Args:
            role: 角色枚举

        Returns:
            bool: 是否允许
        """
        return role in self.allowed_roles


class PermissionRegistry:
    """
    权限注册表

    管理所有API的权限配置
    """

    def __init__(self):
        """初始化注册表"""
        self._registry: Dict[Tuple[str, str], APIPermission] = {}
        self._initialize_default_permissions()

    def _initialize_default_permissions(self):
        """初始化默认权限配置"""
        # 认证API（无需权限）
        self.register(APIPermission(
            path="/api/login",
            method="POST",
            required_permissions=set(),
            allowed_roles={Role.ADMIN, Role.DOCTOR, Role.NURSE, Role.ARCHIVIST},
            description="用户登录"
        ))

        self.register(APIPermission(
            path="/api/register",
            method="POST",
            required_permissions=set(),
            allowed_roles={Role.ADMIN},
            description="用户注册"
        ))

        # 患者管理API
        self.register(APIPermission(
            path="/api/patients",
            method="GET",
            required_permissions={Permission.PATIENT_VIEW},
            description="获取患者列表"
        ))

        self.register(APIPermission(
            path="/api/patient",
            method="POST",
            required_permissions={Permission.PATIENT_CREATE},
            description="创建患者"
        ))

        self.register(APIPermission(
            path="/api/patient/{id}",
            method="GET",
            required_permissions={Permission.PATIENT_VIEW},
            description="获取患者详情"
        ))

        self.register(APIPermission(
            path="/api/patient/{id}",
            method="PUT",
            required_permissions={Permission.PATIENT_UPDATE},
            description="更新患者"
        ))

        self.register(APIPermission(
            path="/api/patient/{id}",
            method="DELETE",
            required_permissions={Permission.PATIENT_DELETE},
            description="删除患者"
        ))

        # 事件管理API
        self.register(APIPermission(
            path="/api/patient/{id}/event",
            method="POST",
            required_permissions={Permission.EVENT_CREATE},
            description="添加患者事件"
        ))

        self.register(APIPermission(
            path="/api/timeline/{id}",
            method="GET",
            required_permissions={Permission.EVENT_VIEW},
            description="获取患者时间线"
        ))

        # 预测API
        self.register(APIPermission(
            path="/api/predict",
            method="POST",
            required_permissions={Permission.PREDICTION_RUN},
            description="运行预测"
        ))

        # 建议API
        self.register(APIPermission(
            path="/api/advice/generate",
            method="POST",
            required_permissions={Permission.ADVICE_GENERATE},
            description="生成建议"
        ))

        # 随访API
        self.register(APIPermission(
            path="/api/worklists/followups",
            method="GET",
            required_permissions={Permission.FOLLOWUP_VIEW},
            description="获取随访任务列表"
        ))

        self.register(APIPermission(
            path="/api/worklists/flow-board",
            method="GET",
            required_permissions={Permission.TASK_VIEW},
            description="获取流程看板"
        ))

    def register(self, api_permission: APIPermission):
        """
        注册API权限

        Args:
            api_permission: API权限配置
        """
        key = (api_permission.path, api_permission.method)
        self._registry[key] = api_permission

    def get_permission(self, path: str, method: str) -> Optional[APIPermission]:
        """
        获取API权限配置

        Args:
            path: API路径
            method: HTTP方法

        Returns:
            Optional[APIPermission]: 权限配置，如果未注册则返回None
        """
        # 标准化路径（移除路径参数的具体值）
        normalized_path = self._normalize_path(path)

        key = (normalized_path, method.upper())
        return self._registry.get(key)

    def _normalize_path(self, path: str) -> str:
        """
        标准化路径

        将路径参数的具体值替换为占位符

        Args:
            path: 原始路径

        Returns:
            str: 标准化后的路径
        """
        # 简单实现：查找已注册的路径进行匹配
        for (registered_path, _) in self._registry.keys():
            if self._path_matches(path, registered_path):
                return registered_path

        return path

    def _path_matches(self, actual_path: str, pattern_path: str) -> bool:
        """
        检查路径是否匹配模式

        Args:
            actual_path: 实际路径
            pattern_path: 模式路径（可能包含{param}占位符）

        Returns:
            bool: 是否匹配
        """
        actual_parts = actual_path.strip("/").split("/")
        pattern_parts = pattern_path.strip("/").split("/")

        if len(actual_parts) != len(pattern_parts):
            return False

        for actual, pattern in zip(actual_parts, pattern_parts):
            # 如果是占位符，则匹配任意值
            if pattern.startswith("{") and pattern.endswith("}"):
                continue

            # 否则需要精确匹配
            if actual != pattern:
                return False

        return True

    def is_allowed(self, path: str, method: str, role: Role) -> bool:
        """
        检查角色是否有权限访问API

        Args:
            path: API路径
            method: HTTP方法
            role: 角色枚举

        Returns:
            bool: 是否允许
        """
        permission = self.get_permission(path, method)

        if permission is None:
            # 未注册的API默认拒绝
            return False

        return permission.is_role_allowed(role)

    def get_all_permissions(self) -> List[APIPermission]:
        """获取所有已注册的权限配置"""
        return list(self._registry.values())


# 全局权限注册表实例
PERMISSION_REGISTRY = PermissionRegistry()
