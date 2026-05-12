from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from ..auth.dependencies import require_doctor, require_roles
from ..auth.permission_registry import PERMISSION_REGISTRY
from ..schemas import AuthzCapabilityResponse, UserRoleAssignmentRecord, UserRoleUpdateRequest
from ..store import list_doctors, update_doctor_role


router = APIRouter(tags=["authz"])


_ROLE_SECTIONS = {
    "doctor": [
        "doctor",
        "archive",
        "coordination",
        "insights",
    ],
    "nurse": ["tasks", "flow", "contacts", "coordination"],
    "pharmacist": [
        "drug-management",
        "pharmacy",
    ],
    "archivist": [
        "archive",
    ],
    "admin": [
        "drug-permission-management",
        "governance",
        "system",
        "model-dashboard",
        "role-workspaces",
    ],
}


@router.get("/api/authz/capabilities", response_model=AuthzCapabilityResponse)
def capabilities(doctor=Depends(require_doctor)) -> AuthzCapabilityResponse:
    role = doctor.role
    allowed_sections = _ROLE_SECTIONS.get(role, _ROLE_SECTIONS["doctor"])

    allowed_apis = []
    # PermissionRegistry uses Role enum; but require_doctor returns role string.
    # Derive allowed APIs by mapping role string -> Role enum.
    from ..auth.role_definitions import get_role_by_name

    role_enum = get_role_by_name(role)
    for perm in PERMISSION_REGISTRY.get_all_permissions():
        if perm.is_role_allowed(role_enum):
            allowed_apis.append("{0} {1}".format(perm.method, perm.path))

    return AuthzCapabilityResponse(role=role, allowedSections=allowed_sections, allowedApis=sorted(allowed_apis))


@router.get("/api/authz/users", response_model=List[UserRoleAssignmentRecord])
def list_role_assignments(current_user=Depends(require_roles("admin"))) -> List[UserRoleAssignmentRecord]:
    _ = current_user
    return [
        UserRoleAssignmentRecord(
            username=item.username,
            name=item.name,
            title=item.title,
            department=item.department,
            role=item.role,
        )
        for item in list_doctors()
    ]


@router.patch("/api/authz/users/{username}/role", response_model=UserRoleAssignmentRecord)
def patch_user_role(
    username: str,
    payload: UserRoleUpdateRequest,
    current_user=Depends(require_roles("admin")),
) -> UserRoleAssignmentRecord:
    if current_user.username == username and payload.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="管理员不能取消自己的管理员权限",
        )

    updated = update_doctor_role(username, payload.role)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return UserRoleAssignmentRecord(
        username=updated.username,
        name=updated.name,
        title=updated.title,
        department=updated.department,
        role=updated.role,
    )
