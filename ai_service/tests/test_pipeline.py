from pathlib import Path
import tempfile
import unittest

from PIL import Image

from ai_service.traffic_ai.ocr import OcrResult
from ai_service.traffic_ai.pipeline import TrafficViolationPipeline
from ai_service.traffic_ai.schemas import Detection, DetectionBundle


class FakeDetector:
    def detect(self, image_path: Path) -> DetectionBundle:
        return DetectionBundle(
            vehicle=[Detection(label="cars", confidence=0.9, bbox=[0, 0, 10, 10], model="vehicle")],
            license_plate=[
                Detection(label="chinese-plate-license", confidence=0.8, bbox=[1, 1, 8, 4], model="license")
            ],
            illegal_stop=[Detection(label="illegal", confidence=0.7, bbox=[0, 0, 10, 10], model="illegal_stop")],
        )


class NoViolationDetector:
    def detect(self, image_path: Path) -> DetectionBundle:
        return DetectionBundle(
            vehicle=[Detection(label="cars", confidence=0.9, bbox=[0, 0, 10, 10], model="vehicle")],
            license_plate=[],
            illegal_stop=[],
        )


class FakeOcr:
    def __init__(self) -> None:
        self.seen_paths: list[Path] = []

    def recognize(self, image_path: Path) -> OcrResult:
        self.seen_paths.append(image_path)
        return OcrResult(text="粤A12345", engine="fake", status="ok")


class PipelineTest(unittest.TestCase):
    def test_pipeline_crops_plate_and_runs_ocr_only_after_violation(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "frame.jpg"
            Image.new("RGB", (20, 20), "white").save(image)
            ocr = FakeOcr()

            result = TrafficViolationPipeline(detector=FakeDetector(), ocr_engine=ocr).analyze(image)

        self.assertEqual(Path(result.image_path).name, "frame.jpg")
        self.assertEqual(result.plate_text, "粤A12345")
        self.assertTrue(result.rule.rule_matched)
        self.assertEqual(result.review.conclusion, "suggest_approve")
        self.assertEqual(result.detections.illegal_stop[0].label, "illegal")
        self.assertEqual(len(ocr.seen_paths), 1)
        self.assertEqual(ocr.seen_paths[0].name, "plate_crop.jpg")

    def test_pipeline_result_is_json_friendly(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "frame.jpg"
            Image.new("RGB", (20, 20), "white").save(image)
            result = TrafficViolationPipeline(detector=FakeDetector(), ocr_engine=FakeOcr()).analyze(image)

        payload = result.to_dict()

        self.assertEqual(payload["plate_text"], "粤A12345")
        self.assertEqual(payload["rule"]["candidate_violation_type"], "illegal_stop")
        self.assertEqual(payload["detections"]["vehicle"][0]["bbox"], [0, 0, 10, 10])

    def test_pipeline_skips_plate_detection_and_ocr_when_no_violation(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "frame.jpg"
            Image.new("RGB", (20, 20), "white").save(image)
            ocr = FakeOcr()

            result = TrafficViolationPipeline(detector=NoViolationDetector(), ocr_engine=ocr).analyze(image)

        self.assertIsNone(result.plate_text)
        self.assertEqual(result.ocr_status, "skipped_no_violation")
        self.assertEqual(ocr.seen_paths, [])


if __name__ == "__main__":
    unittest.main()
