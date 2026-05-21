import os, io, time, uuid, httpx
from datetime import datetime
from app.utils.file_utils import get_file_url, save_upload_file
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from app.services.history_service import save_cd_record, list_cd_records, get_cd_record, delete_cd_record, get_all_cd_records
from app.utils.dependencies import get_current_user
from app.models.db_models import User
from app.models.schemas import (
    ChangeDetectionResponse, ChangeDetectionResult,
    BatchChangeItem, BatchChangeResponse,
    ChangeHistoryListResponse, ChangeHistoryRecord,
    ChangeHistoryDetailResponse,
)
from app.config import settings

router = APIRouter(prefix="/change-detection", tags=["change-detection"])
CD_ENGINE = settings.CD_ENGINE_URL
ALLOWED = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff'}


def _valid_ext(name):
    if os.path.splitext(name)[1].lower() not in ALLOWED:
        raise HTTPException(400, f"不支持的文件格式: {name}")


# ── 模型管理（代理到引擎）─────────────────────────

@router.get("/models")
async def get_models():
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{CD_ENGINE}/models")
    return r.json()


@router.post("/model/switch")
async def switch_model(data: dict):
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{CD_ENGINE}/model/switch", json=data)
    return r.json()


# ── 单对变化检测 ─────────────────────────────────

@router.post("/single", response_model=ChangeDetectionResponse)
async def detect_change_single(
    file_a: UploadFile = File(...),
    file_b: UploadFile = File(...),
    model_key: str = Form(settings.DEFAULT_CD_MODEL),
    current_user: User = Depends(get_current_user),
):
    _valid_ext(file_a.filename)
    _valid_ext(file_b.filename)

    filename_a = await save_upload_file(file_a, settings.UPLOAD_DIR)
    filename_b = await save_upload_file(file_b, settings.UPLOAD_DIR)
    path_a = os.path.join(settings.UPLOAD_DIR, filename_a)
    path_b = os.path.join(settings.UPLOAD_DIR, filename_b)

    with open(path_a, "rb") as f:
        content_a = f.read()
    with open(path_b, "rb") as f:
        content_b = f.read()
    fd_a = ("file_a", (file_a.filename, content_a, file_a.content_type or "image/jpeg"))
    fd_b = ("file_b", (file_b.filename, content_b, file_b.content_type or "image/jpeg"))
    data = {"model_key": model_key}

    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.post(f"{CD_ENGINE}/detect/single", files=[fd_a, fd_b], data=data)
    if r.status_code != 200:
        raise HTTPException(r.status_code, detail=f"变化检测引擎错误: {r.text}")
    raw = r.json()

    img_a_url = get_file_url(filename_a, "static/uploads")
    img_b_url = get_file_url(filename_b, "static/uploads")
    # 引擎只返回 change_ratio，结果图在主服务端后续渲染
    # 这里用一个 placeholder result_url
    result_url = img_a_url  # TODO: 等引擎返回 mask 后改为真实结果图

    detection_id = f"cd_{os.path.basename(filename_a)[:8]}"
    save_cd_record(detection_id, current_user.id, current_user.username,
                   filename_a, filename_b, img_a_url, img_b_url, result_url,
                   raw["change_ratio"], raw["detection_time"], raw["model_name"])

    return ChangeDetectionResponse(
        success=True, message="检测完成",
        data=ChangeDetectionResult(
            detection_id=detection_id, image_a_url=img_a_url,
            image_b_url=img_b_url, result_url=result_url,
            change_ratio=raw["change_ratio"], detection_time=raw["detection_time"],
            model_name=raw["model_name"], created_at=datetime.now(),
        ),
    )


# ── 批量变化检测 ─────────────────────────────────

