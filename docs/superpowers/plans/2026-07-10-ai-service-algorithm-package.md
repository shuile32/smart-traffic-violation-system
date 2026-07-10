# AI Service Algorithm Package Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an independent, testable `ai_service` package that runs the trained YOLO models for vehicle, license-plate, and illegal-stop detection, with a pluggable OCR slot and backend-friendly result schema.

**Architecture:** Keep algorithm code outside frontend and backend ownership. The package exposes pure dataclasses, model configuration, a YOLO detector wrapper, OCR interfaces, a rule evaluator, a pipeline orchestrator, and a CLI that emits JSON. Backend integration can later call the same pipeline or wrap it in the existing `YoloDetector/OcrEngine/RuleEvaluator` adapter interfaces.

**Tech Stack:** Python 3.11, Ultralytics YOLOv8, OpenCV/Pillow where available, pytest-style tests.

---

## File Structure

- Create `ai_service/traffic_ai/config.py`: model paths and local runtime environment setup.
- Create `ai_service/traffic_ai/schemas.py`: stable dataclasses for detections and pipeline results.
- Create `ai_service/traffic_ai/ocr.py`: OCR protocol, no-dependency fallback, optional PaddleOCR adapter, plate text normalization.
- Create `ai_service/traffic_ai/rules.py`: simple illegal-stop rule evaluator from model outputs.
- Create `ai_service/traffic_ai/yolo.py`: lazy Ultralytics model loading and normalized detection output.
- Create `ai_service/traffic_ai/pipeline.py`: combines YOLO detection, OCR, and rule evaluation.
- Create `ai_service/traffic_ai/cli.py`: `python -m ai_service.traffic_ai.cli image.jpg --json`.
- Create `ai_service/tests/`: focused unit tests using fake detectors and no real model load for fast checks.

## Tasks

### Task 1: Schemas, Config, OCR, Rules

- [x] Write failing tests for model path defaults, env setup, OCR normalization, and illegal-stop rule mapping.
- [x] Run tests and verify imports fail because package does not exist.
- [x] Implement minimal dataclasses, config helpers, OCR fallback, and rule evaluator.
- [x] Run tests and verify they pass.

### Task 2: Pipeline

- [x] Write failing tests for a fake YOLO detector and fake OCR engine flowing through `TrafficViolationPipeline`.
- [x] Implement pipeline orchestration and JSON-friendly serialization.
- [x] Run pipeline tests and verify they pass.

### Task 3: YOLO Wrapper and CLI

- [x] Write tests for YOLO result normalization using fake prediction objects.
- [x] Implement lazy Ultralytics wrapper and CLI entry point.
- [x] Run unit tests.
- [x] Run an environment/model-name smoke check with the real `E:\anaconda3\envs\yolo\python.exe`.

### Task 4: Documentation

- [x] Add `ai_service/README.md` with run commands, dependency notes, model layout, OCR status, and backend integration guidance.
- [x] Keep generated runtime folders ignored by git.
