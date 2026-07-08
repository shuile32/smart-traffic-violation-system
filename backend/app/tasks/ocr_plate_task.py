"""Celery 任务：OCR 车牌识别"""

from celery import shared_task
from loguru import logger

from app.core.database import SessionLocal
from app.models.case import Case
from app.ai.adapters.ocr_paddle import PaddleOcrEngine


@shared_task(bind=True, max_retries=1)
def ocr_plate_task(self, case_id: int, plate_crop_path: str | None):
    if not plate_crop_path:
        logger.info(f"无车牌框，跳过 OCR: case_id={case_id}")
        return {"plate_no": None}

    db = SessionLocal()
    try:
        engine = PaddleOcrEngine()
        plate_no = engine.recognize_plate(plate_crop_path)

        # 更新案件的 plate_no
        if plate_no:
            case = db.query(Case).filter(Case.id == case_id).first()
            if case:
                case.plate_no = plate_no
                db.commit()

        logger.info(f"OCR 完成: case_id={case_id}, plate_no={plate_no}")
        return {"plate_no": plate_no}

    except Exception as exc:
        logger.error(f"OCR 失败: case_id={case_id}, error={exc}")
        return {"plate_no": None}  # OCR 失败不阻塞流程，允许人工补录
    finally:
        db.close()
