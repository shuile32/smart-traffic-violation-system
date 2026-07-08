"""交通违章智能管理平台 · 第一阶段 — FastAPI 入口"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"🚀 {settings.APP_NAME} 启动 (第一阶段)")
    yield
    logger.info(f"🛑 {settings.APP_NAME} 已关闭")


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    from fastapi import HTTPException
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.status_code, "message": exc.detail, "data": None},
        )
    logger.error(f"未捕获异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"code": 500, "message": "服务器内部错误", "data": None},
    )


# 注册路由
from app.api.v1.router import api_router
from app.ai.routes import ai_router

app.include_router(api_router, prefix=settings.API_V1_PREFIX)
app.include_router(ai_router, prefix="/internal/ai")

# 静态文件（原图/标注图）
import os
os.makedirs(settings.MEDIA_STORAGE_DIR, exist_ok=True)
app.mount(settings.MEDIA_URL_PREFIX, StaticFiles(directory=settings.MEDIA_STORAGE_DIR), name="media")


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME, "phase": 1}
