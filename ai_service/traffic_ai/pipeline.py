from __future__ import annotations

from pathlib import Path
from typing import Protocol

from PIL import Image

from ai_service.traffic_ai.ocr import OcrEngine, OcrResult, create_default_ocr_engine
from ai_service.traffic_ai.rules import IllegalStopRuleEvaluator, review_from_rule
from ai_service.traffic_ai.schemas import Detection, DetectionBundle, PipelineResult


class Detector(Protocol):
    def detect(self, image_path: Path) -> DetectionBundle:
        raise NotImplementedError


class TrafficViolationPipeline:
    def __init__(
        self,
        detector: Detector,
        ocr_engine: OcrEngine | None = None,
        rule_evaluator: IllegalStopRuleEvaluator | None = None,
    ) -> None:
        self.detector = detector
        self.ocr_engine = ocr_engine or create_default_ocr_engine()
        self.rule_evaluator = rule_evaluator or IllegalStopRuleEvaluator()

    def analyze(self, image_path: Path | str) -> PipelineResult:
        path = Path(image_path)
        detections = self.detector.detect(path)
        ocr = self._recognize_plate_after_violation(path, detections)
        rule = self.rule_evaluator.evaluate(detections, plate_text=ocr.text)
        review = review_from_rule(rule)
        return PipelineResult(
            image_path=str(path),
            detections=detections,
            plate_text=ocr.text,
            ocr_engine=ocr.engine,
            ocr_status=ocr.status,
            rule=rule,
            review=review,
        )

    def _recognize_plate_after_violation(self, image_path: Path, detections: DetectionBundle) -> OcrResult:
        if not detections.illegal_stop:
            return OcrResult(text=None, engine="none", status="skipped_no_violation")
        if not detections.license_plate:
            return OcrResult(text=None, engine="none", status="skipped_no_plate")
        crop_path = crop_plate_image(image_path, detections.license_plate[0])
        return self.ocr_engine.recognize(crop_path)


def crop_plate_image(image_path: Path, plate_detection: Detection) -> Path:
    output_path = image_path.with_name("plate_crop.jpg")
    with Image.open(image_path) as image:
        width, height = image.size
        x1, y1, x2, y2 = plate_detection.bbox
        left = max(0, min(width, x1))
        upper = max(0, min(height, y1))
        right = max(left + 1, min(width, x2))
        lower = max(upper + 1, min(height, y2))
        image.crop((left, upper, right, lower)).save(output_path)
    return output_path
