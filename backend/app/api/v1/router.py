"""
API Router Configuration
"""
from fastapi import APIRouter
from app.api.v1.endpoints import auth, document, access

router = APIRouter()

# Include endpoint routers
router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(document.router, prefix="/documents", tags=["Documents"])
router.include_router(access.router, prefix="/access", tags=["Access Control"])
