"""
YOLO 检测引擎 — 独立 FastAPI 服务
启动: conda activate shixi_det && python main.py
"""

import os, sys, time, uuid
from pathlib import Path
import cv2, torch, numpy as np
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
import uvicorn

BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
sys.path.insert(0, BACKEND)
from app.models.schemas import DetectionBox

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
GEOSPATIAL = {'.tif', '.tiff', '.geotiff', '.ntf', '.img'}
CLASS_NAMES = {
    0: "plane", 1: "ship", 2: "storage-tank", 3: "baseball-diamond",
    4: "tennis-court", 5: "basketball-court", 6: "ground-track-field",
    7: "harbor", 8: "bridge", 9: "large-vehicle", 10: "small-vehicle",
    11: "helicopter", 12: "roundabout", 13: "soccer-ball-field", 14: "swimming-pool",
}

MODEL_REGISTRY = {
    "yolo11n-obb": {"path": os.path.join(BACKEND, "app/models/detection/yolo11n-obb.pt"),
                     "name": "YOLO11n-OBB", "display": "YOLO11n-OBB · 快速",
                     "desc": "2.7M 参数，速度最快"},
    "yolo11m-obb": {"path": os.path.join(BACKEND, "app/models/detection/yolo11m-obb.pt"),
                     "name": "YOLO11m-OBB", "display": "YOLO11m-OBB · 均衡",
                     "desc": "20.9M 参数，速度精度均衡"},
    "yolo11x-obb": {"path": os.path.join(BACKEND, "app/models/detection/yolo11x-obb.pt"),
                     "name": "YOLO11x-OBB", "display": "YOLO11x-OBB · 精准",
                     "desc": "58.8M 参数，精度最高"},
}


