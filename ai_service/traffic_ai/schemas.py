from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class Detection:
    label: str
    confidence: float
    bbox: list[int]
    model: str
    detection_id: str | None = None
    display_label: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class RedLightViolationEvidence:
    vehicle: Detection
    red_light: Detection
    zebra_crossing: Detection
    contact_bbox: list[int]
    intersection_bbox: list[int] | None
    overlap_ratio: float
    bottom_center_inside: bool
    confidence: float

    def to_dict(self) -> dict:
        return {
            "vehicle": self.vehicle.to_dict(),
            "red_light": self.red_light.to_dict(),
            "zebra_crossing": self.zebra_crossing.to_dict(),
            "contact_bbox": self.contact_bbox,
            "intersection_bbox": self.intersection_bbox,
            "overlap_ratio": self.overlap_ratio,
            "bottom_center_inside": self.bottom_center_inside,
            "confidence": self.confidence,
        }

    def to_object_dict(self) -> dict:
        return {
            "label": "suspected_red_light_violation",
            "confidence": self.confidence,
            "bbox": self.vehicle.bbox,
            "model": "red_light_rule",
            "evidence": self.to_dict(),
        }


@dataclass(frozen=True)
class ViolationTargetEvidence:
    violation_type: str
    vehicle: Detection
    confidence: float
    association_score: float
    evidence_bbox: list[int]
    evidence_model: str
    is_primary: bool = False

    def to_dict(self) -> dict:
        return {
            "violation_type": self.violation_type,
            "vehicle": self.vehicle.to_dict(),
            "confidence": self.confidence,
            "association_score": self.association_score,
            "evidence_bbox": self.evidence_bbox,
            "evidence_model": self.evidence_model,
            "is_primary": self.is_primary,
        }


@dataclass(frozen=True)
class DetectionBundle:
    vehicle: list[Detection] = field(default_factory=list)
    license_plate: list[Detection] = field(default_factory=list)
    illegal_stop: list[Detection] = field(default_factory=list)
    red_light: list[Detection] = field(default_factory=list)
    zebra_crossing: list[Detection] = field(default_factory=list)
    red_light_violation: list[RedLightViolationEvidence] = field(default_factory=list)
    annotated_image_path: str | None = None
    requested_violation_type: str | None = None
    violation_targets: list[ViolationTargetEvidence] = field(default_factory=list)
    primary_target: ViolationTargetEvidence | None = None

    def to_dict(self) -> dict:
        return {
            "vehicle": [item.to_dict() for item in self.vehicle],
            "license_plate": [item.to_dict() for item in self.license_plate],
            "illegal_stop": [item.to_dict() for item in self.illegal_stop],
            "red_light": [item.to_dict() for item in self.red_light],
            "zebra_crossing": [item.to_dict() for item in self.zebra_crossing],
            "red_light_violation": [item.to_dict() for item in self.red_light_violation],
            "annotated_image_path": self.annotated_image_path,
            "requested_violation_type": self.requested_violation_type,
            "violation_targets": [item.to_dict() for item in self.violation_targets],
            "primary_target": self.primary_target.to_dict() if self.primary_target else None,
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
