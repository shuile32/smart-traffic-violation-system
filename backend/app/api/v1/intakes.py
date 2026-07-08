"""图片接入路由 — 市民/摄像头/后台上传"""

import hashlib
import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from celery import chain

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.permissions import RequireReviewer
from app.core.middleware import verify_camera_auth
from app.models.intake_event import IntakeEvent
from app.models.media_asset import MediaAsset
from app.models.case import Case
from schemas.common import APIResponse

router = APIRouter()

MEDIA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "media")


def _save_image(image: UploadFile) -> tuple[str, str, int]:
    """保存图片到本地，返回 (file_path, image_hash, file_size)"""
    os.makedirs(MEDIA_DIR, exist_ok=True)
    content = image.file.read()
    image_hash = hashlib.sha256(content).hexdigest()
    ext = os.path.splitext(image.filename or "image.jpg")[1] or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(MEDIA_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(content)
    return filepath, image_hash, len(content)


def _create_case(db: Session, intake: IntakeEvent, media: MediaAsset) -> Case:
    """创建案件并投递 AI 任务链"""
    case_no = f"CASE{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:4].upper()}"
    case = Case(case_no=case_no, intake_event_id=intake.id, status="uploaded")
    db.add(case)
    db.commit()
    db.refresh(case)

    # 投递 Celery chain: detect → ocr → evaluate → review
    from app.tasks.detect_objects_task import detect_objects_task
    from app.tasks.ocr_plate_task import ocr_plate_task
    from app.tasks.evaluate_rule_task import evaluate_rule_task
    from app.tasks.ai_review_task import ai_review_task

    image_path = media.url.replace(f"/media/", f"{MEDIA_DIR}/") if media.url.startswith("/media/") else media.url

    workflow = chain(
        detect_objects_task.s(case.id, image_path),
        ocr_plate_task.s(),
        evaluate_rule_task.s(),
        ai_review_task.s(),
    )
    workflow.apply_async()

    return case


# ── 市民随手拍 ────────────────────────────────────

@router.post("/citizen-reports", response_model=APIResponse[dict])
async def citizen_report(
    image: UploadFile = File(...),
    location_text: str = Form(...),
    captured_at: str = Form(...),  # ISO datetime
    description: str = Form(""),
    payload: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    filepath, img_hash, file_size = _save_image(image)

    intake = IntakeEvent(
        source_type="citizen",
        source_id=int(payload["sub"]),
        location_text=location_text,
        captured_at=datetime.fromisoformat(captured_at),
        image_hash=img_hash,
        description=description,
        status="uploaded",
    )
    db.add(intake)
    db.flush()

    media = MediaAsset(
        intake_event_id=intake.id,
        asset_type="original",
        url=f"/media/{os.path.basename(filepath)}",
        mime_type=image.content_type or "image/jpeg",
        size=file_size,
    )
    db.add(media)
    db.commit()
    db.refresh(intake)

    case = _create_case(db, intake, media)

    return APIResponse(data={
        "case_id": case.id,
        "case_no": case.case_no,
        "status": case.status,
        "message": "图片已接收，正在进行 AI 识别",
    })


# ── 摄像头抓拍 ────────────────────────────────────

@router.post("/camera-captures", response_model=APIResponse[dict])
async def camera_capture(
    image: UploadFile = File(...),
    camera_id: str = Form(...),  # 即 device_code
    captured_at: str = Form(...),
    location_text: str = Form(""),
    speed: float = Form(None),
    camera_device_id: int = Depends(verify_camera_auth),
    db: Session = Depends(get_db),
):
    filepath, img_hash, file_size = _save_image(image)

    intake = IntakeEvent(
        source_type="camera",
        source_id=camera_device_id,
        location_text=location_text,
        captured_at=datetime.fromisoformat(captured_at),
        speed=speed,
        image_hash=img_hash,
        status="uploaded",
    )
    db.add(intake)
    db.flush()

    media = MediaAsset(
        intake_event_id=intake.id,
        asset_type="original",
        url=f"/media/{os.path.basename(filepath)}",
        mime_type=image.content_type or "image/jpeg",
        size=file_size,
    )
    db.add(media)
    db.commit()
    db.refresh(intake)

    case = _create_case(db, intake, media)

    return APIResponse(data={
        "case_id": case.id,
        "case_no": case.case_no,
        "status": case.status,
        "message": "图片已接收，正在进行 AI 识别",
    })


# ── 管理员后台上传 ─────────────────────────────────

@router.post("/admin-uploads", response_model=APIResponse[dict])
async def admin_upload(
    image: UploadFile = File(...),
    location_text: str = Form(""),
    captured_at: str = Form(...),
    description: str = Form(""),
    payload: dict = Depends(get_current_user),
    _: bool = Depends(RequireReviewer),
    db: Session = Depends(get_db),
):
    filepath, img_hash, file_size = _save_image(image)

    intake = IntakeEvent(
        source_type="admin",
        source_id=int(payload["sub"]),
        location_text=location_text,
        captured_at=datetime.fromisoformat(captured_at),
        image_hash=img_hash,
        description=description,
        status="uploaded",
    )
    db.add(intake)
    db.flush()

    media = MediaAsset(
        intake_event_id=intake.id,
        asset_type="original",
        url=f"/media/{os.path.basename(filepath)}",
        mime_type=image.content_type or "image/jpeg",
        size=file_size,
    )
    db.add(media)
    db.commit()
    db.refresh(intake)

    case = _create_case(db, intake, media)

    return APIResponse(data={
        "case_id": case.id,
        "case_no": case.case_no,
        "status": case.status,
        "message": "图片已接收，正在进行 AI 识别",
    })
