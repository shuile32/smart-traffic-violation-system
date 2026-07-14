"""Local AI adapters that call the repository algorithm package."""
from __future__ import annotations

import sys
from pathlib import Path

from app.ai.adapters.base import DetectionResult, OcrEngine, RuleEvaluator, RuleResult, YoloDetector
from app.core.config import settings

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


class LocalYoloDetector(YoloDetector):
    def __init__(self, output_dir: Path | None = None) -> None:
        from ai_service.traffic_ai.yolo import UltralyticsTrafficDetector

        self._output_dir = output_dir or _default_ai_output_dir()
        self._detector = UltralyticsTrafficDetector(output_dir=self._output_dir)

    def detect(
        self,
        image_path: str,
        requested_violation_type: str | None = None,
    ) -> DetectionResult:
        bundle = self._detector.detect(Path(image_path), requested_violation_type)
        return _bundle_to_detection_result(bundle)


class LocalOcrEngine(OcrEngine):
    def __init__(self, engine=None) -> None:
        self._engine = engine

    def recognize_plate(self, plate_crop_path: str) -> str | None:
        return self._get_engine().recognize(Path(plate_crop_path)).text

    def _get_engine(self):
        if self._engine is None:
            from ai_service.traffic_ai.ocr import create_default_ocr_engine

            self._engine = create_default_ocr_engine()
        return self._engine


class LocalRuleEvaluator(RuleEvaluator):
    def __init__(self) -> None:
        from ai_service.traffic_ai.rules import TrafficRuleEvaluator

        self._evaluator = TrafficRuleEvaluator()

    def evaluate(
        self,
        detection: DetectionResult,
        ocr_result: str | None,
        intake_event: dict,
        rule: dict,
    ) -> RuleResult:
        bundle = _detection_result_to_bundle(detection)
        requested_rule = rule.get("type")
        if requested_rule == "auto":
            requested_rule = None
        result = self._evaluator.evaluate(
            bundle,
            plate_text=ocr_result,
            requested_rule=requested_rule,
        )
        return RuleResult(
            candidate_violation_type=result.candidate_violation_type,
            rule_code=result.rule_code,
            rule_matched=result.rule_matched,
            evidence_level=result.evidence_level,
            evidence_items=result.evidence_items,
            missing_evidence=result.missing_evidence,
            reason=result.reason,
        )


def _default_ai_output_dir() -> Path:
    return Path(settings.MEDIA_STORAGE_DIR)


def _bundle_to_detection_result(bundle) -> DetectionResult:
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
        else (bundle.vehicle[0].bbox if bundle.vehicle else None)
    )
    return DetectionResult(
        objects=objects,
        vehicle_bbox=primary_vehicle_bbox,
        plate_bbox=bundle.license_plate[0].bbox if bundle.license_plate else None,
        annotated_image_path=_media_url_for_path(bundle.annotated_image_path),
        model_version="traffic-ai-local",
        requested_violation_type=bundle.requested_violation_type,
        violation_targets=[item.to_dict() for item in bundle.violation_targets],
        primary_target=bundle.primary_target.to_dict() if bundle.primary_target else None,
    )


def _detection_result_to_bundle(detection: DetectionResult):
    from ai_service.traffic_ai.schemas import DetectionBundle

    vehicle = []
    license_plate = []
    illegal_stop = []
    red_light = []
    zebra_crossing = []
    red_light_violation = []
    for item in detection.objects:
        if item.get("model") == "red_light_rule":
            parsed_evidence = _red_light_evidence_from_dict(item.get("evidence"))
            if parsed_evidence is not None:
                red_light_violation.append(parsed_evidence)
            continue
        parsed = _detection_from_dict(item)
        if parsed.model == "vehicle" or parsed.label in {"bus", "cars", "truck", "van", "car"}:
            vehicle.append(parsed)
        elif parsed.model == "license" or parsed.label == "chinese-plate-license":
            license_plate.append(parsed)
        elif parsed.model == "illegal_stop" or parsed.label == "illegal":
            illegal_stop.append(parsed)
        elif parsed.model == "red_light":
            red_light.append(parsed)
        elif parsed.model == "zebra_crossing" or parsed.label == "zebra crossing":
            zebra_crossing.append(parsed)

    violation_targets = []
    for item in detection.violation_targets:
        parsed_target = _violation_target_from_dict(item)
        if parsed_target is not None:
            violation_targets.append(parsed_target)
    primary_target = _violation_target_from_dict(detection.primary_target)

    return DetectionBundle(
        vehicle=vehicle,
        license_plate=license_plate,
        illegal_stop=illegal_stop,
        red_light=red_light,
        zebra_crossing=zebra_crossing,
        red_light_violation=red_light_violation,
        annotated_image_path=detection.annotated_image_path,
        requested_violation_type=detection.requested_violation_type,
        violation_targets=violation_targets,
        primary_target=primary_target,
    )


def _detection_from_dict(item: dict):
    from ai_service.traffic_ai.schemas import Detection

    return Detection(
        label=str(item.get("label", "")),
        confidence=float(item.get("confidence", 0)),
        bbox=[int(value) for value in item.get("bbox", [])],
        model=str(item.get("model", "")),
        detection_id=str(item["detection_id"]) if item.get("detection_id") else None,
        display_label=str(item["display_label"]) if item.get("display_label") else None,
    )


def _violation_target_from_dict(data: dict | None):
    from ai_service.traffic_ai.schemas import ViolationTargetEvidence

    if not isinstance(data, dict):
        return None
    try:
        return ViolationTargetEvidence(
            violation_type=str(data["violation_type"]),
            vehicle=_detection_from_dict(data["vehicle"]),
            confidence=float(data["confidence"]),
            association_score=float(data["association_score"]),
            evidence_bbox=[int(value) for value in data["evidence_bbox"]],
            evidence_model=str(data["evidence_model"]),
            is_primary=bool(data.get("is_primary", False)),
        )
    except (KeyError, TypeError, ValueError):
        return None


def _red_light_evidence_from_dict(data: dict | None):
    from ai_service.traffic_ai.schemas import RedLightViolationEvidence

    if not isinstance(data, dict):
        return None
    try:
        intersection = data.get("intersection_bbox")
        return RedLightViolationEvidence(
            vehicle=_detection_from_dict(data["vehicle"]),
            red_light=_detection_from_dict(data["red_light"]),
            zebra_crossing=_detection_from_dict(data["zebra_crossing"]),
            contact_bbox=[int(value) for value in data["contact_bbox"]],
            intersection_bbox=[int(value) for value in intersection] if intersection else None,
            overlap_ratio=float(data["overlap_ratio"]),
            bottom_center_inside=bool(data["bottom_center_inside"]),
            confidence=float(data["confidence"]),
        )
    except (KeyError, TypeError, ValueError):
        return None


def _media_url_for_path(path_value: str | None) -> str | None:
    if not path_value:
        return None

    path = Path(path_value).resolve()
    media_root = Path(settings.MEDIA_STORAGE_DIR).resolve()
    try:
        relative = path.relative_to(media_root)
    except ValueError:
        return str(path)
    return "/media/" + relative.as_posix()
