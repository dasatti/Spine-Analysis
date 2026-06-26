import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.pipeline.loader import validate_detector_config
from app.routers import api_router
from app.services.storage_service import storage_service
from app.utils.exceptions import AppError

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title="SpinePose API",
        version="1.0.0",
        description="Clinical-grade AI-powered posture and spine analysis platform.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    async def startup() -> None:
        storage_service.ensure_bucket()
        validate_detector_config()
        logger.info("SpinePose API started with detector_model=%s", settings.detector_model)

    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
        if isinstance(exc.detail, dict) and "code" in exc.detail:
            return JSONResponse(status_code=exc.status_code, content=exc.detail)
        if exc.status_code == status.HTTP_404_NOT_FOUND:
            return JSONResponse(
                status_code=exc.status_code,
                content={"code": "NOT_FOUND", "message": str(exc.detail)},
            )
        return JSONResponse(status_code=exc.status_code, content=exc.detail)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"code": "VALIDATION_ERROR", "detail": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_request: Request, _exc: Exception) -> JSONResponse:
        logger.exception("Unhandled server error")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"code": "INTERNAL_ERROR", "message": "An unexpected error occurred"},
        )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "detector_model": settings.detector_model}

    app.include_router(api_router)
    return app


app = create_app()
