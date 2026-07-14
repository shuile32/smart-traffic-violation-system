from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from pathlib import Path
from typing import Protocol

from ai_service.traffic_ai.config import ensure_runtime_environment

CHINESE_PLATE_PROVINCES = frozenset(
    "京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领警学港澳"
)
MAINLAND_PLATE_PROVINCES = frozenset(
    "京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼"
)
PLATE_LETTERS = frozenset("ABCDEFGHJKLMNPQRSTUVWXYZ")
PLATE_SUFFIX_CHARACTERS = PLATE_LETTERS | frozenset("0123456789")
PLATE_SEPARATOR_CHARACTERS = frozenset({" ", "-", "_", ".", "·", "•"})


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
    cleaned = "".join(ch for ch in text.strip() if ch not in PLATE_SEPARATOR_CHARACTERS)
    cleaned = cleaned.upper()
    return cleaned or None


def normalize_valid_plate_text(text: str | None) -> str | None:
    """Return a normalized mainland civilian plate, or None when OCR is unreliable."""
    normalized = normalize_plate_text(text)
    if not normalized or len(normalized) not in {7, 8}:
        return None
    if normalized[0] not in MAINLAND_PLATE_PROVINCES:
        return None
    if normalized[1] not in PLATE_LETTERS:
        return None

    # I and O are not used as plate letters, so OCR occurrences in the suffix
    # can only represent the digits 1 and 0.
    suffix = normalized[2:].translate(str.maketrans({"I": "1", "O": "0"}))
    if any(character not in PLATE_SUFFIX_CHARACTERS for character in suffix):
        return None
    return normalized[:2] + suffix


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
        raw_candidates: list[str] = []
        for ocr_input in _plate_ocr_inputs(image_path):
            raw = self._ocr.ocr(ocr_input)
            candidates = _extract_ocr_texts(raw)
            raw_candidates.extend(candidates)
            for candidate in [*candidates, "".join(candidates)]:
                plate_text = normalize_valid_plate_text(candidate)
                if plate_text:
                    return OcrResult(text=plate_text, engine="paddleocr", status="ok")

        status = "invalid_format" if raw_candidates else "not_detected"
        return OcrResult(text=None, engine="paddleocr", status=status)


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


def _plate_ocr_inputs(image_path: Path) -> list[object]:
    """Run OCR on the original crop and one enlarged, sharpened variant."""
    from PIL import Image, ImageEnhance
    import numpy as np

    with Image.open(image_path) as source:
        image = source.convert("RGB")
        scale = max(1, min(12, ceil(96 / max(1, image.height))))
        enlarged = image.resize(
            (image.width * scale, image.height * scale),
            Image.Resampling.LANCZOS,
        )
        enhanced = ImageEnhance.Contrast(enlarged).enhance(1.5)
        enhanced = ImageEnhance.Sharpness(enhanced).enhance(2.0)
        enhanced_array = np.asarray(enhanced)

    return [str(image_path), enhanced_array]
