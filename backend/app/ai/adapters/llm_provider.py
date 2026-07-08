"""LLM Provider — OpenAI 兼容协议（智谱 GLM，env 切 provider）"""

from openai import OpenAI

from app.core.config import settings
from app.ai.adapters.base import LLMProvider, AIReviewResultData


class OpenAICompatibleLLMProvider(LLMProvider):
    def __init__(self):
        self.client = OpenAI(
            base_url=settings.LLM_BASE_URL,
            api_key=settings.LLM_API_KEY,
        )
        self.model = settings.LLM_MODEL
        self.prompt_version = "traffic-review-v1"

    def review(self, evidence_payload: dict) -> AIReviewResultData:
        import json

        system_prompt = """你是一名交通违章审核助理。根据给定的证据 JSON，判断该案件是否构成违章。
输出 JSON 格式：
{
  "conclusion": "suggest_approve" | "need_review" | "suggest_reject",
  "confidence": 0.0-1.0,
  "reason": "判定理由，200字以内",
  "risk_points": ["风险点1"],
  "missing_evidence": ["缺失证据1"]
}"""

        user_prompt = f"证据如下：\n{json.dumps(evidence_payload, ensure_ascii=False, indent=2)}"

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        data = json.loads(content)

        return AIReviewResultData(
            conclusion=data.get("conclusion", "need_review"),
            ai_confidence=data.get("confidence"),
            reason=data.get("reason", ""),
            risk_points=data.get("risk_points", []),
            missing_evidence=data.get("missing_evidence", []),
            prompt_version=self.prompt_version,
        )
