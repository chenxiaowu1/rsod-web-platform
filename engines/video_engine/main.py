"""
YOLO 视频流检测引擎 — 独立 FastAPI 服务
启动: conda activate shixi_video && python main.py
"""

import glob, os, shutil, subprocess, sys, time, uuid, json
from pathlib import Path
import cv2, torch, numpy as np
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
    # COCO 80 类 — 与 Ultralytics 官方 YOLO11 预训练模型一致
    0: "person", 1: "bicycle", 2: "car", 3: "motorcycle", 4: "airplane",
    5: "bus", 6: "train", 7: "truck", 8: "boat", 9: "traffic light",
    10: "fire hydrant", 11: "stop sign", 12: "parking meter", 13: "bench",
    14: "bird", 15: "cat", 16: "dog", 17: "horse", 18: "sheep", 19: "cow",
    20: "elephant", 21: "bear", 22: "zebra", 23: "giraffe",
    24: "backpack", 25: "umbrella", 26: "handbag", 27: "tie",
    28: "suitcase", 29: "frisbee", 30: "skis", 31: "snowboard",
    32: "sports ball", 33: "kite", 34: "baseball bat", 35: "baseball glove",
    36: "skateboard", 37: "surfboard", 38: "tennis racket", 39: "bottle",
    40: "wine glass", 41: "cup", 42: "fork", 43: "knife", 44: "spoon",
    45: "bowl", 46: "banana", 47: "apple", 48: "sandwich", 49: "orange",
    50: "broccoli", 51: "carrot", 52: "hot dog", 53: "pizza", 54: "donut",
    55: "cake", 56: "chair", 57: "couch", 58: "potted plant", 59: "bed",
    60: "dining table", 61: "toilet", 62: "tv", 63: "laptop", 64: "mouse",
    65: "remote", 66: "keyboard", 67: "cell phone", 68: "microwave",
    69: "oven", 70: "toaster", 71: "sink", 72: "refrigerator", 73: "book",
    74: "clock", 75: "vase", 76: "scissors", 77: "teddy bear",
    78: "hair drier", 79: "toothbrush",
}


def find_ffmpeg_bin():
    ffmpeg_bin = shutil.which("ffmpeg")
    if ffmpeg_bin:
        return ffmpeg_bin

    local_app_data = os.environ.get("LOCALAPPDATA", "")
    program_files = os.environ.get("ProgramFiles", "")
    program_files_x86 = os.environ.get("ProgramFiles(x86)", "")
    patterns = [
        os.path.join(local_app_data, "Microsoft", "WinGet", "Links", "ffmpeg.exe"),
        os.path.join(local_app_data, "Microsoft", "WinGet", "Packages", "*FFmpeg*", "**", "ffmpeg.exe"),
        os.path.join(program_files, "ffmpeg", "**", "ffmpeg.exe"),
        os.path.join(program_files_x86, "ffmpeg", "**", "ffmpeg.exe"),
    ]
    for pattern in patterns:
        if pattern:
            matches = glob.glob(pattern, recursive=True)
            if matches:
                return matches[0]
    return ""


def transcode_to_browser_mp4(source_path: str, target_path: str):
    ffmpeg_bin = find_ffmpeg_bin()
    if not ffmpeg_bin:
        if source_path != target_path and os.path.exists(source_path):
            os.replace(source_path, target_path)
        return False

    command = [
        ffmpeg_bin,
        "-y",
        "-i",
        source_path,
        "-an",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-preset",
        "veryfast",
        "-movflags",
        "+faststart",
        target_path,
    ]
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "ffmpeg transcode failed").strip()
        raise RuntimeError(detail)

    if source_path != target_path and os.path.exists(source_path):
        os.remove(source_path)
    return True


