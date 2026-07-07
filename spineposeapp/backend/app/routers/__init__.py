from fastapi import APIRouter

from app.routers import admin, auth, doctors, patients, scans

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(doctors.router, tags=["doctors"])
api_router.include_router(patients.router, prefix="/patients", tags=["patients"])
api_router.include_router(scans.router, prefix="/scans", tags=["scans"])

__all__ = ["api_router"]
