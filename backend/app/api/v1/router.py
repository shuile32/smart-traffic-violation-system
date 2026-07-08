"""API v1 路由汇总"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.intakes import router as intakes_router
from app.api.v1.cases import router as cases_router
from app.api.v1.violations import router as violations_router
from app.api.v1.statistics import router as statistics_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
api_router.include_router(intakes_router, prefix="/intakes", tags=["图片接入"])
api_router.include_router(cases_router, prefix="/cases", tags=["案件审核"])
api_router.include_router(violations_router, prefix="/violations", tags=["违章查询"])
api_router.include_router(statistics_router, prefix="/statistics", tags=["统计分析"])
