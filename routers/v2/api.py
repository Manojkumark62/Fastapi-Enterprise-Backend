"""Version 2 API aggregation over the same modular resource routers."""

from fastapi import APIRouter

from routers.v1.api import api_router as resource_router

api_router = APIRouter()
api_router.include_router(resource_router)