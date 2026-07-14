from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any
from uuid import uuid4

from ai_service.traffic_ai.config import ModelPaths, ensure_runtime_environment
from ai_service.traffic_ai.red_light import find_red_light_violations
from ai_service.traffic_ai.schemas import (
    Detection,
    DetectionBundle,
    RedLightViolationEvidence,
    ViolationTargetEvidence,
)


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


_VEHICLE_DISPLAY_NAMES = {
    "car": "小汽车",
    "cars": "小汽车",
    "bus": "公交车",
    "truck": "卡车",
    "van": "面包车",
}


def assign_vehicle_ids(vehicles: list[Detection]) -> list[Detection]:
    ordered = sorted(vehicles, key=lambda item: (item.bbox[1], item.bbox[0], item.bbox[3], item.bbox[2]))
    class_counts: dict[str, int] = {}
    numbered: list[Detection] = []
    for index, vehicle in enumerate(ordered, start=1):
        display_name = _VEHICLE_DISPLAY_NAMES.get(vehicle.label.strip().casefold(), "车辆")
        class_counts[display_name] = class_counts.get(display_name, 0) + 1
        numbered.append(
            replace(
                vehicle,
                detection_id=f"vehicle-{index}",
                display_label=f"{display_name}{class_counts[display_name]}",
            )
        )
    return numbered


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

    def detect(
        self,
        image_path: Path | str,
        requested_violation_type: str | None = None,
    ) -> DetectionBundle:
        if requested_violation_type not in {None, "illegal_stop", "red_light_violation"}:
            raise ValueError(f"Unsupported violation type: {requested_violation_type}")

        path = Path(image_path)
        vehicle = assign_vehicle_ids(self._predict("vehicle", self.model_paths.vehicle, path))
        illegal_stop = (
            self._predict("illegal_stop", self.model_paths.illegal_stop, path)
            if requested_violation_type in {None, "illegal_stop"}
            else []
        )
        red_light = (
            self._predict("red_light", self.model_paths.red_light, path)
            if requested_violation_type in {None, "red_light_violation"}
            else []
        )
        zebra_crossing = (
            self._predict("zebra_crossing", self.model_paths.zebra_crossing, path)
            if requested_violation_type in {None, "red_light_violation"}
            else []
        )
        red_light_violation = find_red_light_violations(vehicle, red_light, zebra_crossing)
        illegal_targets = build_illegal_stop_targets(vehicle, illegal_stop)
        red_light_targets = build_red_light_targets(red_light_violation)
        if requested_violation_type == "illegal_stop":
            violation_targets = illegal_targets
        elif requested_violation_type == "red_light_violation":
            violation_targets = red_light_targets
        else:
            violation_targets = red_light_targets or illegal_targets
        violation_targets, primary_target = select_primary_target(violation_targets)
        raw_plates = (
            self._predict("license", self.model_paths.license_plate, path)
            if primary_target is not None
            else []
        )
        license_plate = match_plate_to_primary_vehicle(raw_plates, primary_target)
        bundle = DetectionBundle(
            vehicle=vehicle,
            license_plate=license_plate,
            illegal_stop=illegal_stop,
            red_light=red_light,
            zebra_crossing=zebra_crossing,
            red_light_violation=red_light_violation,
            requested_violation_type=requested_violation_type,
            violation_targets=violation_targets,
            primary_target=primary_target,
        )
        annotated = None
        if vehicle or license_plate or illegal_stop or red_light or zebra_crossing:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            annotated = draw_annotated_image(path, bundle, self.output_dir / f"{path.stem}-{uuid4().hex}.jpg")
        return DetectionBundle(
            vehicle=vehicle,
            license_plate=license_plate,
            illegal_stop=illegal_stop,
            red_light=red_light,
            zebra_crossing=zebra_crossing,
            red_light_violation=red_light_violation,
            annotated_image_path=str(annotated) if annotated else None,
            requested_violation_type=requested_violation_type,
            violation_targets=violation_targets,
            primary_target=primary_target,
        )


def build_illegal_stop_targets(
    vehicles: list[Detection],
    illegal_stops: list[Detection],
) -> list[ViolationTargetEvidence]:
    best_by_vehicle: dict[str, ViolationTargetEvidence] = {}
    for illegal_stop in illegal_stops:
        candidates = [(_box_association_score(vehicle.bbox, illegal_stop.bbox), vehicle) for vehicle in vehicles]
        if not candidates:
            continue
        association_score, vehicle = max(candidates, key=lambda item: item[0])
        if association_score <= 0:
            continue
        target = ViolationTargetEvidence(
            violation_type="illegal_stop",
            vehicle=vehicle,
            confidence=round(min(vehicle.confidence, illegal_stop.confidence), 4),
            association_score=round(association_score, 4),
            evidence_bbox=illegal_stop.bbox,
            evidence_model="illegal_stop",
        )
        key = vehicle.detection_id or str(vehicle.bbox)
        previous = best_by_vehicle.get(key)
        if previous is None or (target.confidence, target.association_score) > (
            previous.confidence,
            previous.association_score,
        ):
            best_by_vehicle[key] = target
    return list(best_by_vehicle.values())


def build_red_light_targets(
    violations: list[RedLightViolationEvidence],
) -> list[ViolationTargetEvidence]:
    return [
        ViolationTargetEvidence(
            violation_type="red_light_violation",
            vehicle=evidence.vehicle,
            confidence=evidence.confidence,
            association_score=round(
                max(evidence.overlap_ratio, 1.0 if evidence.bottom_center_inside else 0.0),
                4,
            ),
            evidence_bbox=evidence.intersection_bbox or evidence.contact_bbox,
            evidence_model="red_light_rule",
        )
        for evidence in violations
    ]


