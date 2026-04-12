from typing import Optional

from fastapi import Depends, Header, HTTPException

from ..store import get_doctor_by_token, is_token_valid


def require_token(authorization: Optional[str] = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = authorization.replace("Bearer ", "", 1).strip()
    if not is_token_valid(token):
        raise HTTPException(status_code=401, detail="Invalid token")

    return token


def require_doctor(token: str = Depends(require_token)):
    doctor = get_doctor_by_token(token)
    if doctor is None:
        raise HTTPException(status_code=401, detail="Invalid session")
    return doctor


def require_roles(*allowed_roles: str):
    def dependency(doctor=Depends(require_doctor)):
        if doctor.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Role not allowed for this action")
        return doctor

    return dependency