def resolve_output_file(video_id: str):
    direct_path = os.path.join(OUTPUT_DIR, video_id, "annotated.mp4")
    if os.path.exists(direct_path):
        return direct_path

    matches = glob.glob(os.path.join(OUTPUT_DIR, "*", video_id, "annotated.mp4"))
    if matches:
        return matches[0]
    return ""


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
        vid = uuid.uuid4().hex
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        vid_dir = os.path.join(output_dir or OUTPUT_DIR, vid)
        os.makedirs(vid_dir, exist_ok=True)
        out_path = os.path.join(vid_dir, "annotated.mp4")
        raw_out_path = os.path.join(vid_dir, "annotated_raw.mp4")
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(raw_out_path, fourcc, fps, (w, h))
        if not writer.isOpened():
            raise RuntimeError("failed to create annotated video writer")

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
        transcode_to_browser_mp4(raw_out_path, out_path)

        dt = round(time.time() - t0, 3)
        return {
            "video_id": vid,
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
    try:
        result = engine.detect_video(video_path, model_key, conf_threshold, OUTPUT_DIR)
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


@app.post("/detect-frame")
async def detect_frame(data: dict):
    """实时帧检测 — 接收 base64 图片 + model_key，返回检测结果。"""
    import base64

    # ── 输入校验 ──
    if "image" not in data or not data["image"]:
        raise HTTPException(400, "缺少 image 字段（base64 图片数据）")
    model_key = data.get("model_key", "yolo11m")
    if model_key not in MODEL_REGISTRY:
        raise HTTPException(400, f"无效模型: {model_key}，可选: {list(MODEL_REGISTRY.keys())}")
    conf = float(data.get("conf_threshold", 0.25))

    # ── 模型加载 ──
    try:
        engine._ensure(model_key)
    except FileNotFoundError as e:
        raise HTTPException(503, f"模型权重文件未找到: {e}")
    except Exception as e:
        raise HTTPException(503, f"模型加载失败: {e}")

    # ── 图片解码 ──
    try:
        img_bytes = base64.b64decode(data["image"])
    except Exception:
        raise HTTPException(400, "base64 解码失败，请检查图片数据")

    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(400, "无法解码图片（可能不是有效的 JPEG/PNG 帧数据）")

    # ── 推理 ──
    try:
        results = engine.model(img, conf=conf, verbose=False)
    except Exception as e:
        raise HTTPException(500, f"推理失败: {e}")

    boxes = []
    for r in results:
        if r.boxes is None:
            continue
        for b in r.boxes:
            xyxy = b.xyxy.cpu().numpy()[0]
            cls_id = int(b.cls.cpu().numpy()[0])
            boxes.append({
                "x1": float(xyxy[0]), "y1": float(xyxy[1]),
                "x2": float(xyxy[2]), "y2": float(xyxy[3]),
                "class_id": cls_id,
                "class_name": CLASS_NAMES.get(cls_id, f"cls_{cls_id}"),
                "confidence": float(b.conf.cpu().numpy()[0]),
            })
    return {"boxes": boxes, "total_objects": len(boxes)}


@app.post("/camera-save")
async def camera_save(data: dict):
    """摄像头会话结束后，将收集的帧列表合成为检测结果视频。"""
    import base64
    frames_base64 = data.get("frames", [])  # ["base64...", ...]
    model_key = data.get("model_key", "yolo11m")
    conf = float(data.get("conf_threshold", 0.25))
    fps = int(data.get("fps", 10))

    if not frames_base64 or len(frames_base64) < 1:
        raise HTTPException(400, "至少需要 1 帧")

    engine._ensure(model_key)
    vid = uuid.uuid4().hex
    vid_dir = os.path.join(OUTPUT_DIR, vid)
    os.makedirs(vid_dir, exist_ok=True)
    out_path = os.path.join(vid_dir, "annotated.mp4")
    raw_out_path = os.path.join(vid_dir, "annotated_raw.mp4")

    total_objects = 0
    first_shape = None

    try:
        # 第一帧确定视频尺寸
        img_bytes = base64.b64decode(frames_base64[0])
        nparr = np.frombuffer(img_bytes, np.uint8)
        first_frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if first_frame is None:
            raise HTTPException(400, "第一帧无法解码")
        h, w = first_frame.shape[:2]
        first_shape = (w, h)
    except Exception as e:
        raise HTTPException(400, f"解码失败: {e}")

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(raw_out_path, fourcc, fps, first_shape)
    if not writer.isOpened():
        raise HTTPException(500, "failed to create camera annotated video writer")

    t0 = time.time()
    frame_count = 0
    for b64_frame in frames_base64:
        try:
            frame_count += 1
            img_bytes = base64.b64decode(b64_frame)
            nparr = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is None:
                continue
            if frame.shape[1] != first_shape[0] or frame.shape[0] != first_shape[1]:
                frame = cv2.resize(frame, first_shape)

            results = engine.model(frame, conf=conf, verbose=False)
            annotated = results[0].plot()
            writer.write(annotated)

            for r in results:
                if r.boxes is None:
                    continue
                total_objects += len(r.boxes)
        except Exception:
            continue

    writer.release()
    transcode_to_browser_mp4(raw_out_path, out_path)
    dt = round(time.time() - t0, 3)

    return {
        "video_id": vid,
        "total_frames": frame_count,
        "total_objects": total_objects,
        "detection_time": dt,
        "fps_original": fps,
        "output_video": out_path,
        "model_name": MODEL_REGISTRY[model_key]["name"],
    }


@app.get("/download/{video_id}")
async def download_video(video_id: str):
    # 精确查找 video_id 对应的输出目录
    vid_dir = os.path.join(OUTPUT_DIR, video_id)
    fp = os.path.join(vid_dir, "annotated.mp4")
    if os.path.exists(fp):
        return FileResponse(fp, media_type="video/mp4",
                            filename=f"detected_{video_id[:8]}.mp4")
    # 兼容旧格式：扫一遍输出目录（旧数据迁移用）
    for d in os.listdir(OUTPUT_DIR):
        fp = os.path.join(OUTPUT_DIR, d, "annotated.mp4")
        if os.path.exists(fp):
            return FileResponse(fp, media_type="video/mp4",
                                filename=f"detected_{video_id[:8]}.mp4")
    raise HTTPException(404, "视频不存在")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