@router.post("/batch", response_model=BatchChangeResponse)
async def detect_change_batch(
    files_a: list[UploadFile] = File(...),
    files_b: list[UploadFile] = File(...),
    model_key: str = Form(settings.DEFAULT_CD_MODEL),
    current_user: User = Depends(get_current_user),
):
    if len(files_a) != len(files_b):
        raise HTTPException(400, "两个时相的图片数量不一致")
    if not files_a:
        raise HTTPException(400, "请至少上传一对图片")

    t_total = time.time()
    results = []
    fd_list_a = [("files_a", (f.filename, await f.read(), f.content_type or "image/jpeg")) for f in files_a]
    fd_list_b = [("files_b", (f.filename, await f.read(), f.content_type or "image/jpeg")) for f in files_b]
    data = {"model_key": model_key}

    async with httpx.AsyncClient(timeout=300) as c:
        r = await c.post(f"{CD_ENGINE}/detect/batch", files=fd_list_a + fd_list_b, data=data)
    items = r.json()["results"]

    for item in items:
        if "error" in item:
            results.append(BatchChangeItem(filename_a=item.get("filename_a", ""),
                                           filename_b=item.get("filename_b", ""),
                                           image_a_url="", image_b_url="", result_url="",
                                           change_ratio=0, detection_time=0))
            continue

        detection_id = f"cd_{uuid.uuid4().hex[:12]}"
        save_cd_record(detection_id, current_user.id, current_user.username,
                       item.get("filename_a", ""), item.get("filename_b", ""),
                       "", "", "",
                       item["change_ratio"], item["detection_time"], item["model_name"])

        results.append(BatchChangeItem(
            filename_a=item.get("filename_a", ""), filename_b=item.get("filename_b", ""),
            image_a_url="", image_b_url="", result_url="",
            change_ratio=item["change_ratio"], detection_time=item["detection_time"],
        ))

    return BatchChangeResponse(
        success=True, message=f"批量检测完成，共 {len(files_a)} 对图片",
        data=results, total_pairs=len(files_a),
        total_time=round(time.time() - t_total, 1),
    )


# ── 历史 ──────────────────────────────────────────

@router.get("/history", response_model=ChangeHistoryListResponse)
async def get_cd_history(page: int = 1, page_size: int = 10,
                         current_user: User = Depends(get_current_user)):
    records, total = list_cd_records(page, page_size, current_user.username)
    return ChangeHistoryListResponse(
        success=True, message="获取成功",
        data=[ChangeHistoryRecord(**r) for r in records],
        total=total, page=page, page_size=page_size,
    )


@router.get("/history/{record_id}", response_model=ChangeHistoryDetailResponse)
async def get_cd_history_detail(record_id: str):
    r = get_cd_record(record_id)
    if not r:
        raise HTTPException(404, "记录不存在")
    return ChangeHistoryDetailResponse(
        success=True, message="获取成功",
        data=ChangeDetectionResult(
            detection_id=r["id"], image_a_url=r["image_a_url"],
            image_b_url=r["image_b_url"], result_url=r["result_url"],
            change_ratio=r["change_ratio"], detection_time=r["detection_time"],
            model_name=r["model_name"],
            created_at=datetime.fromisoformat(r["created_at"]) if r.get("created_at") else datetime.now(),
        ),
    )


@router.delete("/history/{record_id}")
async def delete_cd_history_record(record_id: str):
    if not delete_cd_record(record_id):
        raise HTTPException(404, "记录不存在")
    return {"success": True, "message": "删除成功"}


@router.get("/statistics")
async def get_cd_statistics(current_user: User = Depends(get_current_user)):
    records = get_all_cd_records(username=current_user.username)
    if not records:
        return {"success": True, "message": "暂无数据", "data": None}

    total_pairs = len(records)
    total_time = sum(r.get("detection_time", 0) for r in records)
    avg_change = sum(r.get("change_ratio", 0) for r in records) / total_pairs if total_pairs else 0

    daily, models = {}, {}
    for r in records:
        d = r.get("created_at", "")[:10]
        daily[d] = daily.get(d, {"count": 0, "change_sum": 0})
        daily[d]["count"] += 1
        daily[d]["change_sum"] += r.get("change_ratio", 0)
        m = r.get("model_name", "")
        models[m] = models.get(m, 0) + 1

    return {
        "success": True, "message": "统计完成",
        "data": {
            "total_pairs": total_pairs,
            "avg_change_ratio": round(avg_change, 4),
            "total_time": round(total_time, 1),
            "avg_time": round(total_time / total_pairs, 3) if total_pairs else 0,
            "daily_trend": [{"date": d, "count": v["count"],
                              "avg_change": round(v["change_sum"] / v["count"], 4)}
                             for d, v in sorted(daily.items())],
            "model_usage": [{"model": m, "count": c} for m, c in sorted(models.items(), key=lambda x: -x[1])],
        },
    }
