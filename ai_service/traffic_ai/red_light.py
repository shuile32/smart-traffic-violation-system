from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from ai_service.traffic_ai.schemas import Detection, RedLightViolationEvidence


@dataclass(frozen=True)
class RedLightGeometryConfig:
    contact_height_ratio: float = 0.20
    horizontal_inset_ratio: float = 0.15
    crossing_horizontal_expansion_ratio: float = 0.15
    min_overlap_ratio: float = 0.25


def is_red_light_label(label: str) -> bool:
    normalized = " ".join(label.strip().casefold().replace("_", " ").replace("-", " ").split())
    return normalized in {"red", "red light", "traffic light red"}


def build_vehicle_contact_box(
    vehicle_bbox: list[int],
    config: RedLightGeometryConfig | None = None,
) -> list[int]:
    config = config or RedLightGeometryConfig()
    x1, y1, x2, y2 = _normalized_box(vehicle_bbox)
    width = x2 - x1
    height = y2 - y1
    left = round(x1 + width * config.horizontal_inset_ratio)
    right = round(x2 - width * config.horizontal_inset_ratio)
    top = round(y2 - height * config.contact_height_ratio)
    return [left, top, max(left + 1, right), max(top + 1, y2)]


def find_red_light_violations(
    vehicles: list[Detection],
    traffic_lights: list[Detection],
    zebra_crossings: list[Detection],
    config: RedLightGeometryConfig | None = None,
) -> list[RedLightViolationEvidence]:
    config = config or RedLightGeometryConfig()
    red_lights = [item for item in traffic_lights if is_red_light_label(item.label)]
    if not vehicles or not red_lights or not zebra_crossings:
        return []

    strongest_red = max(red_lights, key=lambda item: item.confidence)
    violations: list[RedLightViolationEvidence] = []
    for vehicle in vehicles:
        contact_bbox = build_vehicle_contact_box(vehicle.bbox, config)
        candidates: list[RedLightViolationEvidence] = []
        for crossing in zebra_crossings:
            crossing_rule_bbox = _expand_horizontal(
                crossing.bbox,
                config.crossing_horizontal_expansion_ratio,
            )
            overlap_ratio, intersection_bbox = _opencv_overlap(contact_bbox, crossing_rule_bbox)
            bottom_center_inside = _bottom_center_inside(vehicle.bbox, crossing_rule_bbox)
            if overlap_ratio < config.min_overlap_ratio and not bottom_center_inside:
                continue
            candidates.append(
                RedLightViolationEvidence(
                    vehicle=vehicle,
                    red_light=strongest_red,
                    zebra_crossing=crossing,
                    contact_bbox=contact_bbox,
                    intersection_bbox=intersection_bbox,
                    overlap_ratio=round(overlap_ratio, 4),
                    bottom_center_inside=bottom_center_inside,
                    confidence=round(
                        min(vehicle.confidence, strongest_red.confidence, crossing.confidence),
                        4,
                    ),
                )
            )
        if candidates:
            violations.append(max(candidates, key=lambda item: (item.overlap_ratio, item.confidence)))
    return violations


def _opencv_overlap(first_bbox: list[int], second_bbox: list[int]) -> tuple[float, list[int] | None]:
    first = _normalized_box(first_bbox)
    second = _normalized_box(second_bbox)
    union_left = min(first[0], second[0])
    union_top = min(first[1], second[1])
    union_right = max(first[2], second[2])
    union_bottom = max(first[3], second[3])
    width = union_right - union_left
    height = union_bottom - union_top
    if width <= 0 or height <= 0:
        return 0.0, None

    first_mask = np.zeros((height, width), dtype=np.uint8)
    second_mask = np.zeros((height, width), dtype=np.uint8)
    _fill_box(first_mask, first, union_left, union_top)
    _fill_box(second_mask, second, union_left, union_top)
    intersection = cv2.bitwise_and(first_mask, second_mask)
    first_area = int(cv2.countNonZero(first_mask))
    intersection_area = int(cv2.countNonZero(intersection))
    if first_area == 0 or intersection_area == 0:
        return 0.0, None

    points = cv2.findNonZero(intersection)
    x, y, intersection_width, intersection_height = cv2.boundingRect(points)
    intersection_bbox = [
        union_left + x,
        union_top + y,
        union_left + x + intersection_width,
        union_top + y + intersection_height,
    ]
    return intersection_area / first_area, intersection_bbox


def _fill_box(mask: np.ndarray, bbox: list[int], origin_x: int, origin_y: int) -> None:
    x1, y1, x2, y2 = bbox
    cv2.rectangle(
        mask,
        (x1 - origin_x, y1 - origin_y),
        (x2 - origin_x - 1, y2 - origin_y - 1),
        color=255,
        thickness=-1,
    )


def _bottom_center_inside(vehicle_bbox: list[int], crossing_bbox: list[int]) -> bool:
    vx1, _, vx2, vy2 = _normalized_box(vehicle_bbox)
    zx1, zy1, zx2, zy2 = _normalized_box(crossing_bbox)
    center_x = (vx1 + vx2) / 2
    return zx1 <= center_x <= zx2 and zy1 <= vy2 <= zy2


def _expand_horizontal(bbox: list[int], ratio: float) -> list[int]:
    x1, y1, x2, y2 = _normalized_box(bbox)
    padding = round((x2 - x1) * max(0.0, ratio))
    return [x1 - padding, y1, x2 + padding, y2]


def _normalized_box(bbox: list[int]) -> list[int]:
    if len(bbox) != 4:
        raise ValueError("bbox must contain four coordinates")
    x1, y1, x2, y2 = (int(value) for value in bbox)
    left, right = sorted((x1, x2))
    top, bottom = sorted((y1, y2))
    return [left, top, max(left + 1, right), max(top + 1, bottom)]
