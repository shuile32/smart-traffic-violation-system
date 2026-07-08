"""PaddleOCR 车牌识别实现"""

from app.ai.adapters.base import OcrEngine


class PaddleOcrEngine(OcrEngine):
    def __init__(self):
        # 延迟导入避免启动时加载 PaddlePaddle
        self._ocr = None

    @property
    def ocr(self):
        if self._ocr is None:
            from paddleocr import PaddleOCR
            self._ocr = PaddleOCR(use_angle_cls=True, lang="ch")
        return self._ocr

    def recognize_plate(self, plate_crop_path: str) -> str | None:
        try:
            results = self.ocr.ocr(plate_crop_path, cls=True)
            if not results or not results[0]:
                return None
            # 取置信度最高的文本
            texts = [line[1][0] for line in results[0] if line[1][1] > 0.5]
            if texts:
                return "".join(texts).replace(" ", "").upper()
            return None
        except Exception:
            return None
