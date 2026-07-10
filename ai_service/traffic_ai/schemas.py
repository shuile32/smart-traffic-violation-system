from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class Detection:
    label: str
    confidence: float
    bbox: list[int]
    model: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class DetectionBundle:
    vehicle: list[Detection] = field(default_factory=list)
    license_plate: list[Detection] = field(default_factory=list)
    illegal_stop: list[Detection] = field(default_factory=list)
    annotated_image_path: str | None = None

    def to_dict(self) -> dict:
        return {
            "vehicle": [item.to_dict() for item in self.vehicle],
            "license_plate": [item.to_dict() for item in self.license_plate],
            "illegal_stop": [item.to_dict() for item in self.illegal_stop],
            "annotated_image_path": self.annotated_image_path,
        }


@dataclass(frozen=True)
class RuleResult:
    candidate_violation_type: str | None
    rule_code: str | None
    rule_matched: bool
    evidence_level: str
    evidence_items: list[str]
    missing_evidence: list[str]
    reason: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ReviewResult:
    conclusion: str
    confidence: float | None
    reason: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class PipelineResult:
    image_path: str
    detections: DetectionBundle
    plate_text: str | None
    ocr_engine: str
    ocr_status: str
    rule: RuleResult
    review: ReviewResult

    def to_dict(self) -> dict:
        return {
            "image_path": self.image_path,
            "detections": self.detections.to_dict(),
            "plate_text": self.plate_text,
            "ocr_engine": self.ocr_engine,
            "ocr_status": self.ocr_status,
            "rule": self.rule.to_dict(),
            "review": self.review.to_dict(),
        }
