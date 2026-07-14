from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import require_role
from app.models.user import User
from app.schemas.violation_rule import (
    ViolationRuleCreateIn, ViolationRuleListResponse, ViolationRuleOut, ViolationRuleUpdateIn)
from app.services.violation_rule_service import ViolationRuleService

router = APIRouter(prefix="/admin/rules", tags=["rules"])


@router.post("", response_model=ViolationRuleOut, status_code=201)
def create_rule(body: ViolationRuleCreateIn, db: Session = Depends(get_db),
                _: User = Depends(require_role("admin"))) -> ViolationRuleOut:
    r = ViolationRuleService(db).create_rule(
        rule_code=body.rule_code, violation_type=body.violation_type,
        rule_type=body.rule_type, params=body.params, description=body.description)
    return ViolationRuleOut.model_validate(r)


@router.get("", response_model=ViolationRuleListResponse)
def list_rules(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
               rule_type: str | None = None, db: Session = Depends(get_db),
               _: User = Depends(require_role("admin"))) -> ViolationRuleListResponse:
    res = ViolationRuleService(db).list_rules(page=page, page_size=page_size, rule_type=rule_type)
    return ViolationRuleListResponse(
        items=[ViolationRuleOut.model_validate(r) for r in res["items"]],
        total=res["total"], page=res["page"], page_size=res["page_size"])


@router.patch("/{rule_id}", response_model=ViolationRuleOut)
def update_rule(rule_id: int, body: ViolationRuleUpdateIn,
                db: Session = Depends(get_db),
                _: User = Depends(require_role("admin"))) -> ViolationRuleOut:
    r = ViolationRuleService(db).update_rule(
        rule_id, violation_type=body.violation_type, rule_type=body.rule_type,
        params=body.params, description=body.description, is_active=body.is_active)
    return ViolationRuleOut.model_validate(r)


@router.delete("/{rule_id}", status_code=204)
def delete_rule(rule_id: int, db: Session = Depends(get_db),
                _: User = Depends(require_role("admin"))) -> None:
    ViolationRuleService(db).delete_rule(rule_id)
