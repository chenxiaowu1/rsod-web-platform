"""
YOLO 视频流检测引擎 — 独立 FastAPI 服务
启动: conda activate shixi_video && python main.py
"""

import os, sys, time, uuid, json
from pathlib import Path
import cv2, torch
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
import uvicorn

BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_REGISTRY = {
    "yolo11n": {"path": os.path.join(BACKEND, "app/models/video/yolo11n.pt"),
                 "name": "YOLO11n", "display": "YOLO11n · 快速",
                 "desc": "2.6M 参数，帧率最高"},
    "yolo11m": {"path": os.path.join(BACKEND, "app/models/video/yolo11m.pt"),
                 "name": "YOLO11m", "display": "YOLO11m · 均衡",
                 "desc": "20.9M 参数，速度精度均衡"},
    "yolo11x": {"path": os.path.join(BACKEND, "app/models/video/yolo11x.pt"),
                 "name": "YOLO11x", "display": "YOLO11x · 精准",
                 "desc": "56.9M 参数，精度最高"},
}

CLASS_NAMES = {
    0: "person", 1: "bicycle", 2: "car", 3: "motorcycle", 4: "airplane",
    5: "bus", 6: "train", 7: "truck", 8: "boat", 9: "traffic light",
    10: "fire hydrant", 11: "stop sign", 12: "parking meter", 13: "bench",
    14: "bird", 15: "cat", 16: "dog", 17: "horse", 18: "sheep", 19: "cow",
    20: "elephant", 21: "bear", 22: "zebra", 23: "giraffe",
}


class VideoEngine:
    def __init__(self):
        self.current_key = None
        self.model = None

    def _ensure(self, key=None):
        if key is None:
            key = "yolo11m"
        if key == self.current_key and self.model is not None:
            return
        from ultralytics import YOLO
        cfg = MODEL_REGISTRY[key]
        self.model = YOLO(cfg["path"])
        self.model.to(DEVICE)
        self.current_key = key

    def get_models(self):
        return [{"key": k, "name": v["name"], "display": v["display"],
                 "desc": v["desc"], "loaded": self.current_key == k}
                for k, v in MODEL_REGISTRY.items()]

    def switch_model(self, key):
        if key not in MODEL_REGISTRY:
            return {"success": False, "message": f"未知模型: {key}"}
        self._ensure(key)
        return {"success": True, "message": f"已切换到 {MODEL_REGISTRY[key]['name']}"}

    def detect_video(self, video_path, model_key, conf=0.25, output_dir=None):
        self._ensure(model_key)
        t0 = time.time()
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        out_path = os.path.join(output_dir, "annotated.mp4")
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(out_path, fourcc, fps, (w, h))

        all_boxes = []
        frame_idx = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            results = self.model(frame, conf=conf, verbose=False)
            annotated = results[0].plot()
            writer.write(annotated)

            for box in results[0].boxes:
                xyxy = box.xyxy.cpu().numpy()[0]
                cls_id = int(box.cls.cpu().numpy()[0])
                conf_val = float(box.conf.cpu().numpy()[0])
                all_boxes.append({
                    "frame": frame_idx,
                    "x1": float(xyxy[0]), "y1": float(xyxy[1]),
                    "x2": float(xyxy[2]), "y2": float(xyxy[3]),
                    "class_id": cls_id,
                    "class_name": CLASS_NAMES.get(cls_id, f"cls_{cls_id}"),
                    "confidence": conf_val,
                })
            frame_idx += 1

        cap.release()
        writer.release()

        dt = round(time.time() - t0, 3)
        return {
            "video_id": uuid.uuid4().hex,
            "total_frames": frame_idx,
            "total_objects": len(all_boxes),
            "detection_time": dt,
            "fps_original": fps,
            "output_video": out_path,
            "boxes": all_boxes,
            "model_name": MODEL_REGISTRY[model_key]["name"],
        }


engine = VideoEngine()
app = FastAPI(title="RSOD Video Engine", version="1.0")
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "outputs")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


async def save_file(file: UploadFile) -> tuple[str, str]:
    ext = Path(file.filename).suffix or ".mp4"
    fn = f"{uuid.uuid4().hex}{ext}"
    fp = os.path.join(UPLOAD_DIR, fn)
    with open(fp, "wb") as f:
        f.write(await file.read())
    return fp, fn


@app.get("/health")
async def health():
    return {"status": "ok", "device": DEVICE}


@app.get("/models")
async def get_models():
    return {"data": engine.get_models()}


@app.post("/model/switch")
async def switch_model(data: dict):
    return engine.switch_model(data.get("model_key", ""))


@app.post("/detect")
async def detect_video(
    file: UploadFile = File(...),
    model_key: str = Form("yolo11m"),
    conf_threshold: float = Form(0.25),
):
    video_path, _ = await save_file(file)
    out_dir = os.path.join(OUTPUT_DIR, uuid.uuid4().hex)
    os.makedirs(out_dir, exist_ok=True)
    try:
        result = engine.detect_video(video_path, model_key, conf_threshold, out_dir)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "video_id": result["video_id"],
        "total_frames": result["total_frames"],
        "total_objects": result["total_objects"],
        "detection_time": result["detection_time"],
        "fps_original": result["fps_original"],
        "model_name": result["model_name"],
        "boxes": result["boxes"],
    }


@app.get("/download/{video_id}")
async def download_video(video_id: str):
    for d in os.listdir(OUTPUT_DIR):
        fp = os.path.join(OUTPUT_DIR, d, "annotated.mp4")
        if os.path.exists(fp):
            return FileResponse(fp, media_type="video/mp4",
                                filename=f"detected_{video_id[:8]}.mp4")
    raise HTTPException(404, "视频不存在")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
