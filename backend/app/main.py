from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from app.ai.routes import internal_router
from app.api.v1.router import api_router
from app.core.config import settings

app = FastAPI(title="交通违章智能管理平台 API")
app.include_router(api_router)
app.include_router(internal_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/media/{filename}", response_class=FileResponse)
def get_media(filename: str) -> FileResponse:
    storage_root = Path(settings.MEDIA_STORAGE_DIR).resolve()
    if filename in {".", ".."} or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=404, detail="Media file not found")

    media_path = (storage_root / filename).resolve()
    if media_path.parent != storage_root or not media_path.is_file():
        raise HTTPException(status_code=404, detail="Media file not found")
    return FileResponse(media_path)