class DetectionEngine:
    def __init__(self):
        self.sahi_model = None
        self.current_key = None

    def _load_model(self, key=None):
        if key is None:
            key = "yolo11m-obb"
        cfg = MODEL_REGISTRY[key]
        if not os.path.exists(cfg["path"]):
            raise FileNotFoundError(f"权重不存在: {cfg['path']}")

        from sahi import AutoDetectionModel
        self.sahi_model = AutoDetectionModel.from_pretrained(
            model_type="yolov8", model_path=cfg["path"],
            confidence_threshold=0.25, device=DEVICE)
        self.current_key = key

    def ensure_loaded(self, key=None):
        if key and key != self.current_key:
            self._load_model(key)
        elif self.sahi_model is None:
            self._load_model(key)

    def get_models(self):
        return [{"key": k, "name": v["name"], "display": v["display"],
                 "desc": v["desc"], "loaded": self.current_key == k}
                for k, v in MODEL_REGISTRY.items()]

    def switch_model(self, key):
        if key not in MODEL_REGISTRY:
            return {"success": False, "message": f"未知模型: {key}"}
        self._load_model(key)
        return {"success": True, "message": f"已切换到 {MODEL_REGISTRY[key]['name']}"}

    def _load_image(self, path):
        ext = os.path.splitext(path)[1].lower()
        if ext not in GEOSPATIAL:
            bgr = cv2.imread(path)
            if bgr is None:
                raise ValueError(f"无法读取图片或文件不存在: {path}")
            return path, os.path.basename(path), cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

        import rasterio
        with rasterio.open(path) as src:
            n = src.count
            if n >= 3: bands = src.read([1, 2, 3])
            elif n == 2: bands = src.read([1, 2]); bands = np.concatenate([bands, bands[-1:]], axis=0)
            else: band = src.read(1); bands = np.stack([band, band, band], axis=0)
            img = np.transpose(bands, (1, 2, 0))
            if img.dtype != np.uint8:
                img = ((img - img.min()) / (img.max() - img.min() + 1e-8) * 255).astype(np.uint8)
        preview_name = f"{os.path.splitext(os.path.basename(path))[0]}_{uuid.uuid4().hex[:6]}.png"
        preview_path = os.path.join(UPLOAD_DIR, preview_name)
        cv2.imwrite(preview_path, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
        return preview_path, preview_name, img

    def _extract_boxes(self, preds, w, h):
        """统一提取 xyxy boxes"""
        boxes = []
        if hasattr(preds, 'obb') and preds.obb is not None:
            polys = preds.obb.xyxyxyxy.cpu().numpy()
            confs = preds.obb.conf.cpu().numpy()
            cls_ids = preds.obb.cls.cpu().numpy().astype(int)
            for i, poly in enumerate(polys):
                boxes.append(DetectionBox(
                    x1=float(max(0, poly[:, 0].min())), y1=float(max(0, poly[:, 1].min())),
                    x2=float(min(w, poly[:, 0].max())), y2=float(min(h, poly[:, 1].max())),
                    confidence=float(confs[i]), class_id=int(cls_ids[i]),
                    class_name=CLASS_NAMES.get(int(cls_ids[i]), "unknown")))
        elif hasattr(preds, 'boxes') and preds.boxes is not None:
            xyxy = preds.boxes.xyxy.cpu().numpy()
            cls_ids = preds.boxes.cls.cpu().numpy().astype(int)
            confs = preds.boxes.conf.cpu().numpy()
            for i, box in enumerate(xyxy):
                boxes.append(DetectionBox(
                    x1=float(max(0, box[0])), y1=float(max(0, box[1])),
                    x2=float(min(w, box[2])), y2=float(min(h, box[3])),
                    confidence=float(confs[i]), class_id=int(cls_ids[i]),
                    class_name=CLASS_NAMES.get(int(cls_ids[i]), "unknown")))
        elif isinstance(preds, list):
            # SAHI object_prediction_list
            for p in preds:
                boxes.append(DetectionBox(
                    x1=float(max(0, p.bbox.minx)), y1=float(max(0, p.bbox.miny)),
                    x2=float(min(w, p.bbox.maxx)), y2=float(min(h, p.bbox.maxy)),
                    confidence=float(p.score.value), class_id=int(p.category.id),
                    class_name=CLASS_NAMES.get(int(p.category.id), p.category.name)))
        return boxes

    def detect(self, image_path, model_key, conf=0.5, iou=0.45, use_sahi=False):
        self.ensure_loaded(model_key)
        t0 = time.time()

        detect_path, preview_filename, orig_img = self._load_image(image_path)
        h, w = orig_img.shape[:2]

        if use_sahi:
            from sahi.predict import get_sliced_prediction
            result = get_sliced_prediction(
                detect_path, self.sahi_model, slice_height=640, slice_width=640,
                overlap_height_ratio=0.2, overlap_width_ratio=0.2,
                postprocess_match_threshold=iou, postprocess_class_agnostic=False)
            preds = result.object_prediction_list
        else:
            raw = self.sahi_model.model.predict(detect_path, conf=conf, iou=iou, verbose=False)
            preds = raw[0]

        boxes = self._extract_boxes(preds, w, h)

        return {"detection_id": uuid.uuid4().hex,
                "boxes": [b.model_dump() for b in boxes],
                "total_objects": len(boxes),
                "detection_time": round(time.time() - t0, 3),
                "model_name": MODEL_REGISTRY[model_key]["name"]}


engine = DetectionEngine()
app = FastAPI(title="RSOD Detection Engine", version="1.0")
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


async def save_file(file: UploadFile) -> str:
    ext = Path(file.filename).suffix if file.filename else ".jpg"
    fn = f"{uuid.uuid4().hex}{ext}"
    with open(os.path.join(UPLOAD_DIR, fn), "wb") as f:
        f.write(await file.read())
    return os.path.join(UPLOAD_DIR, fn), fn


@app.get("/health")
async def health():
    return {"status": "ok", "device": DEVICE}


@app.get("/models")
async def get_models():
    return {"data": engine.get_models()}


@app.post("/model/switch")
async def switch_model(data: dict):
    return engine.switch_model(data.get("model_key", ""))


@app.post("/detect/single")
async def detect_single(
    file: UploadFile = File(...),
    model_name: str = Form("yolo11m-obb"),
    conf_threshold: float = Form(0.5),
    iou_threshold: float = Form(0.45),
    use_sahi: bool = Form(False),
):
    filepath, _ = await save_file(file)
    result = engine.detect(filepath, model_name, conf_threshold, iou_threshold, use_sahi)
    return result


@app.post("/detect/batch")
async def detect_batch(
    files: list[UploadFile] = File(...),
    model_name: str = Form("yolo11m-obb"),
    conf_threshold: float = Form(0.5),
    iou_threshold: float = Form(0.45),
    use_sahi: bool = Form(False),
):
    results = []
    for file in files:
        fp, fn = await save_file(file)
        try:
            r = engine.detect(fp, model_name, conf_threshold, iou_threshold, use_sahi)
            r["filename"] = fn
            results.append(r)
        except Exception as e:
            results.append({"error": True, "message": str(e), "filename": file.filename})
    return {"results": results, "total": len(results)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
