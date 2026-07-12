from __future__ import annotations

from ai_service.traffic_ai.schemas import DetectionBundle, ReviewResult, RuleResult


class IllegalStopRuleEvaluator:
    def evaluate(self, detections: DetectionBundle, plate_text: str | None) -> RuleResult:
        illegal = [item for item in detections.illegal_stop if item.label == "illegal"]
        if not illegal:
            return RuleResult(
                candidate_violation_type=None,
                rule_code="illegal_stop_model",
                rule_matched=False,
                evidence_level="不足",
                evidence_items=[],
                missing_evidence=["违停检测"],
                reason="未检测到违停目标",
            )

        evidence = ["违停检测"]
        missing: list[str] = []
        if detections.vehicle:
            evidence.append("车辆检测")
        else:
            missing.append("车辆检测")
        if plate_text:
            evidence.append("车牌识别")
        elif detections.license_plate:
            evidence.append("车牌定位")
            missing.append("车牌文字识别")
        else:
            missing.append("车牌定位")

        return RuleResult(
            candidate_violation_type="违停",
            rule_code="illegal_stop_model",
            rule_matched=True,
            evidence_level="完整" if not missing else "部分",
            evidence_items=evidence,
            missing_evidence=missing,
            reason="违停模型检测到违章停车目标",
        )


def review_from_rule(rule: RuleResult) -> ReviewResult:
    if rule.rule_matched and rule.evidence_level == "完整":
        return ReviewResult(
            conclusion="suggest_approve",
            confidence=0.85,
            reason="违停证据完整，可提交人工审核",
        )
    if rule.rule_matched:
        return ReviewResult(
            conclusion="need_review",
            confidence=0.65,
            reason="存在违停证据，但部分佐证缺失，需人工复核",
        )
    return ReviewResult(
        conclusion="suggest_reject",
        confidence=0.6,
        reason="未检测到违停证据，建议驳回",
    )
