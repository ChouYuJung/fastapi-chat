from fastapi import APIRouter

from .v1._router import router as v1_router

router = APIRouter()
router.include_router(v1_router, prefix="/v1")
