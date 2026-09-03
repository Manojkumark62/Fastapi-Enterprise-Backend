"""
Application entrypoint. Run with: uvicorn app.main:app --reload

Kept intentionally thin — CORS/logging/router wiring only. Business
logic lives in services/, HTTP concerns live in routers/, this file's
only job is assembling them into one FastAPI instance.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from database.session import engine
from database.base import Base

from core.config import settings
from core.logging_config import setup_logging
from core.middleware import RequestContextMiddleware
from core.rate_limit import RateLimitMiddleware
from core.security_headers import SecurityHeadersMiddleware
from exceptions.custom_exceptions import AppException
from routers.v1.api import api_router
from routers.v2.api import api_router as api_v2_router
from routers.health import router as health_router
import services.audit_service

setup_logging()

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    debug=settings.DEBUG,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)


@app.exception_handler(AppException)
async def app_exception_handler(_: Request, exc: AppException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(_: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": jsonable_encoder(exc.errors())})

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_PREFIX)
app.include_router(api_v2_router, prefix=settings.API_V2_PREFIX)
app.include_router(health_router)


@app.get("/")
def root():
    return {
        "name": settings.PROJECT_NAME,
        "status": "running",
        "swagger_ui": "/docs",
        "openapi_json": "/openapi.json",
        "redoc": "/redoc",
    }


@app.get("/swagger", include_in_schema=False)
def swagger_alias():
    return RedirectResponse(url="/docs")
