from app.ai.adapters.base import (
    AIReviewResultData,
    DetectionResult,
    RuleResult,
)


def test_detection_result_construction():
    r = DetectionResult(
        objects=[{"label": "car"}],
        vehicle_bbox=[1, 2, 3, 4],
        plate_bbox=None,
        annotated_image_path=None,
        model_version="stub",
    )
    assert r.objects == [{"label": "car"}]
    assert r.vehicle_bbox == [1, 2, 3, 4]


def test_rule_result_construction():
    r = RuleResult(
        candidate_violation_type="speed",
        rule_code="speed",
        rule_matched=True,
        evidence_level="complete",
        evidence_items=["超速"],
        missing_evidence=[],
        reason="ok",
    )
    assert r.rule_matched is True
    assert r.evidence_level == "complete"


def test_ai_review_result_data_construction():
    r = AIReviewResultData(
        conclusion="suggest_approve",
        ai_confidence=0.9,
        reason="ok",
        risk_points=[],
        missing_evidence=[],
        prompt_version="v1",
    )
    assert r.conclusion == "suggest_approve"
