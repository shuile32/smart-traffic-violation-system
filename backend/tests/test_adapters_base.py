"""TDD: AI 适配器数据结构"""

import sys
sys.path.insert(0, ".")

from app.ai.adapters.base import DetectionResult, RuleResult, AIReviewResultData, SendResult


class TestDetectionResult:
    def test_creation(self):
        dr = DetectionResult(
            objects=[{"label": "car", "confidence": 0.95, "bbox": [1, 2, 3, 4]}],
            vehicle_bbox=[1, 2, 3, 4],
            plate_bbox=[10, 20, 30, 40],
            annotated_image_path="/tmp/test.jpg",
            model_version="v1",
        )
        assert len(dr.objects) == 1
        assert dr.vehicle_bbox == [1, 2, 3, 4]
        assert dr.model_version == "v1"


class TestRuleResult:
    def test_complete_evidence(self):
        rr = RuleResult(
            candidate_violation_type="超速",
            rule_code="SPD-001",
            rule_matched=True,
            evidence_level="complete",
            evidence_items=["检测到车辆", "车速 80 > 限速 60"],
            missing_evidence=[],
            reason="满足超速规则",
        )
        assert rr.rule_matched is True
        assert rr.evidence_level == "complete"


class TestAIReviewResultData:
    def test_creation(self):
        ar = AIReviewResultData(
            conclusion="suggest_approve",
            ai_confidence=0.88,
            reason="证据完整",
            risk_points=[],
            missing_evidence=[],
            prompt_version="v1",
        )
        assert ar.conclusion == "suggest_approve"


class TestSendResult:
    def test_success(self):
        sr = SendResult(success=True, provider_msg_id="abc123")
        assert sr.success is True

    def test_failure(self):
        sr = SendResult(success=False, error="SMTP connection refused")
        assert sr.success is False
        assert "SMTP" in sr.error
