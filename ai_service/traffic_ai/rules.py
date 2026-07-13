from __future__ import annotations

from ai_service.traffic_ai.red_light import is_red_light_label
from ai_service.traffic_ai.schemas import DetectionBundle, ReviewResult, RuleResult


class IllegalStopRuleEvaluator:
    def evaluate(self, detections: DetectionBundle, plate_text: str | None) -> RuleResult:
        illegal = [item for item in detections.illegal_stop if item.label == "illegal"]
        if not illegal:
            return RuleResult(
                candidate_violation_type=None,
                rule_code="illegal_stop_model",
                rule_matched=False,
                evidence_level="insufficient",
                evidence_items=[],
                missing_evidence=["illegal_stop detection"],
                reason="未检测到违停目标",
            )

        associated_targets = [
            item for item in detections.violation_targets if item.violation_type == "illegal_stop"
        ]
        if not associated_targets:
            evidence = ["illegal_stop detection"]
            missing = ["offending vehicle association"]
            if detections.vehicle:
                evidence.append("vehicle detection")
            else:
                missing.append("vehicle detection")
            return RuleResult(
                candidate_violation_type=None,
                rule_code="illegal_stop_model",
                rule_matched=False,
                evidence_level="insufficient",
                evidence_items=evidence,
                missing_evidence=missing,
                reason="违停检测框未能与车辆检测框关联",
            )

        evidence = ["illegal_stop detection", "offending vehicle association"]
        missing: list[str] = []
        if detections.vehicle:
            evidence.append("vehicle detection")
        else:
            missing.append("vehicle detection")
        if plate_text:
            evidence.append("plate recognition")
        elif detections.license_plate:
            evidence.append("plate localization")
            missing.append("plate text recognition")
        else:
            missing.append("plate localization")

        return RuleResult(
            candidate_violation_type="illegal_stop",
            rule_code="illegal_stop_model",
            rule_matched=True,
            evidence_level="complete" if not missing else "partial",
            evidence_items=evidence,
            missing_evidence=missing,
            reason="违停模型检测到违章停车目标",
        )


class RedLightRuleEvaluator:
    def evaluate(self, detections: DetectionBundle, plate_text: str | None) -> RuleResult:
        if not detections.red_light_violation:
            evidence: list[str] = []
            missing: list[str] = []
            if any(is_red_light_label(item.label) for item in detections.red_light):
                evidence.append("red traffic light detection")
            else:
                missing.append("red traffic light detection")
            if detections.zebra_crossing:
                evidence.append("zebra crossing detection")
            else:
                missing.append("zebra crossing detection")
            if detections.vehicle:
                evidence.append("vehicle detection")
            else:
                missing.append("vehicle detection")
            missing.append("vehicle-crossing contact")
            return RuleResult(
                candidate_violation_type=None,
                rule_code="red_light_zebra_overlap",
                rule_matched=False,
                evidence_level="insufficient",
                evidence_items=evidence,
                missing_evidence=missing,
                reason="未形成红灯状态下车辆占压斑马线的完整证据",
            )

        strongest = max(detections.red_light_violation, key=lambda item: item.confidence)
        evidence = [
            "red traffic light detection",
            "zebra crossing detection",
            "vehicle detection",
            "vehicle-crossing contact",
        ]
        missing: list[str] = []
        _append_plate_evidence(detections, plate_text, evidence, missing)
        return RuleResult(
            candidate_violation_type="red_light_violation",
            rule_code="red_light_zebra_overlap",
            rule_matched=True,
            evidence_level="complete" if not missing else "partial",
            evidence_items=evidence,
            missing_evidence=missing,
            reason=f"红灯状态下车辆接地区域与斑马线重叠 {strongest.overlap_ratio:.1%}，疑似闯红灯",
        )


class TrafficRuleEvaluator:
    def __init__(self) -> None:
        self.red_light = RedLightRuleEvaluator()
        self.illegal_stop = IllegalStopRuleEvaluator()

    def evaluate(
        self,
        detections: DetectionBundle,
        plate_text: str | None,
        requested_rule: str | None = None,
    ) -> RuleResult:
        if requested_rule in {"red_light", "red_light_violation"}:
            return self.red_light.evaluate(detections, plate_text)
        if requested_rule == "illegal_stop":
            return self.illegal_stop.evaluate(detections, plate_text)
        if detections.red_light_violation:
            return self.red_light.evaluate(detections, plate_text)
        return self.illegal_stop.evaluate(detections, plate_text)


def _append_plate_evidence(
    detections: DetectionBundle,
    plate_text: str | None,
    evidence: list[str],
    missing: list[str],
) -> None:
    if plate_text:
        evidence.append("plate recognition")
    elif detections.license_plate:
        evidence.append("plate localization")
        missing.append("plate text recognition")
    else:
        missing.append("plate localization")


def review_from_rule(rule: RuleResult) -> ReviewResult:
    if rule.rule_matched and rule.evidence_level == "complete":
        return ReviewResult(
            conclusion="suggest_approve",
            confidence=0.85,
            reason="疑似违法证据完整，可提交人工审核",
        )
    if rule.rule_matched:
        return ReviewResult(
            conclusion="need_review",
            confidence=0.65,
            reason="存在疑似违法证据，但部分佐证缺失，需人工复核",
        )
    return ReviewResult(
        conclusion="suggest_reject",
        confidence=0.6,
        reason="未检测到支持该违法类型的证据，建议驳回",
    )
