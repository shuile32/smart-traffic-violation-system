from __future__ import annotations

import argparse
import json
from pathlib import Path

from ai_service.traffic_ai.pipeline import TrafficViolationPipeline
from ai_service.traffic_ai.yolo import UltralyticsTrafficDetector


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run traffic violation detection on one image.")
    parser.add_argument("image", type=Path, help="Image path")
    parser.add_argument("--min-confidence", type=float, default=0.25)
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    detector = UltralyticsTrafficDetector(min_confidence=args.min_confidence)
    pipeline = TrafficViolationPipeline(detector=detector)
    result = pipeline.analyze(args.image)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2 if args.pretty else None))


if __name__ == "__main__":
    main()
