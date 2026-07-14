import os
from pathlib import Path
import unittest
from unittest.mock import patch

from ai_service.traffic_ai.config import ModelPaths, RuntimePaths, ensure_runtime_environment, project_root
from ai_service.traffic_ai.ocr import (
    CHINESE_PLATE_PROVINCES,
    NoopOcrEngine,
    PaddleOcrEngine,
    create_default_ocr_engine,
    normalize_valid_plate_text,
    normalize_plate_text,
    plate_text_has_chinese_province,
)
from ai_service.traffic_ai.rules import IllegalStopRuleEvaluator, RedLightRuleEvaluator, TrafficRuleEvaluator
from ai_service.traffic_ai.schemas import (
    Detection,
    DetectionBundle,
    RedLightViolationEvidence,
    ViolationTargetEvidence,
)


class ConfigOcrRulesTest(unittest.TestCase):
    def test_model_paths_default_to_repo_models(self):
        paths = ModelPaths.default()

        self.assertEqual(paths.vehicle.name, "car_yolov8s.pt")
        self.assertEqual(paths.license_plate.name, "license.pt")
        self.assertEqual(paths.illegal_stop.name, "illegal_stop.pt")
        self.assertEqual(paths.red_light.name, "red_light.pt")
        self.assertEqual(paths.zebra_crossing.name, "zebra_crossing.pt")
        self.assertEqual(paths.vehicle.parent.name, "models")
        self.assertEqual(paths.vehicle.parent.parent.name, "ai_service")
        self.assertTrue(paths.vehicle.exists())

    def test_runtime_environment_points_ultralytics_to_project_dirs(self):
        runtime = RuntimePaths(root=Path.cwd() / ".tmp" / "unit-runtime")

        ensure_runtime_environment(runtime)

        self.assertTrue(Path(runtime.tmp_dir).exists())
        self.assertTrue(Path(runtime.yolo_config_dir).exists())
        self.assertTrue(Path(runtime.paddlex_cache_dir).exists())
        self.assertTrue(Path(runtime.matplotlib_config_dir).exists())

    def test_default_runtime_paths_stay_inside_repo_root(self):
        runtime = RuntimePaths.default()

        self.assertEqual(runtime.root, project_root())
        self.assertEqual(runtime.tmp_dir.parent, runtime.root)
        self.assertEqual(runtime.yolo_config_dir.parent, runtime.root)
        self.assertTrue(runtime.paddlex_cache_dir.name.endswith("paddlex"))
        self.assertEqual(runtime.matplotlib_config_dir.parent, runtime.root)

    def test_external_paddlex_cache_avoids_windows_temp_for_non_ascii_root(self):
        runtime = RuntimePaths(root=Path("C:/项目/smart-traffic"), use_external_paddlex_cache=True)

        if os.name == "nt":
            self.assertEqual(runtime.paddlex_cache_dir.drive, "C:")
            self.assertIn("tmp", runtime.paddlex_cache_dir.parts)
            self.assertNotIn("Temp", runtime.paddlex_cache_dir.parts)
        self.assertEqual(runtime.paddlex_cache_dir.name, "smart_traffic_violation_paddlex")

    def test_normalize_plate_text_removes_separators_and_uppercases_ascii(self):
        self.assertEqual(normalize_plate_text(" 粤 a-12345 "), "粤A12345")
        self.assertIsNone(normalize_plate_text(None))
        self.assertIsNone(normalize_plate_text("   "))

    def test_plate_text_has_chinese_province_prefix(self):
        self.assertIn("粤", CHINESE_PLATE_PROVINCES)
        self.assertTrue(plate_text_has_chinese_province("粤A12345"))
        self.assertTrue(plate_text_has_chinese_province("京B12345"))
        self.assertFalse(plate_text_has_chinese_province("XA12345"))

    def test_normalize_valid_plate_text_enforces_mainland_plate_format(self):
        self.assertEqual(normalize_valid_plate_text("贵A1CY81"), "贵A1CY81")
        self.assertEqual(normalize_valid_plate_text("粤BD12345"), "粤BD12345")
        self.assertEqual(normalize_valid_plate_text("贵AICY8I"), "贵A1CY81")
        self.assertIsNone(normalize_valid_plate_text("BLUCYAL"))
        self.assertIsNone(normalize_valid_plate_text("RAICY81"))
        self.assertIsNone(normalize_valid_plate_text("贵I12345"))
        self.assertIsNone(normalize_valid_plate_text("贵O12345"))

    def test_paddle_ocr_rejects_non_plate_text(self):
        from tempfile import TemporaryDirectory

        from PIL import Image

        with TemporaryDirectory() as directory:
            image_path = Path(directory) / "plate.png"
            Image.new("RGB", (80, 24), "blue").save(image_path)

            engine = object.__new__(PaddleOcrEngine)
            engine._ocr = type(
                "FakePaddleOcr",
                (),
                {"ocr": lambda self, _image: {"rec_texts": ["BLUCYAL"]}},
            )()

            result = engine.recognize(image_path)

        self.assertIsNone(result.text)
        self.assertEqual(result.status, "invalid_format")

    def test_noop_ocr_returns_none_with_unavailable_status(self):
        result = NoopOcrEngine().recognize(Path("plate.jpg"))

        self.assertIsNone(result.text)
        self.assertEqual(result.engine, "none")
        self.assertEqual(result.status, "unavailable")

    def test_default_ocr_engine_does_not_hide_cache_errors(self):
        with patch("ai_service.traffic_ai.ocr.PaddleOcrEngine", side_effect=PermissionError("cache denied")):
            with self.assertRaises(PermissionError):
                create_default_ocr_engine()

    def test_illegal_stop_rule_matches_illegal_detection(self):
        vehicle = Detection(label="cars", confidence=0.91, bbox=[1, 2, 30, 40], model="vehicle")
        target = ViolationTargetEvidence(
            violation_type="illegal_stop",
            vehicle=vehicle,
            confidence=0.86,
            association_score=0.9,
            evidence_bbox=[1, 2, 30, 40],
            evidence_model="illegal_stop",
            is_primary=True,
        )
        bundle = DetectionBundle(
            vehicle=[vehicle],
            license_plate=[],
            illegal_stop=[
                Detection(label="illegal", confidence=0.86, bbox=[1, 2, 30, 40], model="illegal_stop")
            ],
            requested_violation_type="illegal_stop",
            violation_targets=[target],
            primary_target=target,
        )

        result = IllegalStopRuleEvaluator().evaluate(bundle, plate_text="粤A12345")

        self.assertTrue(result.rule_matched)
        self.assertEqual(result.candidate_violation_type, "illegal_stop")
        self.assertEqual(result.evidence_level, "complete")
        self.assertIn("illegal_stop detection", result.evidence_items)

    def test_illegal_stop_rule_rejects_unassociated_illegal_box(self):
        bundle = DetectionBundle(
            vehicle=[Detection("cars", 0.91, [0, 0, 40, 40], "vehicle")],
            illegal_stop=[Detection("illegal", 0.86, [80, 80, 120, 120], "illegal_stop")],
            requested_violation_type="illegal_stop",
        )

        result = IllegalStopRuleEvaluator().evaluate(bundle, plate_text=None)

        self.assertFalse(result.rule_matched)
        self.assertIn("offending vehicle association", result.missing_evidence)

    def test_illegal_stop_rule_requires_illegal_detection(self):
        result = IllegalStopRuleEvaluator().evaluate(
            DetectionBundle(vehicle=[], license_plate=[], illegal_stop=[]),
            plate_text=None,
        )

        self.assertFalse(result.rule_matched)
        self.assertEqual(result.evidence_level, "insufficient")
        self.assertIn("illegal_stop detection", result.missing_evidence)

    def test_red_light_rule_requires_geometric_violation_evidence(self):
        vehicle = Detection(label="cars", confidence=0.91, bbox=[0, 0, 100, 100], model="vehicle")
        red = Detection(
            label="Traffic Light - Red",
            confidence=0.88,
            bbox=[120, 0, 140, 30],
            model="red_light",
        )
        crossing = Detection(
            label="zebra crossing",
            confidence=0.86,
            bbox=[0, 80, 100, 110],
            model="zebra_crossing",
        )
        evidence = RedLightViolationEvidence(
            vehicle=vehicle,
            red_light=red,
            zebra_crossing=crossing,
            contact_bbox=[15, 80, 85, 100],
            intersection_bbox=[15, 80, 85, 100],
            overlap_ratio=1.0,
            bottom_center_inside=True,
            confidence=0.86,
        )
        bundle = DetectionBundle(
            vehicle=[vehicle],
            license_plate=[],
            red_light=[red],
            zebra_crossing=[crossing],
            red_light_violation=[evidence],
        )

        result = RedLightRuleEvaluator().evaluate(bundle, plate_text="粤A12345")

        self.assertTrue(result.rule_matched)
        self.assertEqual(result.candidate_violation_type, "red_light_violation")
        self.assertEqual(result.rule_code, "red_light_zebra_overlap")
        self.assertEqual(result.evidence_level, "complete")
        self.assertIn("vehicle-crossing contact", result.evidence_items)

    def test_red_light_rule_does_not_match_detection_boxes_without_contact_evidence(self):
        result = RedLightRuleEvaluator().evaluate(
            DetectionBundle(
                vehicle=[Detection("cars", 0.9, [0, 0, 100, 100], "vehicle")],
                red_light=[Detection("Traffic Light - Red", 0.9, [110, 0, 130, 30], "red_light")],
                zebra_crossing=[Detection("zebra crossing", 0.9, [0, 80, 100, 110], "zebra_crossing")],
            ),
            plate_text=None,
        )

        self.assertFalse(result.rule_matched)
        self.assertIn("vehicle-crossing contact", result.missing_evidence)

    def test_aggregate_rule_prioritizes_red_light_violation(self):
        vehicle = Detection("cars", 0.91, [0, 0, 100, 100], "vehicle")
        red = Detection("Traffic Light - Red", 0.88, [120, 0, 140, 30], "red_light")
        crossing = Detection("zebra crossing", 0.86, [0, 80, 100, 110], "zebra_crossing")
        evidence = RedLightViolationEvidence(
            vehicle=vehicle,
            red_light=red,
            zebra_crossing=crossing,
            contact_bbox=[15, 80, 85, 100],
            intersection_bbox=[15, 80, 85, 100],
            overlap_ratio=1.0,
            bottom_center_inside=True,
            confidence=0.86,
        )
        bundle = DetectionBundle(
            vehicle=[vehicle],
            illegal_stop=[Detection("illegal", 0.8, [0, 0, 100, 100], "illegal_stop")],
            red_light=[red],
            zebra_crossing=[crossing],
            red_light_violation=[evidence],
        )

        result = TrafficRuleEvaluator().evaluate(bundle, plate_text=None)

        self.assertEqual(result.candidate_violation_type, "red_light_violation")


if __name__ == "__main__":
    unittest.main()
