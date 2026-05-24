import glob, time, httpx, logging
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from app.config import settings
from app.utils.validation import CheckContext, DataValidator
from app.utils.paths import Paths
from app.services.history_service import (
    save_video_record, list_video_records, get_video_record,
    get_all_video_records, delete_video_record,
)
from app.utils.dependencies import get_current_user
from app.models.db_models import User

logger = logging.getLogger("rsod.video")
router = APIRouter(prefix="/video", tags=["video"])
ENGINE = settings.VIDEO_ENGINE_URL
ALLOWED_VIDEO = {'.mp4', '.avi', '.mov', '.mkv', '.webm'}
VIDEO_OUTPUT_DIR = Paths.engines() / "video_engine" / "outputs"


def resolve_video_file(video_id: str):
    direct_path = VIDEO_OUTPUT_DIR / video_id / "annotated.mp4"
    if direct_path.exists():
        return direct_path

    matches = glob.glob(str(VIDEO_OUTPUT_DIR / "*" / video_id / "annotated.mp4"))
    if matches:
        return Path(matches[0])
    return None


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
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_VIDEO:
        raise HTTPException(400, f"不支持的视频格式: {ext}, 支持 mp4/avi/mov/mkv")

    logger.info("开始视频检测: %s, 模型: %s", file.filename, model_key)

    content = await file.read()
    fd = {"file": (file.filename, content, file.content_type or "video/mp4")}
    data = {"model_key": model_key, "conf_threshold": conf_threshold}

    async with httpx.AsyncClient(timeout=600) as c:
        r = await c.post(f"{ENGINE}/detect", files=fd, data=data)
    if r.status_code != 200:
        logger.error("视频引擎返回 %d: %s", r.status_code, r.text[:200])
        raise HTTPException(502, "视频检测服务暂时不可用，请稍后重试")
    raw = r.json()

    save_video_record(raw["video_id"], current_user.id, current_user.username,
                      file.filename, raw["total_frames"], raw["total_objects"],
                      raw["detection_time"], raw["fps_original"], raw["model_name"],
                      source_type="video",
                      result_url=f"/api/video/download/{raw['video_id']}")

    logger.info("视频检测完成: %d 帧, %d 个目标, 耗时 %.2fs",
                raw["total_frames"], raw["total_objects"], raw["detection_time"])
    return raw


@router.post("/detect-frame")
async def detect_frame(data: dict):
    """实时帧检测代理 — 透传上游错误详情。"""
    async with httpx.AsyncClient(timeout=30) as c:
        try:
            r = await c.post(f"{ENGINE}/detect-frame", json=data)
        except Exception as e:
            logger.error("帧检测引擎连接失败: %s", e)
            raise HTTPException(502, f"帧检测引擎不可达: {ENGINE}")
    if r.status_code != 200:
        detail = "帧检测失败"
        try:
            detail = r.json().get("detail", r.text[:200])
        except Exception:
            detail = r.text[:200]
        logger.error("帧检测引擎返回 %d: %s", r.status_code, detail)
        raise HTTPException(502, detail)
    return r.json()


@router.post("/camera-save")
async def camera_session_save(
    data: dict,
    current_user: User = Depends(get_current_user),
):
    """摄像头检测会话结束 — 提交帧列表，合成视频并保存历史记录。"""
    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.post(f"{ENGINE}/camera-save", json=data)
    if r.status_code != 200:
        detail = "摄像头会话保存失败"
        try:
            detail = r.json().get("detail", r.text[:200])
        except Exception:
            detail = r.text[:200]
        logger.error("摄像头保存引擎返回 %d: %s", r.status_code, detail)
        raise HTTPException(502, detail)
    raw = r.json()

    filename = data.get("filename", f"camera_{raw['video_id'][:8]}")
    save_video_record(
        raw["video_id"], current_user.id, current_user.username,
        filename, raw["total_frames"], raw["total_objects"],
        raw["detection_time"], raw["fps_original"], raw["model_name"],
        source_type="camera",
        result_url=f"/api/video/download/{raw['video_id']}",
    )

    logger.info("摄像头会话已保存: video_id=%s, %d 帧, %d 目标",
                raw["video_id"], raw["total_frames"], raw["total_objects"])
    return {"success": True, "data": raw}


@router.get("/download/{video_id}")
async def download_video(video_id: str):
    """代理视频引擎的下载/播放流 — 支持 <video> 标签直接播放。"""
    async def stream_bytes():
        async with httpx.AsyncClient(timeout=120) as c:
            async with c.stream("GET", f"{ENGINE}/download/{video_id}") as r:
                if r.status_code != 200:
                    raise HTTPException(404, "视频不存在")
                async for chunk in r.aiter_bytes(chunk_size=65536):
                    yield chunk

    return StreamingResponse(
        stream_bytes(), media_type="video/mp4",
        headers={"Content-Disposition": f'inline; filename="detected_{video_id[:8]}.mp4"'},
    )


# ── 历史 ──────────────────────────────────────

@router.get("/preview/{video_id}")
async def preview_video(video_id: str):
    fp = resolve_video_file(video_id)
    if not fp:
        raise HTTPException(404, "视频不存在")
    return FileResponse(
        str(fp),
        media_type="video/mp4",
        headers={"Content-Disposition": "inline"},
    )


@router.get("/history")
async def get_history(
    page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    records, total = list_video_records(page, page_size, user_id=current_user.id)
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
