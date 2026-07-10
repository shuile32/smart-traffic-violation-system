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

    def detect(self, image_path: str) -> DetectionResult:
        bundle = self._detector.detect(Path(image_path))
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
        from ai_service.traffic_ai.rules import IllegalStopRuleEvaluator

        self._evaluator = IllegalStopRuleEvaluator()

    def evaluate(
        self,
        detection: DetectionResult,
        ocr_result: str | None,
        intake_event: dict,
        rule: dict,
    ) -> RuleResult:
        bundle = _detection_result_to_bundle(detection)
        result = self._evaluator.evaluate(bundle, plate_text=ocr_result)
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
    return Path(settings.MEDIA_STORAGE_DIR) / "ai_outputs"


def _bundle_to_detection_result(bundle) -> DetectionResult:
    objects = []
    for group in (bundle.vehicle, bundle.license_plate, bundle.illegal_stop):
        objects.extend(item.to_dict() for item in group)

    return DetectionResult(
        objects=objects,
        vehicle_bbox=bundle.vehicle[0].bbox if bundle.vehicle else None,
        plate_bbox=bundle.license_plate[0].bbox if bundle.license_plate else None,
        annotated_image_path=_media_url_for_path(bundle.annotated_image_path),
        model_version="traffic-ai-local",
    )


def _detection_result_to_bundle(detection: DetectionResult):
    from ai_service.traffic_ai.schemas import Detection, DetectionBundle

    vehicle = []
    license_plate = []
    illegal_stop = []
    for item in detection.objects:
        parsed = Detection(
            label=str(item.get("label", "")),
            confidence=float(item.get("confidence", 0)),
            bbox=[int(value) for value in item.get("bbox", [])],
            model=str(item.get("model", "")),
        )
        if parsed.model == "vehicle" or parsed.label in {"bus", "cars", "truck", "van", "car"}:
            vehicle.append(parsed)
        elif parsed.model == "license" or parsed.label == "chinese-plate-license":
            license_plate.append(parsed)
        elif parsed.model == "illegal_stop" or parsed.label == "illegal":
            illegal_stop.append(parsed)

    return DetectionBundle(
        vehicle=vehicle,
        license_plate=license_plate,
        illegal_stop=illegal_stop,
        annotated_image_path=detection.annotated_image_path,
    )


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
