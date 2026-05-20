import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from ultralytics import YOLO
from PIL import Image
import cv2
from app.config import settings
from app.models.schemas import DetectionBox, DetectionResult
from app.utils.file_utils import get_file_url

# 模型注册表
MODEL_REGISTRY = {
    "yolo11n-obb": {
        "path": "app/models/yolo11n-obb.pt",
        "name": "YOLO11n-OBB",
        "display": "Nano · 快速",
        "desc": "最小模型 (2.7M)，速度最快，适合快速预览、低配设备",
        "icon": "n",
    },
    "yolo11m-obb": {
        "path": "app/models/yolo11m-obb.pt",
        "name": "YOLO11m-OBB",
        "display": "Medium · 均衡",
        "desc": "中型模型 (20.9M)，速度与精度均衡，适合日常检测",
        "icon": "m",
    },
    "yolo11x-obb": {
        "path": "app/models/yolo11x-obb.pt",
        "name": "YOLO11x-OBB",
        "display": "XLarge · 精准",
        "desc": "最大模型 (58.8M)，精度最高，适合高精度分析场景",
        "icon": "x",
    },
}


class DetectionService:
    def __init__(self):
        self.model = None
        self.current_model_key = None
        self.class_names = {}
        self._init_class_names()

    def _init_class_names(self):
        self.class_names = {
            0: "plane", 1: "ship", 2: "storage-tank",
            3: "baseball-diamond", 4: "tennis-court", 5: "basketball-court",
            6: "ground-track-field", 7: "harbor", 8: "bridge",
            9: "large-vehicle", 10: "small-vehicle", 11: "helicopter",
            12: "roundabout", 13: "soccer-ball-field", 14: "swimming-pool",
        }

    def _load_model(self, model_key: str = None):
        if model_key is None:
            model_key = settings.DEFAULT_MODEL
        cfg = MODEL_REGISTRY.get(model_key)
        if not cfg:
            raise ValueError(f"未知模型: {model_key}")
        if not os.path.exists(cfg["path"]):
            raise FileNotFoundError(f"模型文件不存在: {cfg['path']}")
        # 释放旧模型
        if self.model is not None:
            del self.model
        self.model = YOLO(cfg["path"])
        self.current_model_key = model_key

    def ensure_model_loaded(self):
        if self.model is None:
            self._load_model()

    def switch_model(self, model_key: str) -> dict:
        if model_key not in MODEL_REGISTRY:
            return {"success": False, "message": f"未知模型: {model_key}"}
        try:
            self._load_model(model_key)
            cfg = MODEL_REGISTRY[model_key]
            return {"success": True, "message": f"已切换到 {cfg['name']}", "model": cfg["name"]}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def get_models(self) -> list[dict]:
        return [
            {
                "key": key,
                "name": cfg["name"],
                "display": cfg["display"],
                "desc": cfg["desc"],
                "loaded": self.current_model_key == key,
            }
            for key, cfg in MODEL_REGISTRY.items()
        ]

    def _extract_boxes(self, results):
        boxes = []
        for result in results:
            obb = result.obb
            if obb is not None:
                for i in range(len(obb.cls)):
                    x1, y1, x2, y2 = obb.xyxy[i].tolist()
                    confidence = float(obb.conf[i])
                    class_id = int(obb.cls[i])
                    class_name = self.class_names.get(class_id, f"class_{class_id}")
                    boxes.append(DetectionBox(
                        x1=x1, y1=y1, x2=x2, y2=y2,
                        confidence=confidence, class_id=class_id, class_name=class_name,
                    ))
        return boxes

    def detect_single_image(self, image_path: str, model_name: str = "yolo11x-obb") -> DetectionResult:
        self.ensure_model_loaded()
        start_time = time.time()
        detection_id = str(uuid.uuid4())

        results = self.model.predict(
            source=image_path,
            conf=settings.CONFIDENCE_THRESHOLD,
            iou=settings.IOU_THRESHOLD,
            save=False,
        )
        boxes = self._extract_boxes(results)

        result_filename = f"result_{uuid.uuid4().hex}.jpg"
        result_path = os.path.join(settings.RESULT_DIR, result_filename)
        annotated_image = results[0].plot()
        cv2.imwrite(result_path, cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR))

        return DetectionResult(
            detection_id=detection_id,
            image_url=get_file_url(os.path.basename(image_path), "static/uploads"),
            result_image_url=get_file_url(result_filename, "static/results"),
            boxes=boxes,
            total_objects=len(boxes),
            detection_time=round(time.time() - start_time, 3),
            model_name=self.current_model_key or model_name,
            created_at=datetime.now(),
        )

    def detect_batch_images(self, image_paths: list[str], model_name: str = "yolo11x-obb") -> list[dict]:
        self.ensure_model_loaded()
        results_list = []
        for img_path in image_paths:
            t0 = time.time()
            filename = os.path.basename(img_path)
            results = self.model.predict(
                source=img_path,
                conf=settings.CONFIDENCE_THRESHOLD,
                iou=settings.IOU_THRESHOLD,
                save=False,
            )
            boxes = self._extract_boxes(results)
            result_filename = f"result_{uuid.uuid4().hex}.jpg"
            result_path = os.path.join(settings.RESULT_DIR, result_filename)
            annotated_image = results[0].plot()
            cv2.imwrite(result_path, cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR))
            results_list.append({
                "filename": filename,
                "image_url": get_file_url(filename, "static/uploads"),
                "result_image_url": get_file_url(result_filename, "static/results"),
                "total_objects": len(boxes),
                "detection_time": round(time.time() - t0, 3),
                "boxes": [b.model_dump() for b in boxes],
            })
        return results_list


detection_service = DetectionService()
