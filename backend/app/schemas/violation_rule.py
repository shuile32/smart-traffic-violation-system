from datetime import datetime

from pydantic import BaseModel


class ViolationRuleOut(BaseModel):
    id: int
    rule_code: str
    violation_type: str
    rule_type: str
    params: str | None
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class ViolationRuleCreateIn(BaseModel):
    rule_code: str
    violation_type: str
    rule_type: str
    params: str | None = None
    description: str | None = None


class ViolationRuleUpdateIn(BaseModel):
    violation_type: str | None = None
    rule_type: str | None = None
    params: str | None = None
    description: str | None = None
    is_active: bool | None = None


class ViolationRuleListResponse(BaseModel):
    items: list[ViolationRuleOut]
    total: int
    page: int
    page_size: int
