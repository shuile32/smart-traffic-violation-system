"""AI 组件抽象接口 — 可插拔，每组件一套实现，后期可换"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class DetectionResult:
    """YOLO 检测结果"""
    objects: list[dict]  # [{label, confidence, bbox}, ...]
    vehicle_bbox: list[int] | None  # [x1, y1, x2, y2]
    plate_bbox: list[int] | None
    annotated_image_path: str | None
    model_version: str


@dataclass
class RuleResult:
    """规则判定结果"""
    candidate_violation_type: str | None
    rule_code: str | None
    rule_matched: bool
    evidence_level: str  # complete / partial / insufficient
    evidence_items: list[str]
    missing_evidence: list[str]
    reason: str


@dataclass
class AIReviewResultData:
    """LLM 初审结果"""
    conclusion: str  # suggest_approve / need_review / suggest_reject
    ai_confidence: float | None
    reason: str
    risk_points: list[str]
    missing_evidence: list[str]
    prompt_version: str


@dataclass
class SendResult:
    """通知发送结果"""
    success: bool
    provider_msg_id: str | None = None
    error: str | None = None


class YoloDetector(ABC):
    @abstractmethod
    def detect(self, image_path: str) -> DetectionResult:
        """对图片进行目标检测，返回结构化结果"""
        pass


class OcrEngine(ABC):
    @abstractmethod
    def recognize_plate(self, plate_crop_path: str) -> str | None:
        """从车牌裁剪图中识别车牌号，失败返回 None"""
        pass


class RuleEvaluator(ABC):
    @abstractmethod
    def evaluate(
        self,
        detection: DetectionResult,
        ocr_result: str | None,
        intake_event: dict,
        rule: dict,
    ) -> RuleResult:
        """基于检测结果 + OCR + 接入事件 + 规则配置，判定是否满足违章规则"""
        pass


class LLMProvider(ABC):
    @abstractmethod
    def review(self, evidence_payload: dict) -> AIReviewResultData:
        """基于证据 JSON 生成 AI 初审意见"""
        pass


class NotificationProvider(ABC):
    @abstractmethod
    def send(self, to_email: str, subject: str, html_body: str) -> SendResult:
        """发送通知（邮件/短信等）"""
        pass
