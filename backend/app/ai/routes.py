"""内部 AI 接口路由 — 无状态探测，对接 AI adapter。"""
import os
import tempfile

from fastapi import APIRouter, Depends, File, UploadFile

from app.ai.adapters.base import DetectionResult
from app.ai.providers import (
    get_llm_provider,
    get_ocr_engine,
    get_rule_evaluator,
    get_yolo_detector,
)
from app.core.deps import require_role
from app.models.user import User
from app.schemas.ai import DetectionOut, OcrOut, ReviewOut, RuleEvalOut

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


@internal_router.post("/rules/evaluate", response_model=RuleEvalOut)
def rules_evaluate(
    body: dict,
    evaluator=Depends(get_rule_evaluator),
    _: User = Depends(require_role("admin", "reviewer")),
) -> RuleEvalOut:
    detection_data = body.get("detection", {})
    detection = DetectionResult(
        objects=detection_data.get("objects", []),
        vehicle_bbox=detection_data.get("vehicle_bbox"),
        plate_bbox=detection_data.get("plate_bbox"),
        annotated_image_path=detection_data.get("annotated_image_url"),
        model_version=detection_data.get("model_version", ""),
    )
    r = evaluator.evaluate(
        detection=detection,
        ocr_result=body.get("ocr_result"),
        intake_event=body.get("intake_event", {}),
        rule=body.get("rule", {}),
    )
    return RuleEvalOut(
        rule_matched=r.rule_matched,
        evidence_level=r.evidence_level,
        evidence_items=r.evidence_items,
        reason=r.reason,
    )


@internal_router.post("/review/text", response_model=ReviewOut)
def review_text(
    body: dict,
    provider=Depends(get_llm_provider),
    _: User = Depends(require_role("admin", "reviewer")),
) -> ReviewOut:
    r = provider.review(body)
    return ReviewOut(
        conclusion=r.conclusion,
        ai_confidence=r.ai_confidence,
        reason=r.reason,
    )
