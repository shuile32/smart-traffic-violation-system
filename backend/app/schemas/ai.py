from pydantic import BaseModel


class DetectionOut(BaseModel):
    objects: list[dict]
    vehicle_bbox: list[int] | None
    plate_bbox: list[int] | None
    annotated_image_url: str | None
    model_version: str


class OcrOut(BaseModel):
    plate_no: str | None


class RuleEvalOut(BaseModel):
    rule_matched: bool
    evidence_level: str
    evidence_items: list[str]
    reason: str


class ReviewOut(BaseModel):
    conclusion: str
    ai_confidence: float | None
    reason: str
