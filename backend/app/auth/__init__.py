"""
认证和授权模块

提供基于角色的访问控制（RBAC）功能
"""

from .role_definitions import Role, Permission, ROLE_PERMISSIONS, get_role_permissions, has_permission
from .permission_registry import PermissionRegistry, APIPermission, PERMISSION_REGISTRY
from .rbac_middleware import RBACMiddleware, require_role, require_permission

__all__ = [
    'Role',
    'Permission',
    'ROLE_PERMISSIONS',
    'get_role_permissions',
    'has_permission',
    'PermissionRegistry',
    'APIPermission',
    'PERMISSION_REGISTRY',
    'RBACMiddleware',
    'require_role',
    'require_permission'
]
