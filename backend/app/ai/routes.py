"""内部 AI 路由 — 调试/手动触发用，生产走 Celery chain"""

from fastapi import APIRouter, UploadFile, File, Depends
from fastapi.responses import JSONResponse

from app.core.security import get_current_user
from app.core.permissions import RequireReviewer

ai_router = APIRouter(tags=["内部 AI"])


@ai_router.post("/yolo/detect")
async def yolo_detect(
    image: UploadFile = File(...),
    _: bool = Depends(RequireReviewer),
):
    """手动触发 YOLO 检测（调试用）"""
    import tempfile, os
    from app.ai.adapters.yolo_ultralytics import UltralyticsYoloDetector

    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        content = await image.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        detector = UltralyticsYoloDetector()
        result = detector.detect(tmp_path)
        return JSONResponse(content={
            "objects": result.objects,
            "vehicle_bbox": result.vehicle_bbox,
            "plate_bbox": result.plate_bbox,
            "model_version": result.model_version,
        })
    finally:
        os.unlink(tmp_path)


@ai_router.post("/ocr/plate")
async def ocr_plate(
    image: UploadFile = File(...),
    _: bool = Depends(RequireReviewer),
):
    """手动触发 OCR（调试用）"""
    import tempfile, os
    from app.ai.adapters.ocr_paddle import PaddleOcrEngine

    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        content = await image.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        engine = PaddleOcrEngine()
        plate_no = engine.recognize_plate(tmp_path)
        return JSONResponse(content={"plate_no": plate_no})
    finally:
        os.unlink(tmp_path)


@ai_router.post("/rules/evaluate")
async def rules_evaluate(
    case_data: dict,
    _: bool = Depends(RequireReviewer),
):
    """手动触发规则判定（调试用）"""
    from app.ai.rules.roi_evaluator import RoiRuleEvaluator
    from app.ai.adapters.base import DetectionResult

    evaluator = RoiRuleEvaluator()
    det = DetectionResult(
        objects=case_data.get("objects", []),
        vehicle_bbox=case_data.get("vehicle_bbox"),
        plate_bbox=case_data.get("plate_bbox"),
        annotated_image_path=None,
        model_version="manual",
    )
    evaluator._detection_objects = det.objects
    result = evaluator.evaluate(det, None, case_data.get("intake_event", {}), case_data.get("rule", {}))
    return JSONResponse(content={
        "rule_matched": result.rule_matched,
        "evidence_level": result.evidence_level,
        "reason": result.reason,
    })


@ai_router.post("/review/text")
async def text_review(
    evidence: dict,
    _: bool = Depends(RequireReviewer),
):
    """手动触发 LLM 初审（调试用）"""
    from app.ai.adapters.llm_provider import OpenAICompatibleLLMProvider

    provider = OpenAICompatibleLLMProvider()
    result = provider.review(evidence)
    return JSONResponse(content={
        "conclusion": result.conclusion,
        "confidence": result.ai_confidence,
        "reason": result.reason,
    })
