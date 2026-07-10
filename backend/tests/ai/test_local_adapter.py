from pathlib import Path

from app.ai.adapters.base import DetectionResult


def test_local_rule_evaluator_maps_illegal_stop_detection():
    from app.ai.adapters.local import LocalRuleEvaluator

    detection = DetectionResult(
        objects=[
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
    )

    result = LocalRuleEvaluator().evaluate(detection, "京A12345", {}, {})

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


def test_local_ocr_engine_delegates_to_algorithm_engine(tmp_path):
    from app.ai.adapters.local import LocalOcrEngine

    class FakeEngine:
        def recognize(self, path: Path):
            assert path.name == "plate.jpg"
            return type("OcrResult", (), {"text": "沪B12345"})()

    result = LocalOcrEngine(engine=FakeEngine()).recognize_plate(str(tmp_path / "plate.jpg"))

    assert result == "沪B12345"