def select_primary_target(
    targets: list[ViolationTargetEvidence],
) -> tuple[list[ViolationTargetEvidence], ViolationTargetEvidence | None]:
    if not targets:
        return [], None
    primary_index = max(
        range(len(targets)),
        key=lambda index: (targets[index].confidence, targets[index].association_score),
    )
    marked = [replace(item, is_primary=index == primary_index) for index, item in enumerate(targets)]
    return marked, marked[primary_index]


def match_plate_to_primary_vehicle(
    plates: list[Detection],
    primary_target: ViolationTargetEvidence | None,
) -> list[Detection]:
    if primary_target is None:
        return []
    candidates = [
        plate for plate in plates if _box_center_inside(plate.bbox, primary_target.vehicle.bbox)
    ]
    if not candidates:
        return []
    matched = max(candidates, key=lambda item: item.confidence)
    vehicle_name = primary_target.vehicle.display_label or "违法车辆"
    return [replace(matched, detection_id="plate-1", display_label=f"{vehicle_name}车牌")]


def _box_association_score(first_bbox: list[int], second_bbox: list[int]) -> float:
    ax1, ay1, ax2, ay2 = first_bbox
    bx1, by1, bx2, by2 = second_bbox
    intersection_width = max(0, min(ax2, bx2) - max(ax1, bx1))
    intersection_height = max(0, min(ay2, by2) - max(ay1, by1))
    intersection = intersection_width * intersection_height
    if intersection <= 0:
        return 0.0
    first_area = max(1, (ax2 - ax1) * (ay2 - ay1))
    second_area = max(1, (bx2 - bx1) * (by2 - by1))
    return intersection / min(first_area, second_area)


def prioritize_plate_detections(
    plates: list[Detection],
    red_light_violations: list[RedLightViolationEvidence],
) -> list[Detection]:
    if not plates or not red_light_violations:
        return plates

    offending_boxes = [item.vehicle.bbox for item in red_light_violations]

    def sort_key(plate: Detection) -> tuple[int, float]:
        belongs_to_offending_vehicle = any(_box_center_inside(plate.bbox, box) for box in offending_boxes)
        return (0 if belongs_to_offending_vehicle else 1, -plate.confidence)

    return sorted(plates, key=sort_key)


def _box_center_inside(inner_bbox: list[int], outer_bbox: list[int]) -> bool:
    ix1, iy1, ix2, iy2 = inner_bbox
    ox1, oy1, ox2, oy2 = outer_bbox
    center_x = (ix1 + ix2) / 2
    center_y = (iy1 + iy2) / 2
    return ox1 <= center_x <= ox2 and oy1 <= center_y <= oy2


def draw_annotated_image(image_path: Path, bundle: DetectionBundle, output_path: Path) -> Path:
    from PIL import Image, ImageDraw

    colors = {
        "vehicle": "lime",
        "license": "yellow",
        "illegal_stop": "red",
        "red_light": "red",
        "zebra_crossing": "deepskyblue",
    }
    with Image.open(image_path) as image:
        canvas = image.convert("RGB")
        draw = ImageDraw.Draw(canvas)
        font = _load_annotation_font()
        for group in (
            bundle.vehicle,
            bundle.license_plate,
            bundle.illegal_stop,
            bundle.red_light,
            bundle.zebra_crossing,
        ):
            for item in group:
                color = colors.get(item.model, "cyan")
                draw.rectangle(item.bbox, outline=color, width=3)
                label = f"{item.display_label or item.label} {item.confidence:.0%}"
                _draw_annotation_text(
                    draw,
                    (item.bbox[0], max(0, item.bbox[1] - 18)),
                    label,
                    color,
                    font,
                )
        for evidence in bundle.red_light_violation:
            draw.rectangle(evidence.contact_bbox, outline="orange", width=3)
            if evidence.intersection_bbox:
                draw.rectangle(evidence.intersection_bbox, outline="magenta", width=4)
            label = f"suspected red light {evidence.overlap_ratio:.0%}"
            _draw_annotation_text(
                draw,
                (evidence.contact_bbox[0], max(0, evidence.contact_bbox[1] - 24)),
                label,
                "magenta",
                font,
            )
        if bundle.primary_target is not None:
            vehicle = bundle.primary_target.vehicle
            draw.rectangle(vehicle.bbox, outline="red", width=6)
            _draw_annotation_text(
                draw,
                (vehicle.bbox[0], min(canvas.height - 18, vehicle.bbox[1] + 4)),
                f"疑似违法目标 {vehicle.display_label or vehicle.label}",
                "red",
                font,
            )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(output_path)
    return output_path


def _load_annotation_font():
    import os

    from PIL import ImageFont

    windir = os.environ.get("WINDIR")
    candidates = []
    if windir:
        font_dir = Path(windir) / "Fonts"
        candidates.extend((font_dir / "msyh.ttc", font_dir / "simhei.ttf"))
    for candidate in candidates:
        if candidate.is_file():
            try:
                return ImageFont.truetype(str(candidate), size=16)
            except OSError:
                continue
    return ImageFont.load_default()


def _draw_annotation_text(draw, position, text: str, fill: str, font) -> None:
    try:
        draw.text(position, text, fill=fill, font=font)
    except UnicodeEncodeError:
        draw.text(position, text.encode("ascii", "replace").decode("ascii"), fill=fill, font=font)
