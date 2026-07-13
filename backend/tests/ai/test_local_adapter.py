from pathlib import Path
from types import SimpleNamespace

from app.ai.adapters.base import DetectionResult


def test_local_yolo_detector_forwards_requested_violation_type():
    from app.ai.adapters import local
    from ai_service.traffic_ai.schemas import DetectionBundle

    seen = {}
    adapter = object.__new__(local.LocalYoloDetector)

    def detect(path, requested_violation_type):
        seen["path"] = path
        seen["requested_violation_type"] = requested_violation_type
        return DetectionBundle(requested_violation_type=requested_violation_type)

    adapter._detector = SimpleNamespace(detect=detect)

    result = adapter.detect("frame.jpg", "illegal_stop")

    assert seen["path"] == Path("frame.jpg")
    assert seen["requested_violation_type"] == "illegal_stop"
    assert result.requested_violation_type == "illegal_stop"


def test_local_rule_evaluator_maps_illegal_stop_detection():
    from app.ai.adapters.local import LocalRuleEvaluator

    vehicle = {
        "label": "cars",
        "confidence": 0.93,
        "bbox": [10, 20, 100, 120],
        "model": "vehicle",
        "detection_id": "vehicle-1",
        "display_label": "小汽车1",
    }
    primary_target = {
        "violation_type": "illegal_stop",
        "vehicle": vehicle,
        "confidence": 0.91,
        "association_score": 1.0,
        "evidence_bbox": [10, 20, 100, 120],
        "evidence_model": "illegal_stop",
        "is_primary": True,
    }
    detection = DetectionResult(
        objects=[
            vehicle,
            {
                "label": "illegal",
                "confidence": 0.91,
                "bbox": [10, 20, 100, 120],
                "model": "illegal_stop",
            }
        ],
        vehicle_bbox=None,
        plate_bbox=None,
        annotated_image_path=None,
        model_version="traffic-ai-local",
        requested_violation_type="illegal_stop",
        violation_targets=[primary_target],
        primary_target=primary_target,
    )

    result = LocalRuleEvaluator().evaluate(detection, "京A12345", {}, {"type": "illegal_stop"})

    assert result.rule_matched is True
    assert result.candidate_violation_type == "illegal_stop"
    assert result.evidence_level in {"complete", "partial"}


def test_detection_bundle_is_converted_to_backend_media_url(tmp_path, monkeypatch):
    from ai_service.traffic_ai.schemas import Detection, DetectionBundle
    from app.ai.adapters import local

    media_root = tmp_path / "media"
    output_path = media_root / "ai_outputs" / "case.jpg"
    output_path.parent.mkdir(parents=True)
    output_path.write_bytes(b"fake")
    monkeypatch.setattr(local.settings, "MEDIA_STORAGE_DIR", str(media_root))

    bundle = DetectionBundle(
        vehicle=[Detection("car", 0.9, [1, 2, 3, 4], "vehicle")],
        license_plate=[Detection("chinese-plate-license", 0.8, [5, 6, 7, 8], "license")],
        illegal_stop=[Detection("illegal", 0.95, [9, 10, 11, 12], "illegal_stop")],
        annotated_image_path=str(output_path),
    )

    result = local._bundle_to_detection_result(bundle)

    assert result.vehicle_bbox == [1, 2, 3, 4]
    assert result.plate_bbox == [5, 6, 7, 8]
    assert result.annotated_image_path == "/media/ai_outputs/case.jpg"
    assert result.model_version == "traffic-ai-local"


def test_default_ai_output_dir_is_flat_media_root(tmp_path, monkeypatch):
    from app.ai.adapters import local

    monkeypatch.setattr(local.settings, "MEDIA_STORAGE_DIR", str(tmp_path))

    assert local._default_ai_output_dir() == tmp_path


def test_local_adapter_round_trips_primary_violation_target():
    from app.ai.adapters import local
    from ai_service.traffic_ai.schemas import Detection, DetectionBundle, ViolationTargetEvidence

    other_vehicle = Detection(
        "cars", 0.95, [110, 0, 200, 100], "vehicle", "vehicle-1", "小汽车1"
    )
    vehicle = Detection(
        "cars", 0.91, [0, 0, 100, 100], "vehicle", "vehicle-2", "小汽车2"
    )
    target = ViolationTargetEvidence(
        violation_type="illegal_stop",
        vehicle=vehicle,
        confidence=0.88,
        association_score=0.95,
        evidence_bbox=[0, 0, 100, 100],
        evidence_model="illegal_stop",
        is_primary=True,
    )
    bundle = DetectionBundle(
        vehicle=[other_vehicle, vehicle],
        requested_violation_type="illegal_stop",
        violation_targets=[target],
        primary_target=target,
    )

    detection_result = local._bundle_to_detection_result(bundle)
    restored = local._detection_result_to_bundle(detection_result)

    assert detection_result.primary_target["vehicle"]["detection_id"] == "vehicle-2"
    assert detection_result.vehicle_bbox == vehicle.bbox
    assert restored.requested_violation_type == "illegal_stop"
    assert restored.primary_target is not None
    assert restored.primary_target.vehicle.display_label == "小汽车2"


def test_local_ocr_engine_delegates_to_algorithm_engine(tmp_path):
    from app.ai.adapters.local import LocalOcrEngine

    class FakeEngine:
        def recognize(self, path: Path):
            assert path.name == "plate.jpg"
            return type("OcrResult", (), {"text": "沪B12345"})()

    result = LocalOcrEngine(engine=FakeEngine()).recognize_plate(str(tmp_path / "plate.jpg"))

    assert result == "沪B12345"


def test_local_adapter_round_trips_red_light_evidence(tmp_path, monkeypatch):
    from ai_service.traffic_ai.schemas import Detection, DetectionBundle, RedLightViolationEvidence
    from app.ai.adapters import local

    media_root = tmp_path / "media"
    output_path = media_root / "ai_outputs" / "red-light.jpg"
    output_path.parent.mkdir(parents=True)
    output_path.write_bytes(b"fake")
    monkeypatch.setattr(local.settings, "MEDIA_STORAGE_DIR", str(media_root))
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
        red_light=[red],
        zebra_crossing=[crossing],
        red_light_violation=[evidence],
        annotated_image_path=str(output_path),
    )

    detection_result = local._bundle_to_detection_result(bundle)
    restored = local._detection_result_to_bundle(detection_result)

    assert [item["model"] for item in detection_result.objects][-1] == "red_light_rule"
    assert len(restored.red_light_violation) == 1
    assert restored.red_light_violation[0].overlap_ratio == 1.0


def test_local_rule_evaluator_maps_red_light_violation():
    from ai_service.traffic_ai.schemas import Detection, DetectionBundle, RedLightViolationEvidence
    from app.ai.adapters import local

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
    detection = local._bundle_to_detection_result(
        DetectionBundle(
            vehicle=[vehicle],
            red_light=[red],
            zebra_crossing=[crossing],
            red_light_violation=[evidence],
        )
    )

    result = local.LocalRuleEvaluator().evaluate(detection, "粤A12345", {}, {"type": "auto"})

    assert result.rule_matched is True
    assert result.candidate_violation_type == "red_light_violation"
    assert result.rule_code == "red_light_zebra_overlap"
