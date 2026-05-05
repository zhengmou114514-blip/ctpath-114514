from fastapi import APIRouter

from ..modules.patients.router import router as patients_module_router


router = APIRouter(tags=["patients"])
router.include_router(patients_module_router)
