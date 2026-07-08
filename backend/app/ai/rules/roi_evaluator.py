"""ROI 规则判定器 — 超速 + 占用专用车道

第一阶段支持两种违章类型：
- speed: 不依赖 YOLO 视觉要素，靠摄像头上传的 speed 元数据
- special_lane: YOLO 车辆框 + ROI 几何判断
"""

import json
from datetime import datetime

from app.ai.adapters.base import RuleEvaluator, DetectionResult, RuleResult


class RoiRuleEvaluator(RuleEvaluator):
    COCO_VEHICLE_CLASSES = {"car", "truck", "bus", "motorcycle"}

    def evaluate(
        self,
        detection: DetectionResult,
        ocr_result: str | None,
        intake_event: dict,
        rule: dict,
    ) -> RuleResult:
        rule_type = rule.get("rule_type", "")
        params = rule.get("params", {})
        if isinstance(params, str):
            params = json.loads(params)

        if rule_type == "speed":
            return self._evaluate_speed(intake_event, rule, params)
        elif rule_type == "special_lane":
            return self._evaluate_special_lane(detection, intake_event, rule, params)
        else:
            return RuleResult(
                candidate_violation_type=None,
                rule_code=rule.get("rule_code"),
                rule_matched=False,
                evidence_level="insufficient",
                evidence_items=[],
                missing_evidence=[f"不支持的规则类型: {rule_type}"],
                reason=f"规则类型 {rule_type} 尚未实现",
            )

    # ── 超速判定 ──────────────────────────────────

    def _evaluate_speed(self, intake_event: dict, rule: dict, params: dict) -> RuleResult:
        speed = intake_event.get("speed")
        speed_limit = params.get("speed_limit", 60)
        road_segment = params.get("road_segment", "")

        # 检测到车辆
        vehicle_found = any(
            obj["label"] in self.COCO_VEHICLE_CLASSES
            for obj in getattr(self, "_detection_objects", [])
        )

        evidence_items = []
        missing_evidence = []

        if speed is None:
            missing_evidence.append("未提供车速数据")
        else:
            evidence_items.append(f"车速 {speed} km/h，限速 {speed_limit} km/h")

        if vehicle_found:
            evidence_items.append("检测到车辆")
        # 超速不强制要求 YOLO 检到车（摄像头抓拍本身就已经判断有车）

        rule_matched = speed is not None and speed > speed_limit

        if speed is not None and speed <= speed_limit:
            evidence_items.append(f"车速 {speed} 未超过限速 {speed_limit}")
            rule_matched = False

        return RuleResult(
            candidate_violation_type=rule.get("violation_type"),  # 超速
            rule_code=rule.get("rule_code"),
            rule_matched=rule_matched,
            evidence_level="complete" if rule_matched and not missing_evidence else "partial",
            evidence_items=evidence_items,
            missing_evidence=missing_evidence,
            reason=f"{'满足' if rule_matched else '不满足'}超速规则" + (f"（{road_segment}）" if road_segment else ""),
        )

    # ── 占用专用车道判定 ──────────────────────────

    def _evaluate_special_lane(
        self,
        detection: DetectionResult,
        intake_event: dict,
        rule: dict,
        params: dict,
    ) -> RuleResult:
        lane_roi = params.get("lane_roi", [])  # [[x1,y1],[x2,y2],...]
        allowed_vehicle_types = params.get("allowed_vehicle_types", ["bus"])
        time_window = params.get("time_window")  # {"start":"07:00","end":"09:00"}

        evidence_items = []
        missing_evidence = []

        # 1. 车辆框中心点是否在 ROI 内
        vehicle_in_roi = False
        if detection.vehicle_bbox and lane_roi:
            cx = (detection.vehicle_bbox[0] + detection.vehicle_bbox[2]) / 2
            cy = (detection.vehicle_bbox[1] + detection.vehicle_bbox[3]) / 2
            vehicle_in_roi = self._point_in_polygon(cx, cy, lane_roi)
            if vehicle_in_roi:
                evidence_items.append("车辆位于专用车道 ROI 内")
            else:
                missing_evidence.append("车辆不在专用车道 ROI 内")
        else:
            missing_evidence.append("未检测到车辆框或未配置 ROI")

        # 2. 时间窗口检查
        in_time_window = True
        if time_window:
            captured_at = intake_event.get("captured_at")
            if isinstance(captured_at, str):
                captured_at = datetime.fromisoformat(captured_at)
            if isinstance(captured_at, datetime):
                current_time = captured_at.strftime("%H:%M")
                in_time_window = time_window["start"] <= current_time <= time_window["end"]
                if in_time_window:
                    evidence_items.append(f"当前时间 {current_time} 在限行时段 {time_window['start']}-{time_window['end']}")
                else:
                    missing_evidence.append(f"当前时间 {current_time} 不在限行时段")

        # 3. 车辆类型检查
        vehicle_label = None
        for obj in detection.objects:
            if obj["label"] in self.COCO_VEHICLE_CLASSES:
                vehicle_label = obj["label"]
                break

        vehicle_disallowed = False
        if vehicle_label:
            if vehicle_label not in allowed_vehicle_types:
                vehicle_disallowed = True
                evidence_items.append(f"车辆类型 {vehicle_label} 不在允许列表 {allowed_vehicle_types}")
            else:
                evidence_items.append(f"车辆类型 {vehicle_label} 在允许列表中")

        rule_matched = vehicle_in_roi and in_time_window and vehicle_disallowed

        return RuleResult(
            candidate_violation_type=rule.get("violation_type"),  # 占用专用车道
            rule_code=rule.get("rule_code"),
            rule_matched=rule_matched,
            evidence_level="complete" if rule_matched else "partial",
            evidence_items=evidence_items,
            missing_evidence=missing_evidence,
            reason="满足占用专用车道规则" if rule_matched else "不满足占用专用车道规则",
        )

    # ── 工具：点是否在多边形内 ─────────────────────

    @staticmethod
    def _point_in_polygon(x: float, y: float, polygon: list) -> bool:
        """射线法判断点是否在多边形内"""
        n = len(polygon)
        inside = False
        j = n - 1
        for i in range(n):
            xi, yi = polygon[i]
            xj, yj = polygon[j]
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                inside = not inside
            j = i
        return inside
