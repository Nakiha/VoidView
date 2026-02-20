"""API v1 路由汇总"""

from fastapi import APIRouter

from .auth import router as auth_router
from .users import router as users_router
from .experiments import router as experiments_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(experiments_router)


@api_router.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "ok"}
