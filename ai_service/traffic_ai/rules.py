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
                evidence_level="insufficient",
                evidence_items=[],
                missing_evidence=["illegal_stop detection"],
                reason="No illegal-stop target was detected.",
            )

        evidence = ["illegal_stop detection"]
        missing: list[str] = []
        if detections.vehicle:
            evidence.append("vehicle detection")
        else:
            missing.append("vehicle detection")
        if plate_text:
            evidence.append("plate OCR")
        elif detections.license_plate:
            evidence.append("license plate region")
            missing.append("plate OCR text")
        else:
            missing.append("license plate region")

        return RuleResult(
            candidate_violation_type="illegal_stop",
            rule_code="illegal_stop_model",
            rule_matched=True,
            evidence_level="complete" if not missing else "partial",
            evidence_items=evidence,
            missing_evidence=missing,
            reason="The illegal-stop model detected an illegal-stop target.",
        )


def review_from_rule(rule: RuleResult) -> ReviewResult:
    if rule.rule_matched and rule.evidence_level == "complete":
        return ReviewResult(
            conclusion="suggest_approve",
            confidence=0.85,
            reason="Illegal-stop evidence is complete enough for human review.",
        )
    if rule.rule_matched:
        return ReviewResult(
            conclusion="need_review",
            confidence=0.65,
            reason="Illegal-stop evidence exists, but some supporting evidence is missing.",
        )
    return ReviewResult(
        conclusion="suggest_reject",
        confidence=0.6,
        reason="No illegal-stop evidence was detected.",
    )
