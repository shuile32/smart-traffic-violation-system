import unittest

from ai_service.traffic_ai.red_light import (
    RedLightGeometryConfig,
    build_vehicle_contact_box,
    find_red_light_violations,
    is_red_light_label,
)
from ai_service.traffic_ai.schemas import Detection


def detection(label, confidence, bbox, model):
    return Detection(label=label, confidence=confidence, bbox=bbox, model=model)


class RedLightGeometryTest(unittest.TestCase):
    def test_only_trained_red_signal_label_is_treated_as_red(self):
        self.assertTrue(is_red_light_label("Traffic Light - Red"))
        self.assertTrue(is_red_light_label("traffic_light_red"))
        self.assertFalse(is_red_light_label("Traffic Light - Yellow"))
        self.assertFalse(is_red_light_label("Traffic Lioght - Green"))
        self.assertFalse(is_red_light_label("Traffic Light - Off"))

    def test_vehicle_contact_box_uses_bottom_twenty_percent_with_side_insets(self):
        contact = build_vehicle_contact_box([0, 0, 100, 100])

        self.assertEqual(contact, [15, 80, 85, 100])

    def test_overlap_at_threshold_creates_suspected_violation(self):
        config = RedLightGeometryConfig(
            horizontal_inset_ratio=0.0,
            crossing_horizontal_expansion_ratio=0.0,
        )
        vehicles = [detection("cars", 0.91, [0, 0, 100, 100], "vehicle")]
        red_lights = [detection("Traffic Light - Red", 0.88, [120, 0, 140, 30], "red_light")]
        crossings = [detection("zebra crossing", 0.86, [0, 80, 25, 100], "zebra_crossing")]

        evidence = find_red_light_violations(vehicles, red_lights, crossings, config)

        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0].contact_bbox, [0, 80, 100, 100])
        self.assertEqual(evidence[0].intersection_bbox, [0, 80, 25, 100])
        self.assertEqual(evidence[0].overlap_ratio, 0.25)
        self.assertFalse(evidence[0].bottom_center_inside)
        self.assertEqual(evidence[0].confidence, 0.86)

    def test_overlap_below_threshold_does_not_match_without_bottom_center(self):
        config = RedLightGeometryConfig(
            horizontal_inset_ratio=0.0,
            crossing_horizontal_expansion_ratio=0.0,
        )
        vehicles = [detection("cars", 0.91, [0, 0, 100, 100], "vehicle")]
        red_lights = [detection("Traffic Light - Red", 0.88, [120, 0, 140, 30], "red_light")]
        crossings = [detection("zebra crossing", 0.86, [0, 80, 24, 100], "zebra_crossing")]

        evidence = find_red_light_violations(vehicles, red_lights, crossings, config)

        self.assertEqual(evidence, [])

    def test_bottom_center_inside_matches_even_when_overlap_is_small(self):
        config = RedLightGeometryConfig(
            horizontal_inset_ratio=0.0,
            crossing_horizontal_expansion_ratio=0.0,
        )
        vehicles = [detection("cars", 0.91, [0, 0, 100, 100], "vehicle")]
        red_lights = [detection("Traffic Light - Red", 0.88, [120, 0, 140, 30], "red_light")]
        crossings = [detection("zebra crossing", 0.86, [49, 99, 51, 101], "zebra_crossing")]

        evidence = find_red_light_violations(vehicles, red_lights, crossings, config)

        self.assertEqual(len(evidence), 1)
        self.assertTrue(evidence[0].bottom_center_inside)
        self.assertLess(evidence[0].overlap_ratio, 0.25)

    def test_horizontal_crossing_tolerance_handles_detector_undercoverage(self):
        vehicles = [detection("cars", 0.874, [610, 440, 780, 610], "vehicle")]
        red_lights = [
            detection("Traffic Light - Red", 0.7297, [726, 0, 748, 57], "red_light")
        ]
        crossings = [
            detection("zebra crossing", 0.6884, [0, 437, 629, 592], "zebra_crossing")
        ]

        evidence = find_red_light_violations(vehicles, red_lights, crossings)

        self.assertEqual(len(evidence), 1)
        self.assertGreaterEqual(evidence[0].overlap_ratio, 0.25)

    def test_missing_red_vehicle_or_crossing_never_matches(self):
        vehicle = detection("cars", 0.91, [0, 0, 100, 100], "vehicle")
        red = detection("Traffic Light - Red", 0.88, [120, 0, 140, 30], "red_light")
        green = detection("Traffic Lioght - Green", 0.93, [120, 0, 140, 30], "red_light")
        crossing = detection("zebra crossing", 0.86, [0, 80, 100, 110], "zebra_crossing")

        self.assertEqual(find_red_light_violations([], [red], [crossing]), [])
        self.assertEqual(find_red_light_violations([vehicle], [], [crossing]), [])
        self.assertEqual(find_red_light_violations([vehicle], [green], [crossing]), [])
        self.assertEqual(find_red_light_violations([vehicle], [red], []), [])


if __name__ == "__main__":
    unittest.main()
