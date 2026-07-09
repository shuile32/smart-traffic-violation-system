"""AI adapter DI 工厂。按 settings.AI_PROVIDER 选实现。

唐高鹏交付 real 实现后，在各工厂加 elif 分支返回 real 类，不改路由。
"""
from app.ai.adapters.base import (
    LLMProvider,
    OcrEngine,
    RuleEvaluator,
    YoloDetector,
)
from app.ai.adapters.stub import (
    StubLLMProvider,
    StubOcrEngine,
    StubRuleEvaluator,
    StubYoloDetector,
)
from app.core.config import settings


def _provider_not_supported() -> Exception:
    return NotImplementedError(f"AI_PROVIDER={settings.AI_PROVIDER} 暂未支持")


def get_yolo_detector() -> YoloDetector:
    if settings.AI_PROVIDER == "stub":
        return StubYoloDetector()
    raise _provider_not_supported()


def get_ocr_engine() -> OcrEngine:
    if settings.AI_PROVIDER == "stub":
        return StubOcrEngine()
    raise _provider_not_supported()


def get_rule_evaluator() -> RuleEvaluator:
    if settings.AI_PROVIDER == "stub":
        return StubRuleEvaluator()
    raise _provider_not_supported()


def get_llm_provider() -> LLMProvider:
    if settings.AI_PROVIDER == "stub":
        return StubLLMProvider()
    raise _provider_not_supported()
