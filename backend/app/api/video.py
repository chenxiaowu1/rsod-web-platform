import os, time, httpx
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import StreamingResponse
from app.config import settings
from app.services.history_service import (
    save_video_record, list_video_records, get_video_record,
    get_all_video_records, delete_video_record,
)
from app.utils.dependencies import get_current_user
from app.models.db_models import User

router = APIRouter(prefix="/video", tags=["video"])
ENGINE = settings.VIDEO_ENGINE_URL
ALLOWED = {'.mp4', '.avi', '.mov', '.mkv', '.webm'}


def _valid(name):
    if os.path.splitext(name)[1].lower() not in ALLOWED:
        raise HTTPException(400, f"不支持: {name}, 支持 mp4/avi/mov/mkv")


@router.get("/models")
async def get_models():
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{ENGINE}/models")
    return r.json()


@router.post("/model/switch")
async def switch_model(data: dict):
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{ENGINE}/model/switch", json=data)
    return r.json()


@router.post("/detect")
async def detect_video(
    file: UploadFile = File(...),
    model_key: str = Form("yolo11m"),
    conf_threshold: float = Form(0.25),
    current_user: User = Depends(get_current_user),
):
    _valid(file.filename)
    content = await file.read()
    fd = {"file": (file.filename, content, file.content_type or "video/mp4")}
    data = {"model_key": model_key, "conf_threshold": conf_threshold}

    async with httpx.AsyncClient(timeout=600) as c:
        r = await c.post(f"{ENGINE}/detect", files=fd, data=data)
    if r.status_code != 200:
        raise HTTPException(r.status_code, detail=f"视频引擎错误: {r.text}")
    raw = r.json()

    save_video_record(raw["video_id"], current_user.id, current_user.username,
                      file.filename, raw["total_frames"], raw["total_objects"],
                      raw["detection_time"], raw["fps_original"], raw["model_name"])
    return raw


@router.get("/download/{video_id}")
async def download_video(video_id: str):
    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.get(f"{ENGINE}/download/{video_id}")
    if r.status_code != 200:
        raise HTTPException(404, "视频不存在")
    content = await r.aread()
    return StreamingResponse(
        iter([content]), media_type="video/mp4",
        headers={"Content-Disposition": f'attachment; filename="detected_{video_id[:8]}.mp4"'},
    )


# ── 历史 ──────────────────────────────────────

@router.get("/history")
async def get_history(
    page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    records, total = list_video_records(page, page_size, current_user.username)
    return {"success": True, "message": "获取成功",
            "data": records, "total": total, "page": page, "page_size": page_size}


@router.get("/history/{record_id}")
async def get_history_detail(record_id: str):
    r = get_video_record(record_id)
    if not r:
        raise HTTPException(404, "记录不存在")
    return {"success": True, "data": r}


@router.delete("/history/{record_id}")
async def delete_record(record_id: str):
    if not delete_video_record(record_id):
        raise HTTPException(404, "记录不存在")
    return {"success": True, "message": "删除成功"}


# ── 统计 ──────────────────────────────────────

@router.get("/statistics")
async def get_statistics(current_user: User = Depends(get_current_user)):
    records = get_all_video_records(username=current_user.username)
    if not records:
        return {"success": True, "message": "暂无数据", "data": None}

    total_videos = len(records)
    total_frames = sum(r.get("total_frames", 0) for r in records)
    total_objects = sum(r.get("total_objects", 0) for r in records)
    total_time = sum(r.get("detection_time", 0) for r in records)

    daily, models = {}, {}
    for r in records:
        d = r.get("created_at", "")[:10]
        daily[d] = daily.get(d, 0) + 1
        m = r.get("model_name", "")
        models[m] = models.get(m, 0) + 1

    return {
        "success": True, "message": "统计完成",
        "data": {
            "total_videos": total_videos,
            "total_frames": total_frames,
            "total_objects": total_objects,
            "avg_frames": round(total_frames / total_videos, 1) if total_videos else 0,
            "avg_time": round(total_time / total_videos, 1) if total_videos else 0,
            "daily_trend": [{"date": d, "count": c} for d, c in sorted(daily.items())],
            "model_usage": [{"model": m, "count": c} for m, c in sorted(models.items(), key=lambda x: -x[1])],
        },
    }
