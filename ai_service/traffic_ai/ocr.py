from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from ai_service.traffic_ai.config import ensure_runtime_environment

CHINESE_PLATE_PROVINCES = frozenset(
    "京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领警学港澳"
)


@dataclass(frozen=True)
class OcrResult:
    text: str | None
    engine: str
    status: str


class OcrEngine(Protocol):
    def recognize(self, image_path: Path) -> OcrResult:
        raise NotImplementedError


def normalize_plate_text(text: str | None) -> str | None:
    if text is None:
        return None
    cleaned = "".join(ch for ch in text.strip() if ch not in {" ", "-", "_", "."})
    cleaned = cleaned.upper()
    return cleaned or None


def plate_text_has_chinese_province(text: str | None) -> bool:
    normalized = normalize_plate_text(text)
    return bool(normalized and normalized[0] in CHINESE_PLATE_PROVINCES)


class NoopOcrEngine:
    def recognize(self, image_path: Path) -> OcrResult:
        return OcrResult(text=None, engine="none", status="unavailable")


class PaddleOcrEngine:
    def __init__(self) -> None:
        ensure_runtime_environment()
        try:
            from paddleocr import PaddleOCR
        except ImportError as exc:
            raise RuntimeError("paddleocr is not installed") from exc
        self._ocr = PaddleOCR(
            lang="ch",
            device="cpu",
            enable_mkldnn=False,
            cpu_threads=4,
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
        )

    def recognize(self, image_path: Path) -> OcrResult:
        raw = self._ocr.ocr(str(image_path))
        candidates = _extract_ocr_texts(raw)
        return OcrResult(text=normalize_plate_text("".join(candidates)), engine="paddleocr", status="ok")


def create_default_ocr_engine() -> OcrEngine:
    try:
        return PaddleOcrEngine()
    except RuntimeError as exc:
        if str(exc) != "paddleocr is not installed":
            raise
        return NoopOcrEngine()


def _extract_ocr_texts(raw: object) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, dict):
        for key in ("rec_texts", "texts"):
            value = raw.get(key)
            if isinstance(value, list):
                return [str(item) for item in value if item]
        for key in ("rec_text", "text"):
            value = raw.get(key)
            if isinstance(value, str) and value:
                return [value]
        return []
    if isinstance(raw, (list, tuple)):
        if len(raw) >= 2 and isinstance(raw[1], (list, tuple)) and raw[1]:
            first = raw[1][0]
            if isinstance(first, str):
                return [first]
        texts: list[str] = []
        for item in raw:
            texts.extend(_extract_ocr_texts(item))
        return texts
    return []
