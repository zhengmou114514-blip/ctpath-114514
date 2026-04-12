"""
角色和权限定义

定义系统中的所有角色和对应的权限
"""

from enum import Enum
from typing import List, Set, Dict


class Role(str, Enum):
    """系统角色枚举"""
    ADMIN = "admin"
    DOCTOR = "doctor"
    NURSE = "nurse"
    ARCHIVIST = "archivist"


class Permission(str, Enum):
    """权限枚举"""
    # 患者管理权限
    PATIENT_VIEW = "patient:view"
    PATIENT_CREATE = "patient:create"
    PATIENT_UPDATE = "patient:update"
    PATIENT_DELETE = "patient:delete"

    # 事件管理权限
    EVENT_VIEW = "event:view"
    EVENT_CREATE = "event:create"
    EVENT_UPDATE = "event:update"
    EVENT_DELETE = "event:delete"

    # 预测权限
    PREDICTION_VIEW = "prediction:view"
    PREDICTION_RUN = "prediction:run"

    # 建议权限
    ADVICE_VIEW = "advice:view"
    ADVICE_GENERATE = "advice:generate"

    # 随访权限
    FOLLOWUP_VIEW = "followup:view"
    FOLLOWUP_CREATE = "followup:create"
    FOLLOWUP_UPDATE = "followup:update"
    FOLLOWUP_DELETE = "followup:delete"

    # 任务权限
    TASK_VIEW = "task:view"
    TASK_CREATE = "task:create"
    TASK_UPDATE = "task:update"
    TASK_DELETE = "task:delete"

    # 系统管理权限
    SYSTEM_CONFIG = "system:config"
    SYSTEM_MONITOR = "system:monitor"
    USER_MANAGE = "user:manage"


# 角色权限映射
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.ADMIN: {
        # 管理员拥有所有权限
        Permission.PATIENT_VIEW,
        Permission.PATIENT_CREATE,
        Permission.PATIENT_UPDATE,
        Permission.PATIENT_DELETE,
        Permission.EVENT_VIEW,
        Permission.EVENT_CREATE,
        Permission.EVENT_UPDATE,
        Permission.EVENT_DELETE,
        Permission.PREDICTION_VIEW,
        Permission.PREDICTION_RUN,
        Permission.ADVICE_VIEW,
        Permission.ADVICE_GENERATE,
        Permission.FOLLOWUP_VIEW,
        Permission.FOLLOWUP_CREATE,
        Permission.FOLLOWUP_UPDATE,
        Permission.FOLLOWUP_DELETE,
        Permission.TASK_VIEW,
        Permission.TASK_CREATE,
        Permission.TASK_UPDATE,
        Permission.TASK_DELETE,
        Permission.SYSTEM_CONFIG,
        Permission.SYSTEM_MONITOR,
        Permission.USER_MANAGE,
    },

    Role.DOCTOR: {
        # 医生权限
        Permission.PATIENT_VIEW,
        Permission.PATIENT_CREATE,
        Permission.PATIENT_UPDATE,
        Permission.EVENT_VIEW,
        Permission.EVENT_CREATE,
        Permission.EVENT_UPDATE,
        Permission.PREDICTION_VIEW,
        Permission.PREDICTION_RUN,
        Permission.ADVICE_VIEW,
        Permission.ADVICE_GENERATE,
        Permission.FOLLOWUP_VIEW,
        Permission.FOLLOWUP_CREATE,
        Permission.FOLLOWUP_UPDATE,
        Permission.TASK_VIEW,
        Permission.TASK_CREATE,
        Permission.TASK_UPDATE,
    },

    Role.NURSE: {
        # 护士权限
        Permission.PATIENT_VIEW,
        Permission.EVENT_VIEW,
        Permission.EVENT_CREATE,
        Permission.PREDICTION_VIEW,
        Permission.ADVICE_VIEW,
        Permission.FOLLOWUP_VIEW,
        Permission.FOLLOWUP_CREATE,
        Permission.FOLLOWUP_UPDATE,
        Permission.TASK_VIEW,
        Permission.TASK_UPDATE,
    },

    Role.ARCHIVIST: {
        # 档案管理员权限
        Permission.PATIENT_VIEW,
        Permission.PATIENT_CREATE,
        Permission.PATIENT_UPDATE,
        Permission.EVENT_VIEW,
        Permission.EVENT_CREATE,
        Permission.EVENT_UPDATE,
        Permission.PREDICTION_VIEW,
        Permission.FOLLOWUP_VIEW,
        Permission.TASK_VIEW,
    },
}


def get_role_permissions(role: Role) -> Set[Permission]:
    """
    获取角色的所有权限

    Args:
        role: 角色枚举

    Returns:
        Set[Permission]: 权限集合
    """
    return ROLE_PERMISSIONS.get(role, set())


def has_permission(role: Role, permission: Permission) -> bool:
    """
    检查角色是否有指定权限

    Args:
        role: 角色枚举
        permission: 权限枚举

    Returns:
        bool: 是否有权限
    """
    return permission in get_role_permissions(role)


def get_role_by_name(name: str) -> Role:
    """
    根据名称获取角色

    Args:
        name: 角色名称

    Returns:
        Role: 角色枚举

    Raises:
        ValueError: 角色名称无效
    """
    try:
        return Role(name.lower())
    except ValueError:
        raise ValueError(f"Invalid role name: {name}")


def validate_role(role_str: str) -> bool:
    """
    验证角色字符串是否有效

    Args:
        role_str: 角色字符串

    Returns:
        bool: 是否有效
    """
    try:
        Role(role_str.lower())
        return True
    except ValueError:
        return False
