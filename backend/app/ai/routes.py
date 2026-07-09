"""内部 AI 接口路由 — 无状态探测，对接 AI adapter。"""
import os
import tempfile

from fastapi import APIRouter, Depends, File, UploadFile

from app.ai.providers import get_ocr_engine, get_yolo_detector
from app.core.deps import require_role
from app.models.user import User
from app.schemas.ai import DetectionOut, OcrOut

internal_router = APIRouter(prefix="/internal/ai", tags=["internal-ai"])


def _save_upload(image: UploadFile) -> str:
    suffix = os.path.splitext(image.filename or "image.jpg")[1] or ".jpg"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(image.file.read())
    tmp.close()
    return tmp.name


@internal_router.post("/yolo/detect", response_model=DetectionOut)
def yolo_detect(
    image: UploadFile = File(...),
    detector=Depends(get_yolo_detector),
    _: User = Depends(require_role("admin", "reviewer")),
) -> DetectionOut:
    path = _save_upload(image)
    try:
        r = detector.detect(path)
    finally:
        os.unlink(path)
    return DetectionOut(
        objects=r.objects,
        vehicle_bbox=r.vehicle_bbox,
        plate_bbox=r.plate_bbox,
        annotated_image_url=r.annotated_image_path,
        model_version=r.model_version,
    )


@internal_router.post("/ocr/plate", response_model=OcrOut)
def ocr_plate(
    image: UploadFile = File(...),
    engine=Depends(get_ocr_engine),
    _: User = Depends(require_role("admin", "reviewer")),
) -> OcrOut:
    path = _save_upload(image)
    try:
        plate = engine.recognize_plate(path)
    finally:
        os.unlink(path)
    return OcrOut(plate_no=plate)
