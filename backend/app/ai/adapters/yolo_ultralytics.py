"""Ultralytics YOLOv8 检测器实现

第一阶段：yolov8n 预训练 COCO 模型检车辆/人
          + 独立预训练车牌检测模型框车牌
"""

from ultralytics import YOLO

from app.ai.adapters.base import YoloDetector, DetectionResult


class UltralyticsYoloDetector(YoloDetector):
    def __init__(self, vehicle_model_path: str = "yolov8n.pt", plate_model_path: str = "yolov8n-plate.pt"):
        self.vehicle_model = YOLO(vehicle_model_path)  # COCO: car/truck/bus/motorcycle/person
        self.plate_model = YOLO(plate_model_path) if plate_model_path else None  # 车牌检测
        self.model_version = "yolov8n-traffic-v1"

    def detect(self, image_path: str) -> DetectionResult:
        # 1. 车辆/行人检测
        results = self.vehicle_model(image_path)
        objects = []
        vehicle_bbox = None
        plate_bbox = None

        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                label = self.vehicle_model.names[cls_id]
                conf = float(box.conf[0])
                bbox = box.xyxy[0].tolist()
                objects.append({"label": label, "confidence": round(conf, 4), "bbox": bbox})

                # 取第一个车辆框
                if vehicle_bbox is None and label in ("car", "truck", "bus", "motorcycle"):
                    vehicle_bbox = bbox

        # 2. 车牌检测（如果有独立模型）
        if self.plate_model:
            plate_results = self.plate_model(image_path)
            for r in plate_results:
                for box in r.boxes:
                    if plate_bbox is None:
                        plate_bbox = box.xyxy[0].tolist()
                        objects.append({"label": "plate", "confidence": round(float(box.conf[0]), 4), "bbox": plate_bbox})

        # 3. 标注图路径
        annotated_path = image_path.replace(".", "_annotated.")

        return DetectionResult(
            objects=objects,
            vehicle_bbox=vehicle_bbox,
            plate_bbox=plate_bbox,
            annotated_image_path=annotated_path,
            model_version=self.model_version,
        )
