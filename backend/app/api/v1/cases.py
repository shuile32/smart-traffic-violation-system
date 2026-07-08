"""案件审核路由"""

import math
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.permissions import RequireReviewer
from app.models.case import Case
from app.models.intake_event import IntakeEvent
from app.models.ai_detection_result import AIDetectionResult
from app.models.violation_rule_result import ViolationRuleResult
from app.models.ai_review_result import AIReviewResult
from app.models.media_asset import MediaAsset
from app.models.violation import Violation
from app.models.vehicle import Vehicle
from app.models.audit_log import AuditLog
from schemas.common import APIResponse

router = APIRouter()


@router.get("", response_model=APIResponse[dict])
async def list_cases(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    source_type: str | None = None,
    _: bool = Depends(RequireReviewer),
    db: Session = Depends(get_db),
):
    query = db.query(Case)
    if status:
        query = query.filter(Case.status == status)
    if source_type:
        query = query.join(IntakeEvent, Case.intake_event_id == IntakeEvent.id).filter(
            IntakeEvent.source_type == source_type
        )

    total = query.count()
    total_pages = max(1, math.ceil(total / page_size))
    items = query.order_by(Case.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return APIResponse(data={
        "items": [_case_detail(db, c) for c in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    })


@router.get("/{case_id}", response_model=APIResponse[dict])
async def get_case(
    case_id: int,
    _: bool = Depends(RequireReviewer),
    db: Session = Depends(get_db),
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        from fastapi import HTTPException
        raise HTTPException(404, detail="案件不存在")
    return APIResponse(data=_case_detail(db, case))


@router.post("/{case_id}/approve", response_model=APIResponse[dict])
async def approve_case(
    case_id: int,
    body: dict,
    payload: dict = Depends(get_current_user),
    _: bool = Depends(RequireReviewer),
    db: Session = Depends(get_db),
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        from fastapi import HTTPException
        raise HTTPException(404, detail="案件不存在")

    if case.status != "pending_human_review":
        from fastapi import HTTPException
        raise HTTPException(400, detail="案件当前状态不可审核")

    plate_no = body.get("plate_no", case.plate_no)
    violation_type = body.get("violation_type", "")

    # 更新案件
    case.plate_no = plate_no
    case.violation_type = violation_type
    case.status = "approved"
    case.reviewer_id = int(payload["sub"])
    case.review_opinion = body.get("review_opinion", "")
    case.reviewed_at = datetime.now(timezone.utc)

    # 查找车辆
    vehicle = db.query(Vehicle).filter(Vehicle.plate_no == plate_no).first()

    # 创建正式违章
    violation_no = f"VIO{datetime.now().strftime('%Y%m%d%H%M%S')}{case_id:04d}"
    violation = Violation(
        violation_no=violation_no,
        case_id=case_id,
        vehicle_id=vehicle.id if vehicle else None,
        owner_id=vehicle.owner_id if vehicle else None,
        plate_no=plate_no,
        violation_type=violation_type,
        occurred_at=body.get("occurred_at", datetime.now(timezone.utc)),
        location_text=body.get("location_text", ""),
        fine_amount=body.get("fine_amount", 200),
        points=body.get("points", 3),
        status="pending",
    )
    db.add(violation)
    db.flush()

    # 审计日志
    audit = AuditLog(
        user_id=int(payload["sub"]),
        username=payload.get("sub"),
        action="case:approve",
        target_type="case",
        target_id=case_id,
        detail=f"通过案件 {case.case_no}，违章类型 {violation_type}",
    )
    db.add(audit)

    case.status = "archived"
    db.commit()

    # 异步发送通知
    try:
        from app.tasks.send_notification_task import send_notification_task
        send_notification_task.delay(violation.id)
    except Exception:
        pass

    return APIResponse(data=case.to_dict(), message="审核通过，已生成违章记录")


@router.post("/{case_id}/reject", response_model=APIResponse[dict])
async def reject_case(
    case_id: int,
    body: dict,
    payload: dict = Depends(get_current_user),
    _: bool = Depends(RequireReviewer),
    db: Session = Depends(get_db),
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        from fastapi import HTTPException
        raise HTTPException(404, detail="案件不存在")

    case.status = "rejected"
    case.reviewer_id = int(payload["sub"])
    case.reject_reason = body.get("reject_reason", "")
    case.reviewed_at = datetime.now(timezone.utc)

    audit = AuditLog(
        user_id=int(payload["sub"]),
        username=payload.get("sub"),
        action="case:reject",
        target_type="case",
        target_id=case_id,
        detail=f"驳回案件 {case.case_no}: {case.reject_reason}",
    )
    db.add(audit)
    db.commit()

    return APIResponse(data=case.to_dict(), message="案件已驳回")


@router.post("/{case_id}/request-recheck", response_model=APIResponse[dict])
async def request_recheck(
    case_id: int,
    _: bool = Depends(RequireReviewer),
    db: Session = Depends(get_db),
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        from fastapi import HTTPException
        raise HTTPException(404, detail="案件不存在")

    # 重新投递 AI 任务链
    from app.tasks.detect_objects_task import detect_objects_task

    media = db.query(MediaAsset).filter(
        MediaAsset.intake_event_id == case.intake_event_id,
        MediaAsset.asset_type == "original",
    ).first()

    if media:
        image_path = media.url
        detect_objects_task.delay(case.id, image_path)

    case.status = "detecting"
    db.commit()

    return APIResponse(data=case.to_dict(), message="已重新提交 AI 识别")


def _case_detail(db: Session, case: Case) -> dict:
    """组装案件完整信息（含 AI 全链路数据）"""
    intake = db.query(IntakeEvent).filter(IntakeEvent.id == case.intake_event_id).first()
    media = (
        db.query(MediaAsset)
        .filter(MediaAsset.intake_event_id == case.intake_event_id)
        .all()
    )
    detection = (
        db.query(AIDetectionResult)
        .filter(AIDetectionResult.case_id == case.id)
        .order_by(AIDetectionResult.id.desc())
        .first()
    )
    rule_result = (
        db.query(ViolationRuleResult)
        .filter(ViolationRuleResult.case_id == case.id)
        .order_by(ViolationRuleResult.id.desc())
        .first()
    )
    ai_review = (
        db.query(AIReviewResult)
        .filter(AIReviewResult.case_id == case.id)
        .order_by(AIReviewResult.id.desc())
        .first()
    )

    return {
        **case.to_dict(),
        "intake_event": intake.to_dict() if intake else None,
        "media": [m.to_dict() for m in media],
        "detection_result": detection.to_dict() if detection else None,
        "rule_result": rule_result.to_dict() if rule_result else None,
        "ai_review": ai_review.to_dict() if ai_review else None,
    }
