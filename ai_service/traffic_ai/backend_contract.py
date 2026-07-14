from __future__ import annotations

from ai_service.traffic_ai.schemas import DetectionBundle, ReviewResult, RuleResult


def _first_bbox(items) -> list[int] | None:
    return items[0].bbox if items else None


def detection_bundle_to_backend_dict(bundle: DetectionBundle) -> dict:
    objects = []
    for group in (
        bundle.vehicle,
        bundle.license_plate,
        bundle.illegal_stop,
        bundle.red_light,
        bundle.zebra_crossing,
    ):
        objects.extend(item.to_dict() for item in group)
    objects.extend(item.to_object_dict() for item in bundle.red_light_violation)
    primary_vehicle_bbox = (
        bundle.primary_target.vehicle.bbox
        if bundle.primary_target is not None
        else _first_bbox(bundle.vehicle)
    )
    return {
        "objects": objects,
        "vehicle_bbox": primary_vehicle_bbox,
        "plate_bbox": _first_bbox(bundle.license_plate),
        "annotated_image_url": bundle.annotated_image_path,
        "model_version": "traffic-ai-local",
    }


def rule_result_to_backend_dict(rule: RuleResult) -> dict:
    return {
        "rule_matched": rule.rule_matched,
        "evidence_level": rule.evidence_level,
        "evidence_items": rule.evidence_items,
        "reason": rule.reason,
    }


def review_result_to_backend_dict(review: ReviewResult) -> dict:
    return {
        "conclusion": review.conclusion,
        "ai_confidence": review.confidence,
        "reason": review.reason,
    }
