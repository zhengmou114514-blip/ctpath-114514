from __future__ import annotations

from fastapi import APIRouter, Depends

from ..auth.dependencies import require_doctor
from ..auth.permission_registry import PERMISSION_REGISTRY
from ..schemas import AuthzCapabilityResponse


router = APIRouter(tags=["authz"])


_ROLE_SECTIONS = {
    "doctor": ["doctor", "archive", "model-dashboard", "insights", "governance"],
    "nurse": ["tasks", "contacts", "flow"],
    "archivist": ["archive", "data-quality", "governance"],
    "admin": ["doctor", "archive", "model-dashboard", "insights", "governance", "tasks", "contacts", "flow", "data-quality"],
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
