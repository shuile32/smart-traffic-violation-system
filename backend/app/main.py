import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.ai.routes import internal_router
from app.api.v1.router import api_router
from app.core.config import settings

app = FastAPI(title="Traffic Violation Management API")
os.makedirs(settings.MEDIA_STORAGE_DIR, exist_ok=True)
app.include_router(api_router)
app.include_router(internal_router)
app.mount("/media", StaticFiles(directory=settings.MEDIA_STORAGE_DIR), name="media")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
