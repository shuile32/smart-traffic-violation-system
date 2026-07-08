"""Celery 任务：LLM 初审"""

import json

from celery import shared_task
from loguru import logger

from app.core.database import SessionLocal
from app.models.case import Case
from app.models.intake_event import IntakeEvent
from app.models.ai_detection_result import AIDetectionResult
from app.models.violation_rule_result import ViolationRuleResult
from app.models.ai_review_result import AIReviewResult
from app.ai.adapters.llm_provider import OpenAICompatibleLLMProvider


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def ai_review_task(self, case_id: int):
    db = SessionLocal()
    try:
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            return {"error": "case not found"}

        case.status = "ai_reviewing"
        db.commit()

        # 收集证据
        intake = db.query(IntakeEvent).filter(IntakeEvent.id == case.intake_event_id).first()
        detection = (
            db.query(AIDetectionResult)
            .filter(AIDetectionResult.case_id == case_id)
            .order_by(AIDetectionResult.id.desc())
            .first()
        )
        rule_result = (
            db.query(ViolationRuleResult)
            .filter(ViolationRuleResult.case_id == case_id)
            .order_by(ViolationRuleResult.id.desc())
            .first()
        )

        # 构建 evidence_payload
        evidence = {
            "case_id": case_id,
            "source_type": intake.source_type if intake else None,
            "location": intake.location_text if intake else None,
            "captured_at": intake.captured_at.isoformat() if intake and intake.captured_at else None,
            "speed": intake.speed if intake else None,
            "plate_no": case.plate_no,
            "detection": detection.to_dict() if detection else None,
            "rule_result": rule_result.to_dict() if rule_result else None,
        }

        # 调用 LLM
        provider = OpenAICompatibleLLMProvider()
        result = provider.review(evidence)

        # 保存初审结果
        review = AIReviewResult(
            case_id=case_id,
            review_mode="text_llm",
            conclusion=result.conclusion,
            ai_confidence=result.ai_confidence,
            reason=result.reason,
            risk_points=json.dumps(result.risk_points, ensure_ascii=False),
            missing_evidence=json.dumps(result.missing_evidence, ensure_ascii=False),
            prompt_version=result.prompt_version,
        )
        db.add(review)
        db.flush()

        # 更新案件状态
        case.ai_review_id = review.id
        case.status = "pending_human_review"
        db.commit()

        logger.info(f"LLM 初审完成: case_id={case_id}, conclusion={result.conclusion}")
        return {"review_id": review.id, "conclusion": result.conclusion}

    except Exception as exc:
        logger.error(f"LLM 初审失败: case_id={case_id}, error={exc}")
        db.rollback()
        case = db.query(Case).get(case_id)
        if case:
            case.ai_failed = True
            case.status = "pending_human_review"
            db.commit()
        raise self.retry(exc=exc)
    finally:
        db.close()
