"""TDD: RoiRuleEvaluator — 超速 + 占用专用车道规则判定"""

import sys
sys.path.insert(0, ".")

from app.ai.rules.roi_evaluator import RoiRuleEvaluator
from app.ai.adapters.base import DetectionResult


def make_detection(objects=None, vehicle_bbox=None, plate_bbox=None):
    return DetectionResult(
        objects=objects or [],
        vehicle_bbox=vehicle_bbox,
        plate_bbox=plate_bbox,
        annotated_image_path=None,
        model_version="test-v1",
    )


class TestSpeedRule:
    """超速规则判定"""

    def test_speed_over_limit_matches(self):
        evaluator = RoiRuleEvaluator()
        det = make_detection(objects=[{"label": "car", "confidence": 0.95, "bbox": [100, 100, 400, 400]}])
        evaluator._detection_objects = det.objects

        result = evaluator.evaluate(
            det,
            None,
            {"speed": 80, "captured_at": "2026-07-08T10:30:00"},
            {"rule_code": "SPD-001", "violation_type": "超速", "rule_type": "speed",
             "params": '{"speed_limit": 60, "road_segment": "人民路"}'},
        )

        assert result.rule_matched is True
        assert result.evidence_level == "complete"
        assert result.candidate_violation_type == "超速"

    def test_speed_under_limit_no_match(self):
        evaluator = RoiRuleEvaluator()
        det = make_detection()
        evaluator._detection_objects = det.objects

        result = evaluator.evaluate(
            det, None,
            {"speed": 50},
            {"rule_code": "SPD-001", "violation_type": "超速", "rule_type": "speed",
             "params": '{"speed_limit": 60}'},
        )

        assert result.rule_matched is False

    def test_speed_missing_data_reports_missing(self):
        evaluator = RoiRuleEvaluator()
        det = make_detection()
        evaluator._detection_objects = det.objects

        result = evaluator.evaluate(
            det, None,
            {"speed": None},
            {"rule_code": "SPD-001", "violation_type": "超速", "rule_type": "speed",
             "params": '{"speed_limit": 60}'},
        )

        assert result.rule_matched is False
        assert "未提供车速数据" in result.missing_evidence


class TestSpecialLaneRule:
    """占用专用车道规则判定"""

    def test_vehicle_in_lane_disallowed_type_matches(self):
        evaluator = RoiRuleEvaluator()
        det = make_detection(
            objects=[{"label": "car", "confidence": 0.9, "bbox": [100, 200, 400, 400]}],
            vehicle_bbox=[100, 200, 400, 400],
        )
        evaluator._detection_objects = det.objects

        lane_roi = [[50, 100], [500, 100], [500, 500], [50, 500]]  # 车辆中心 (250,300) 在内

        result = evaluator.evaluate(
            det, None,
            {"captured_at": "2026-07-08T08:00:00"},
            {"rule_code": "LANE-001", "violation_type": "占用专用车道", "rule_type": "special_lane",
             "params": f'{{"lane_roi": {lane_roi}, "allowed_vehicle_types": ["bus"], "time_window": {{"start": "07:00", "end": "09:00"}}}}'},
        )

        assert result.rule_matched is True
        assert result.candidate_violation_type == "占用专用车道"

    def test_bus_in_lane_allowed_no_match(self):
        evaluator = RoiRuleEvaluator()
        det = make_detection(
            objects=[{"label": "bus", "confidence": 0.9, "bbox": [100, 200, 400, 400]}],
            vehicle_bbox=[100, 200, 400, 400],
        )
        evaluator._detection_objects = det.objects

        lane_roi = [[50, 100], [500, 100], [500, 500], [50, 500]]

        result = evaluator.evaluate(
            det, None,
            {"captured_at": "2026-07-08T08:00:00"},
            {"rule_code": "LANE-001", "violation_type": "占用专用车道", "rule_type": "special_lane",
             "params": f'{{"lane_roi": {lane_roi}, "allowed_vehicle_types": ["bus"], "time_window": {{"start": "07:00", "end": "09:00"}}}}'},
        )

        assert result.rule_matched is False

    def test_outside_time_window_no_match(self):
        evaluator = RoiRuleEvaluator()
        det = make_detection(
            objects=[{"label": "car", "confidence": 0.9, "bbox": [100, 200, 400, 400]}],
            vehicle_bbox=[100, 200, 400, 400],
        )
        evaluator._detection_objects = det.objects

        lane_roi = [[50, 100], [500, 100], [500, 500], [50, 500]]

        result = evaluator.evaluate(
            det, None,
            {"captured_at": "2026-07-08T12:00:00"},  # 非限行时段
            {"rule_code": "LANE-001", "violation_type": "占用专用车道", "rule_type": "special_lane",
             "params": f'{{"lane_roi": {lane_roi}, "allowed_vehicle_types": ["bus"], "time_window": {{"start": "07:00", "end": "09:00"}}}}'},
        )

        assert result.rule_matched is False

    def test_vehicle_outside_roi_no_match(self):
        evaluator = RoiRuleEvaluator()
        det = make_detection(
            objects=[{"label": "car", "confidence": 0.9, "bbox": [600, 600, 800, 800]}],
            vehicle_bbox=[600, 600, 800, 800],
        )  # 中心 (700,700) 在小 ROI 外
        evaluator._detection_objects = det.objects

        lane_roi = [[50, 100], [500, 100], [500, 500], [50, 500]]

        result = evaluator.evaluate(
            det, None,
            {"captured_at": "2026-07-08T08:00:00"},
            {"rule_code": "LANE-001", "violation_type": "占用专用车道", "rule_type": "special_lane",
             "params": f'{{"lane_roi": {lane_roi}, "allowed_vehicle_types": ["bus"], "time_window": {{"start": "07:00", "end": "09:00"}}}}'},
        )

        assert result.rule_matched is False


class TestUnknownRuleType:
    def test_unknown_rule_returns_insufficient(self):
        evaluator = RoiRuleEvaluator()
        det = make_detection()
        evaluator._detection_objects = det.objects

        result = evaluator.evaluate(
            det, None, {},
            {"rule_code": "XXX-001", "violation_type": "未知", "rule_type": "unknown"},
        )

        assert result.rule_matched is False
        assert result.evidence_level == "insufficient"
