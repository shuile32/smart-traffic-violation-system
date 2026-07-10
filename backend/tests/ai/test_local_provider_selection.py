def test_provider_factories_select_local_adapters(monkeypatch):
    from app.ai import providers

    monkeypatch.setattr(providers.settings, "AI_PROVIDER", "local")
    monkeypatch.setattr(providers.settings, "LLM_PROVIDER", "")
    monkeypatch.setattr(providers.settings, "LLM_API_KEY", "")

    assert providers.get_yolo_detector().__class__.__name__ == "LocalYoloDetector"
    assert providers.get_ocr_engine().__class__.__name__ == "LocalOcrEngine"
    assert providers.get_rule_evaluator().__class__.__name__ == "LocalRuleEvaluator"


def test_provider_factory_selects_openai_compatible_llm(monkeypatch):
    from app.ai import providers

    monkeypatch.setattr(providers.settings, "AI_PROVIDER", "local")
    monkeypatch.setattr(providers.settings, "LLM_PROVIDER", "zhipu")
    monkeypatch.setattr(providers.settings, "LLM_API_KEY", "test-key")
    monkeypatch.setattr(providers.settings, "LLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
    monkeypatch.setattr(providers.settings, "LLM_TEXT_MODEL", "glm-5.1")
    monkeypatch.setattr(providers.settings, "LLM_VISION_MODEL", "glm-5v-turbo")
    monkeypatch.setattr(providers.settings, "LLM_MODE", "vision")
    monkeypatch.setattr(providers.settings, "LLM_TIMEOUT_SECONDS", 30)

    assert providers.get_llm_provider().__class__.__name__ == "OpenAICompatibleLLMProvider"
