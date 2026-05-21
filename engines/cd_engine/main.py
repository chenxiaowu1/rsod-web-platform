"""
BAN 变化检测引擎 — 独立 FastAPI 服务
启动: conda activate shixi_cd && python main.py
"""

import os, sys, time, uuid
from pathlib import Path
from typing import Tuple, List
import cv2, numpy as np
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
import uvicorn

# 加载 Open-CD
OPENCD_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "open-cd"))
sys.path.insert(0, OPENCD_PATH)

from opencd.apis import OpenCDInferencer

BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

MODEL_REGISTRY = {
    "ban-b0": {
        "config": "configs/ban/ban_vit-b32-georsclip_mit-b0_512x512_40k_levircd.py",
        "weights": os.path.join(BACKEND, "app/models/change_detection/ban_vit-b32-georsclip_mit-b0_512x512_40k_levircd.pth"),
        "name": "BAN-B0", "display": "BAN-B0 · 快速",
        "desc": "ViT-B/32 + mit-b0，最轻量",
    },
    "ban-l0": {
        "config": "configs/ban/ban_vit-l14-clip_mit-b0_512x512_40k_levircd.py",
        "weights": os.path.join(BACKEND, "app/models/change_detection/ban_vit-l14-clip_mit-b0_512x512_40k_levircd.pth"),
        "name": "BAN-L0", "display": "BAN-L0 · 均衡",
        "desc": "ViT-L/14 + mit-b0，速度与精度均衡",
    },
    "ban-l1": {
        "config": "configs/ban/ban_vit-l14-clip_mit-b1_512x512_40k_levircd.py",
        "weights": os.path.join(BACKEND, "app/models/change_detection/ban_vit-l14-clip_mit-b1_512x512_40k_levircd.pth"),
        "name": "BAN-L1", "display": "BAN-L1 · 精准",
        "desc": "ViT-L/14 + mit-b1，精度最高",
    },
}


class ChangeDetectionEngine:
    def __init__(self):
        self.inferencers = {}
        self.current_key = None

    def _ensure(self, key):
        if key not in MODEL_REGISTRY:
            raise ValueError(f"未知模型: {key}")
        if key in self.inferencers:
            self.current_key = key
            return
        cfg = MODEL_REGISTRY[key]
        config_path = os.path.join(OPENCD_PATH, cfg["config"])
        self.inferencers[key] = OpenCDInferencer(
            model=config_path,
            weights=cfg["weights"],
            classes=('unchanged', 'changed'),
            palette=[[0, 0, 0], [255, 255, 255]],
        )
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

    def detect(self, key, img_a_path, img_b_path, out_dir):
        t0 = time.time()
        self._ensure(key)

        inferencer = self.inferencers[key]
        inferencer([[img_a_path, img_b_path]], show=False, out_dir=out_dir)

        pred_dir = os.path.join(out_dir, "pred")
        mask_files = os.listdir(pred_dir) if os.path.exists(pred_dir) else []
        mask_path = os.path.join(pred_dir, mask_files[0]) if mask_files else None

        change_ratio = 0.0
        if mask_path and os.path.exists(mask_path):
            mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
            if mask is not None:
                change_ratio = float((mask > 0).sum() / mask.size)

        dt = round(time.time() - t0, 3)
        return {"change_ratio": round(change_ratio, 4), "detection_time": dt,
                "model_name": MODEL_REGISTRY[key]["name"]}


engine = ChangeDetectionEngine()
app = FastAPI(title="RSOD Change Detection Engine", version="1.0")
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
TEMP_DIR = os.path.join(os.path.dirname(__file__), "temp")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)


async def save_file(file: UploadFile) -> Tuple[str, str]:
    ext = Path(file.filename).suffix if file.filename else ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(await file.read())
    return filepath, filename


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/models")
async def get_models():
    return {"data": engine.get_models()}


@app.post("/model/switch")
async def switch_model(data: dict):
    return engine.switch_model(data.get("model_key", ""))


@app.post("/detect/single")
async def detect_single(
    file_a: UploadFile = File(...),
    file_b: UploadFile = File(...),
    model_key: str = Form("ban-b0"),
):
    path_a, _ = await save_file(file_a)
    path_b, _ = await save_file(file_b)
    out_dir = os.path.join(TEMP_DIR, uuid.uuid4().hex)
    os.makedirs(out_dir, exist_ok=True)
    try:
        result = engine.detect(model_key, path_a, path_b, out_dir)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/detect/batch")
async def detect_batch(
    files_a: List[UploadFile] = File(...),
    files_b: List[UploadFile] = File(...),
    model_key: str = Form("ban-b0"),
):
    if len(files_a) != len(files_b):
        raise HTTPException(status_code=400, detail="两个时相图片数量不一致")

    results = []
    for fa, fb in zip(files_a, files_b):
        path_a, fn_a = await save_file(fa)
        path_b, fn_b = await save_file(fb)
        out_dir = os.path.join(TEMP_DIR, uuid.uuid4().hex)
        os.makedirs(out_dir, exist_ok=True)
        try:
            r = engine.detect(model_key, path_a, path_b, out_dir)
            r["filename_a"] = fn_a
            r["filename_b"] = fn_b
            results.append(r)
        except Exception:
            results.append({"error": True, "filename_a": fa.filename, "filename_b": fb.filename})
    return {"results": results, "total": len(results)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
