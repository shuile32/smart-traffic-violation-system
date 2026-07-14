import unittest
from pathlib import Path
import tempfile
from unittest.mock import patch

from PIL import Image

from ai_service.traffic_ai.red_light import find_red_light_violations
from ai_service.traffic_ai.schemas import Detection, DetectionBundle, ViolationTargetEvidence
from ai_service.traffic_ai.yolo import (
    UltralyticsTrafficDetector,
    assign_vehicle_ids,
    draw_annotated_image,
    detections_from_prediction,
    prioritize_plate_detections,
)


class FakeBoxes:
    cls = [0, 1]
    conf = [0.91, 0.55]

    class XYXY:
        def tolist(self):
            return [[1.2, 2.6, 10.1, 20.9], [3, 4, 5, 6]]

    xyxy = XYXY()


class FakePrediction:
    names = {0: "cars", 1: "bus"}
    boxes = FakeBoxes()


class YoloTest(unittest.TestCase):
    def test_assign_vehicle_ids_is_stable_and_numbers_same_class(self):
        vehicles = [
            Detection("cars", 0.92, [60, 10, 100, 60], "vehicle"),
            Detection("truck", 0.88, [5, 70, 55, 120], "vehicle"),
            Detection("cars", 0.90, [10, 10, 50, 60], "vehicle"),
        ]

        numbered = assign_vehicle_ids(vehicles)

        self.assertEqual([item.detection_id for item in numbered], ["vehicle-1", "vehicle-2", "vehicle-3"])
        self.assertEqual([item.display_label for item in numbered], ["小汽车1", "小汽车2", "卡车1"])
        self.assertEqual([item.bbox for item in numbered], [[10, 10, 50, 60], [60, 10, 100, 60], [5, 70, 55, 120]])

    def test_detections_from_prediction_normalizes_boxes_and_labels(self):
        detections = detections_from_prediction(FakePrediction(), model_name="vehicle", min_confidence=0.6)

        self.assertEqual(len(detections), 1)
        self.assertEqual(detections[0].label, "cars")
        self.assertEqual(detections[0].bbox, [1, 3, 10, 21])
        self.assertEqual(detections[0].confidence, 0.91)
        self.assertEqual(detections[0].model, "vehicle")

    def test_draw_annotated_image_writes_boxed_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.jpg"
            output = Path(tmp) / "annotated.jpg"
            Image.new("RGB", (40, 40), "white").save(source)
            bundle = DetectionBundle(
                vehicle=[Detection(label="cars", confidence=0.9, bbox=[1, 1, 20, 20], model="vehicle")],
                license_plate=[
                    Detection(label="chinese-plate-license", confidence=0.8, bbox=[5, 5, 18, 12], model="license")
                ],
                illegal_stop=[Detection(label="illegal", confidence=0.7, bbox=[2, 2, 25, 25], model="illegal_stop")],
            )

            result = draw_annotated_image(source, bundle, output)

            self.assertEqual(result, output)
            self.assertTrue(output.exists())

    def test_draw_annotated_image_highlights_primary_vehicle(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.png"
            output = Path(tmp) / "annotated.png"
            Image.new("RGB", (60, 40), "white").save(source)
            primary_vehicle = Detection(
                "cars", 0.9, [2, 2, 22, 30], "vehicle", "vehicle-1", "小汽车1"
            )
            other_vehicle = Detection(
                "cars", 0.8, [32, 2, 55, 30], "vehicle", "vehicle-2", "小汽车2"
            )
            primary_target = ViolationTargetEvidence(
                violation_type="illegal_stop",
                vehicle=primary_vehicle,
                confidence=0.9,
                association_score=0.95,
                evidence_bbox=[2, 2, 22, 30],
                evidence_model="illegal_stop",
                is_primary=True,
            )
            bundle = DetectionBundle(
                vehicle=[primary_vehicle, other_vehicle],
                violation_targets=[primary_target],
                primary_target=primary_target,
                requested_violation_type="illegal_stop",
            )

            draw_annotated_image(source, bundle, output)

            with Image.open(output) as annotated:
                self.assertEqual(annotated.getpixel((2, 2)), (255, 0, 0))
                self.assertEqual(annotated.getpixel((32, 2)), (0, 255, 0))

    def test_detector_runs_only_illegal_stop_workflow_and_uses_primary_vehicle_plate(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.jpg"
            Image.new("RGB", (180, 120), "white").save(source)
            detector = UltralyticsTrafficDetector(output_dir=Path(tmp) / "outputs")
            predictions = {
                "vehicle": [
                    Detection("cars", 0.92, [10, 10, 80, 90], "vehicle"),
                    Detection("cars", 0.90, [100, 10, 170, 90], "vehicle"),
                ],
                "illegal_stop": [
                    Detection("illegal", 0.80, [8, 8, 82, 92], "illegal_stop"),
                    Detection("illegal", 0.95, [95, 5, 175, 95], "illegal_stop"),
                ],
                "license": [
                    Detection("chinese-plate-license", 0.99, [20, 60, 50, 75], "license"),
                    Detection("chinese-plate-license", 0.70, [115, 60, 145, 75], "license"),
                ],
            }

            with patch.object(
                detector,
                "_predict",
                side_effect=lambda key, _path, _image: predictions[key],
            ) as predict:
                result = detector.detect(source, "illegal_stop")

        self.assertEqual([call.args[0] for call in predict.call_args_list], ["vehicle", "illegal_stop", "license"])
        self.assertEqual(result.requested_violation_type, "illegal_stop")
        self.assertEqual(result.red_light, [])
        self.assertEqual(result.zebra_crossing, [])
        self.assertEqual(result.primary_target.vehicle.display_label, "小汽车2")
        self.assertTrue(result.primary_target.is_primary)
        self.assertEqual([item.bbox for item in result.license_plate], [[115, 60, 145, 75]])

    def test_detector_runs_plate_model_after_red_light_violation(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.jpg"
            Image.new("RGB", (180, 140), "white").save(source)
            detector = UltralyticsTrafficDetector(output_dir=Path(tmp) / "outputs")
            predictions = {
                "vehicle": [Detection("cars", 0.91, [10, 10, 110, 110], "vehicle")],
                "illegal_stop": [],
                "red_light": [Detection("Traffic Light - Red", 0.88, [130, 5, 155, 35], "red_light")],
                "zebra_crossing": [
                    Detection("zebra crossing", 0.86, [0, 90, 130, 130], "zebra_crossing")
                ],
                "license": [
                    Detection("chinese-plate-license", 0.81, [40, 60, 75, 75], "license")
                ],
            }

            with patch.object(
                detector,
                "_predict",
                side_effect=lambda key, _path, _image: predictions[key],
            ) as predict:
                result = detector.detect(source, "red_light_violation")

        self.assertEqual(len(result.red_light_violation), 1)
        self.assertEqual(result.license_plate[0].bbox, [40, 60, 75, 75])
        self.assertEqual(
            [call.args[0] for call in predict.call_args_list],
            ["vehicle", "red_light", "zebra_crossing", "license"],
        )
        self.assertEqual(result.requested_violation_type, "red_light_violation")
        self.assertEqual(result.illegal_stop, [])
        self.assertEqual(result.primary_target.violation_type, "red_light_violation")
        self.assertIsNotNone(result.annotated_image_path)

    def test_detector_skips_plate_model_without_any_violation(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.jpg"
            Image.new("RGB", (180, 140), "white").save(source)
            detector = UltralyticsTrafficDetector(output_dir=Path(tmp) / "outputs")
            predictions = {
                "vehicle": [Detection("cars", 0.91, [10, 10, 110, 110], "vehicle")],
                "illegal_stop": [],
                "red_light": [Detection("Traffic Lioght - Green", 0.88, [130, 5, 155, 35], "red_light")],
                "zebra_crossing": [
                    Detection("zebra crossing", 0.86, [0, 90, 130, 130], "zebra_crossing")
                ],
            }

            with patch.object(
                detector,
                "_predict",
                side_effect=lambda key, _path, _image: predictions[key],
            ) as predict:
                result = detector.detect(source, "red_light_violation")

        self.assertEqual(result.red_light_violation, [])
        self.assertEqual(result.license_plate, [])
        self.assertNotIn("license", [call.args[0] for call in predict.call_args_list])

    def test_plate_inside_offending_vehicle_is_prioritized(self):
        vehicle = Detection("cars", 0.91, [10, 10, 110, 110], "vehicle")
        evidence = find_red_light_violations(
            [vehicle],
            [Detection("Traffic Light - Red", 0.88, [130, 5, 155, 35], "red_light")],
            [Detection("zebra crossing", 0.86, [0, 90, 130, 130], "zebra_crossing")],
        )
        outside = Detection("chinese-plate-license", 0.95, [130, 60, 170, 80], "license")
        inside = Detection("chinese-plate-license", 0.75, [40, 60, 75, 75], "license")

        ordered = prioritize_plate_detections([outside, inside], evidence)

        self.assertEqual(ordered, [inside, outside])


if __name__ == "__main__":
    unittest.main()
