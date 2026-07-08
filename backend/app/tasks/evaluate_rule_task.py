"""Celery 任务：违章规则判定"""

import json

from celery import shared_task
from loguru import logger

from app.core.database import SessionLocal
from app.models.case import Case
from app.models.intake_event import IntakeEvent
from app.models.ai_detection_result import AIDetectionResult
from app.models.violation_rule import ViolationRule
from app.models.violation_rule_result import ViolationRuleResult
from app.ai.rules.roi_evaluator import RoiRuleEvaluator
from app.ai.adapters.base import DetectionResult


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def evaluate_rule_task(self, case_id: int, detection_id: int):
    db = SessionLocal()
    try:
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            return {"error": "case not found"}

        # 获取检测结果
        detection = db.query(AIDetectionResult).filter(AIDetectionResult.id == detection_id).first()
        if not detection:
            return {"error": "detection not found"}

        # 获取接入事件（含 speed 等元数据）
        intake = db.query(IntakeEvent).filter(IntakeEvent.id == case.intake_event_id).first()

        # 获取启用的违章规则
        rules = db.query(ViolationRule).filter(ViolationRule.is_active == True).all()

        # 构建 DetectionResult 对象
        det_result = DetectionResult(
            objects=json.loads(detection.detected_objects) if detection.detected_objects else [],
            vehicle_bbox=json.loads(detection.vehicle_bbox) if detection.vehicle_bbox else None,
            plate_bbox=json.loads(detection.plate_bbox) if detection.plate_bbox else None,
            annotated_image_path=detection.annotated_image_url,
            model_version=detection.model_version,
        )

        evaluator = RoiRuleEvaluator()
        # 注入检测对象供超速判定用
        evaluator._detection_objects = det_result.objects

        intake_dict = intake.to_dict() if intake else {}

        best_result = None
        for rule in rules:
            rule_dict = rule.to_dict()
            result = evaluator.evaluate(det_result, case.plate_no, intake_dict, rule_dict)

            # 保存每个规则判定结果
            db_result = ViolationRuleResult(
                case_id=case_id,
                candidate_violation_type=result.candidate_violation_type,
                rule_code=result.rule_code,
                rule_matched=result.rule_matched,
                evidence_level=result.evidence_level,
                evidence_items=json.dumps(result.evidence_items, ensure_ascii=False),
                missing_evidence=json.dumps(result.missing_evidence, ensure_ascii=False),
                reason=result.reason,
            )
            db.add(db_result)

            # 取第一个匹配的规则作为最佳结果
            if best_result is None and result.rule_matched:
                best_result = db_result

        db.commit()
        if best_result:
            db.refresh(best_result)

        logger.info(f"规则判定完成: case_id={case_id}, matched={best_result is not None}")
        return {
            "result_id": best_result.id if best_result else None,
            "rule_matched": best_result is not None,
        }

    except Exception as exc:
        logger.error(f"规则判定失败: case_id={case_id}, error={exc}")
        db.rollback()
        case = db.query(Case).get(case_id)
        if case:
            case.ai_failed = True
            case.status = "pending_human_review"
            db.commit()
        raise self.retry(exc=exc)
    finally:
        db.close()
