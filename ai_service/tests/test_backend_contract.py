import unittest

from ai_service.traffic_ai.backend_contract import (
    detection_bundle_to_backend_dict,
    review_result_to_backend_dict,
    rule_result_to_backend_dict,
)
from ai_service.traffic_ai.schemas import (
    Detection,
    DetectionBundle,
    RedLightViolationEvidence,
    ReviewResult,
    RuleResult,
)


class BackendContractTest(unittest.TestCase):
    def test_detection_bundle_to_backend_dict_uses_first_vehicle_and_plate_box(self):
        bundle = DetectionBundle(
            vehicle=[Detection(label="cars", confidence=0.9, bbox=[0, 1, 2, 3], model="vehicle")],
            license_plate=[
                Detection(label="chinese-plate-license", confidence=0.8, bbox=[4, 5, 6, 7], model="license")
            ],
            illegal_stop=[Detection(label="illegal", confidence=0.7, bbox=[8, 9, 10, 11], model="illegal_stop")],
        )

        payload = detection_bundle_to_backend_dict(bundle)

        self.assertEqual(payload["vehicle_bbox"], [0, 1, 2, 3])
        self.assertEqual(payload["plate_bbox"], [4, 5, 6, 7])
        self.assertEqual(len(payload["objects"]), 3)
        self.assertEqual(payload["model_version"], "traffic-ai-local")

    def test_rule_result_to_backend_dict_keeps_route_response_fields(self):
        rule = RuleResult(
            candidate_violation_type="illegal_stop",
            rule_code="illegal_stop_model",
            rule_matched=True,
            evidence_level="complete",
            evidence_items=["illegal_stop detection"],
            missing_evidence=[],
            reason="matched",
        )

        payload = rule_result_to_backend_dict(rule)

        self.assertEqual(payload["rule_matched"], True)
        self.assertEqual(payload["evidence_items"], ["illegal_stop detection"])
        self.assertEqual(payload["reason"], "matched")

    def test_red_light_evidence_is_exposed_as_backend_object(self):
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

        payload = detection_bundle_to_backend_dict(
            DetectionBundle(
                vehicle=[vehicle],
                red_light=[red],
                zebra_crossing=[crossing],
                red_light_violation=[evidence],
            )
        )

        models = [item["model"] for item in payload["objects"]]
        self.assertEqual(models, ["vehicle", "red_light", "zebra_crossing", "red_light_rule"])
        rule_object = payload["objects"][-1]
        self.assertEqual(rule_object["evidence"]["overlap_ratio"], 1.0)
        self.assertEqual(rule_object["label"], "suspected_red_light_violation")

    def test_review_result_to_backend_dict_keeps_route_response_fields(self):
        review = ReviewResult(conclusion="suggest_approve", confidence=0.85, reason="ok")

        payload = review_result_to_backend_dict(review)

        self.assertEqual(payload["conclusion"], "suggest_approve")
        self.assertEqual(payload["ai_confidence"], 0.85)
        self.assertEqual(payload["reason"], "ok")


if __name__ == "__main__":
    unittest.main()
