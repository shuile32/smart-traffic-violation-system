from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.violation_rule import ViolationRule


class ViolationRuleService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_rule(self, *, rule_code: str, violation_type: str, rule_type: str,
                    params: str | None, description: str | None) -> ViolationRule:
        if self.db.query(ViolationRule).filter_by(rule_code=rule_code).first():
            raise HTTPException(status_code=409, detail="规则代码已存在")
        r = ViolationRule(rule_code=rule_code, violation_type=violation_type,
                          rule_type=rule_type, params=params, description=description)
        self.db.add(r)
        self.db.commit()
        self.db.refresh(r)
        return r

    def list_rules(self, *, page: int, page_size: int, rule_type: str | None = None) -> dict:
        q = self.db.query(ViolationRule)
        if rule_type:
            q = q.filter(ViolationRule.rule_type == rule_type)
        total = q.count()
        items = q.order_by(ViolationRule.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def get_rule(self, rule_id: int) -> ViolationRule:
        r = self.db.get(ViolationRule, rule_id)
        if r is None:
            raise HTTPException(status_code=404, detail="规则不存在")
        return r

    def update_rule(self, rule_id: int, *, violation_type: str | None, rule_type: str | None,
                    params: str | None, description: str | None, is_active: bool | None) -> ViolationRule:
        r = self.get_rule(rule_id)
        if violation_type is not None:
            r.violation_type = violation_type
        if rule_type is not None:
            r.rule_type = rule_type
        if params is not None:
            r.params = params
        if description is not None:
            r.description = description
        if is_active is not None:
            r.is_active = is_active
        self.db.commit()
        self.db.refresh(r)
        return r

    def delete_rule(self, rule_id: int) -> None:
        rule = self.get_rule(rule_id)
        self.db.delete(rule)
        self.db.commit()
