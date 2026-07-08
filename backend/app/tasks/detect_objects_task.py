"""Celery 任务：YOLO 目标检测"""

import json

from celery import shared_task
from loguru import logger

from app.core.database import SessionLocal
from app.models.case import Case
from app.models.ai_detection_result import AIDetectionResult
from app.ai.adapters.yolo_ultralytics import UltralyticsYoloDetector


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def detect_objects_task(self, case_id: int, image_path: str):
    db = SessionLocal()
    try:
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            return {"error": "case not found"}

        case.status = "detecting"
        db.commit()

        detector = UltralyticsYoloDetector()
        result = detector.detect(image_path)

        detection = AIDetectionResult(
            case_id=case_id,
            model_name="yolov8n",
            model_version=result.model_version,
            detected_objects=json.dumps(result.objects, ensure_ascii=False),
            object_confidences=json.dumps(
                {obj["label"]: obj["confidence"] for obj in result.objects},
                ensure_ascii=False,
            ),
            plate_bbox=json.dumps(result.plate_bbox) if result.plate_bbox else None,
            vehicle_bbox=json.dumps(result.vehicle_bbox) if result.vehicle_bbox else None,
            annotated_image_url=result.annotated_image_path,
        )
        db.add(detection)
        db.commit()
        db.refresh(detection)

        logger.info(f"YOLO 检测完成: case_id={case_id}, objects={len(result.objects)}")
        return {"detection_id": detection.id, "objects_count": len(result.objects)}

    except Exception as exc:
        logger.error(f"YOLO 检测失败: case_id={case_id}, error={exc}")
        db.rollback()
        # 标记案件 AI 失败
        case = db.query(Case).get(case_id)
        if case:
            case.ai_failed = True
            case.status = "pending_human_review"
            db.commit()
        raise self.retry(exc=exc)
    finally:
        db.close()
