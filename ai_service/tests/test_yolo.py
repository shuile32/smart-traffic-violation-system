import unittest
from pathlib import Path
import tempfile

from PIL import Image

from ai_service.traffic_ai.schemas import Detection, DetectionBundle
from ai_service.traffic_ai.yolo import draw_annotated_image, detections_from_prediction


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


if __name__ == "__main__":
    unittest.main()
