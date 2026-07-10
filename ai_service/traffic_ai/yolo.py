from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from ai_service.traffic_ai.config import ModelPaths, ensure_runtime_environment
from ai_service.traffic_ai.schemas import Detection, DetectionBundle


def _as_list(value: Any) -> list:
    if hasattr(value, "tolist"):
        return value.tolist()
    return list(value)


def detections_from_prediction(prediction: Any, model_name: str, min_confidence: float) -> list[Detection]:
    boxes = getattr(prediction, "boxes", None)
    if boxes is None:
        return []

    names = getattr(prediction, "names", {})
    class_ids = _as_list(boxes.cls)
    confidences = _as_list(boxes.conf)
    coordinates = _as_list(boxes.xyxy)

    detections: list[Detection] = []
    for class_id, confidence, bbox in zip(class_ids, confidences, coordinates, strict=False):
        confidence_float = round(float(confidence), 4)
        if confidence_float < min_confidence:
            continue
        label = names.get(int(class_id), str(int(class_id)))
        detections.append(
            Detection(
                label=label,
                confidence=confidence_float,
                bbox=[round(float(value)) for value in bbox],
                model=model_name,
            )
        )
    return detections


class UltralyticsTrafficDetector:
    def __init__(
        self,
        model_paths: ModelPaths | None = None,
        min_confidence: float = 0.25,
        output_dir: Path | None = None,
    ) -> None:
        ensure_runtime_environment(include_paddlex=False)
        self.model_paths = model_paths or ModelPaths.default()
        self.min_confidence = min_confidence
        self.output_dir = output_dir or Path(__file__).resolve().parents[1] / "outputs"
        self._models: dict[str, Any] = {}

    def _load_model(self, key: str, path: Path) -> Any:
        if key not in self._models:
            from ultralytics import YOLO

            self._models[key] = YOLO(str(path))
        return self._models[key]

    def _predict(self, key: str, path: Path, image_path: Path) -> list[Detection]:
        model = self._load_model(key, path)
        result = model(str(image_path), verbose=False)[0]
        return detections_from_prediction(result, key, self.min_confidence)

    def detect(self, image_path: Path | str) -> DetectionBundle:
        path = Path(image_path)
        vehicle = self._predict("vehicle", self.model_paths.vehicle, path)
        illegal_stop = self._predict("illegal_stop", self.model_paths.illegal_stop, path)
        license_plate = self._predict("license", self.model_paths.license_plate, path) if illegal_stop else []
        bundle = DetectionBundle(
            vehicle=vehicle,
            license_plate=license_plate,
            illegal_stop=illegal_stop,
        )
        annotated = None
        if vehicle or license_plate or illegal_stop:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            annotated = draw_annotated_image(path, bundle, self.output_dir / f"{path.stem}-{uuid4().hex}.jpg")
        return DetectionBundle(
            vehicle=vehicle,
            license_plate=license_plate,
            illegal_stop=illegal_stop,
            annotated_image_path=str(annotated) if annotated else None,
        )


def draw_annotated_image(image_path: Path, bundle: DetectionBundle, output_path: Path) -> Path:
    from PIL import Image, ImageDraw

    colors = {
        "vehicle": "lime",
        "license": "yellow",
        "illegal_stop": "red",
    }
    with Image.open(image_path) as image:
        canvas = image.convert("RGB")
        draw = ImageDraw.Draw(canvas)
        for group in (bundle.vehicle, bundle.license_plate, bundle.illegal_stop):
            for item in group:
                color = colors.get(item.model, "cyan")
                draw.rectangle(item.bbox, outline=color, width=3)
                label = f"{item.label} {item.confidence:.2f}"
                draw.text((item.bbox[0], max(0, item.bbox[1] - 12)), label, fill=color)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(output_path)
    return output_path
