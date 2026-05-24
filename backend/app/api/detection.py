import io, json, time, uuid, cv2, httpx, logging
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
import numpy as np


def _imread(path):
    """cv2.imread 的 Unicode-safe 替代，避免 Windows 中文路径编码问题。"""
    data = np.fromfile(str(path), dtype=np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def _imwrite(path, img):
    """cv2.imwrite 的 Unicode-safe 替代。"""
    _, buf = cv2.imencode(Path(path).suffix, img)
    buf.tofile(str(path))


GEOSPATIAL = {'.tif', '.tiff', '.img', '.ntf'}
_COLORS = [(0, 0, 255), (0, 255, 0), (255, 0, 0), (0, 255, 255),
           (255, 255, 0), (255, 0, 255), (128, 0, 255), (255, 128, 0),
           (0, 128, 255), (128, 255, 0), (0, 255, 128), (255, 0, 128),
           (128, 128, 255), (255, 128, 128), (128, 255, 128)]


def _tif_to_preview_rgb(filepath):
    """读取 TIF 并返回 3 通道 RGB 预览图 (numpy uint8)。"""
    import rasterio
    with rasterio.open(filepath) as src:
        n = src.count
        if n >= 3:
            bands = [src.read(i + 1) for i in range(3)]
        elif n == 2:
            bands = [src.read(1), src.read(2), src.read(1)]
        elif n == 1:
            b = src.read(1)
            bands = [b, b, b]
        else:
            return np.zeros((256, 256, 3), dtype=np.uint8)

    channels = []
    for b in bands:
        bf = b.astype(np.float32)
        p_low, p_high = np.percentile(bf, 2), np.percentile(bf, 98)
        if p_high - p_low < 1e-6:
            p_high = p_low + 1
        channels.append(np.clip((bf - p_low) / (p_high - p_low) * 255, 0, 255).astype(np.uint8))
    return np.dstack(channels)


def _generate_tif_preview(filepath):
    """对 TIF 生成 PNG 预览，上传 MinIO，返回 preview_url。非 TIF 返回 None；TIF 失败也返回 None（调用方决不可回退 raw tif 给浏览器）。"""
    ext = Path(filepath).suffix.lower()
    if ext not in GEOSPATIAL:
        return None
    try:
        img = _tif_to_preview_rgb(filepath)
        png_name = f"preview_{Path(filepath).stem}_{uuid.uuid4().hex[:6]}.png"
        png_path = Paths.uploads() / png_name
        _imwrite(png_path, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
        minio_service.upload_file(str(png_path), f"uploads/{png_name}", "image/png")
        return get_file_url(png_name, "static/uploads")
    except Exception as e:
        logger.error("TIF preview generation FAILED for %s: %s — raw TIF will not display in browser", filepath, e)
        return None


def _draw_annotations(image, boxes):
    """在 image 上绘制检测框 + 标签文字，原地修改。"""
    for b in boxes:
        color = _COLORS[int(b["class_id"]) % len(_COLORS)]
        cv2.rectangle(image, (int(b["x1"]), int(b["y1"])),
                      (int(b["x2"]), int(b["y2"])), color, 2)
        label = f'{b["class_name"]} {b["confidence"]:.2f}'
        cv2.putText(image, label, (int(b["x1"]), max(int(b["y1"]) - 5, 15)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)


from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import StreamingResponse
from app.services.history_service import list_records, get_record, delete_record, save_record, get_all_records
from app.utils.file_utils import save_upload_file, ensure_directories, get_file_url
from app.utils.paths import Paths
from app.utils.validation import CheckContext, DataValidator
from app.config import settings
from app.models.db_models import User
from app.models.schemas import (
    SingleDetectionResponse, BatchDetectionResponse, BatchDetectionItem,
    HistoryListResponse, HistoryDetailResponse, HistoryRecord,
    TargetListResponse, TargetItem,
    ExportRequest, EvaluationResponse, EvaluationStats, ClassMetrics,
    DailyTrend, ModelUsage, ConfBin,
    DetectionBox, DetectionResult,
)
from app.utils.dependencies import get_current_user
from app.services.minio_service import minio_service
from app.services.redis_service import redis_service

logger = logging.getLogger("rsod.detection")
router = APIRouter(prefix="/detection", tags=["detection"])
ensure_directories()

DET_ENGINE = settings.DET_ENGINE_URL


# ── 导出工具函数 ────────────────────────────────

def _export_coco(boxes, image_id=1):
    cats = [{"id": b.class_id, "name": b.class_name} for b in boxes]
    seen = set()
    cats = [c for c in cats if not (c["id"] in seen or seen.add(c["id"]))]
    anns = [{"id": i, "image_id": image_id, "category_id": b.class_id,
             "bbox": [b.x1, b.y1, b.x2 - b.x1, b.y2 - b.y1],
             "area": (b.x2 - b.x1) * (b.y2 - b.y1), "score": b.confidence}
            for i, b in enumerate(boxes, 1)]
    return {"images": [{"id": image_id}], "categories": cats, "annotations": anns}


def _export_yolo(boxes):
    parts = []
    for b in boxes:
        width = max(b.x2 - b.x1, 1)
        height = max(b.y2 - b.y1, 1)
        cx = (b.x1 + b.x2) / 2
        cy = (b.y1 + b.y2) / 2
        parts.append(f"{b.class_id} {cx:.6f} {cy:.6f} {width:.6f} {height:.6f}")
    return "\n".join(parts)


def _export_geojson(boxes):
    return {"type": "FeatureCollection", "features": [{
        "type": "Feature",
        "properties": {"class_name": b.class_name, "confidence": b.confidence},
        "geometry": {"type": "Polygon", "coordinates": [[[b.x1, b.y1], [b.x2, b.y1],
                        [b.x2, b.y2], [b.x1, b.y2], [b.x1, b.y1]]]},
    } for b in boxes]}


# ── 模型管理（代理到引擎）─────────────────────────

@router.get("/models")
async def get_models():
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{DET_ENGINE}/models")
    return r.json()


@router.post("/model/switch")
async def switch_model(data: dict):
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{DET_ENGINE}/model/switch", json=data)
    return r.json()


# ── 预览 ──────────────────────────────────────────

@router.post("/preview")
async def preview_image(file: UploadFile = File(...)):
    ctx = CheckContext(file_path=Path(file.filename))
    validator = DataValidator(ctx)
    if not validator.validate_and_report(["file_extension"]):
        raise HTTPException(400, "文件格式不支持")

    ext = Path(file.filename).suffix.lower()
    content = await file.read()
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = Paths.uploads() / filename
    with open(filepath, "wb") as f:
        f.write(content)
    minio_service.upload_file(str(filepath), f"uploads/{filename}", file.content_type or "image/jpeg")

    if ext in GEOSPATIAL:
        preview_url = _generate_tif_preview(filepath) or ""
        return {"success": True, "data": {"preview_url": preview_url, "filename": filename}}
    return {"success": True, "data": {"preview_url": get_file_url(filename, "static/uploads"), "filename": filename}}


# ── 单图检测 ──────────────────────────────────────

@router.post("/single", response_model=SingleDetectionResponse)
async def detect_single_image(
    file: UploadFile = File(...),
    model_name: str = Form(settings.DEFAULT_DET_MODEL),
    conf_threshold: float = Form(0.5),
    iou_threshold: float = Form(0.45),
    use_sahi: bool = Form(False),
    current_user: User = Depends(get_current_user),
):
    # 数据验证
    ctx = CheckContext(
        file_path=Path(file.filename),
        model_name=model_name,
        conf_threshold=conf_threshold,
        iou_threshold=iou_threshold,
    )
    validator = DataValidator(ctx)
    if not validator.validate_and_report(["file_extension", "file_size", "image_readable", "detection_params"]):
        raise HTTPException(400, "数据验证未通过")

    if not await redis_service.check_rate_limit(current_user.id):
        raise HTTPException(429, "请求过于频繁，请稍后重试")

    logger.info("开始单图检测: %s, 模型: %s, 用户: %s", file.filename, model_name, current_user.username)

    upload_dir = str(Paths.uploads())
    filename = await save_upload_file(file, upload_dir)
    image_path = Paths.uploads() / filename

    data = {"model_name": model_name, "conf_threshold": conf_threshold,
            "iou_threshold": iou_threshold, "use_sahi": str(use_sahi).lower()}
    with open(image_path, "rb") as f:
        content = f.read()
    fd = {"file": (filename, content, file.content_type or "image/jpeg")}

    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.post(f"{DET_ENGINE}/detect/single", files=fd, data=data)
    if r.status_code != 200:
        logger.error("检测引擎返回 %d: %s", r.status_code, r.text[:200])
        raise HTTPException(502, "检测服务暂时不可用，请稍后重试")

    raw = r.json()

    # 绘制结果图
    result_filename = f"result_{raw['detection_id'][:8]}.jpg"
    result_path = Paths.results() / result_filename
    orig = _imread(image_path)
    if orig is not None:
        _draw_annotations(orig, raw["boxes"])
        _imwrite(result_path, orig)
    else:
        _imwrite(result_path, np.zeros((256, 256, 3), dtype=np.uint8))

    minio_service.upload_file(str(result_path), f"results/{result_filename}", "image/jpeg")

    image_url = get_file_url(filename, "static/uploads")
    result_url = get_file_url(result_filename, "static/results")
    preview_url = _generate_tif_preview(image_path)
    if not preview_url and image_path.suffix.lower() not in GEOSPATIAL:
        preview_url = image_url
    preview_url = preview_url or ""

    boxes = [DetectionBox(**b) for b in raw["boxes"]]
    det_result = DetectionResult(
        detection_id=raw["detection_id"], image_url=image_url,
        result_image_url=result_url, preview_image_url=preview_url,
        boxes=boxes, total_objects=raw["total_objects"],
        detection_time=raw["detection_time"], model_name=raw["model_name"],
        created_at=datetime.now(),
    )
    save_record(det_result, image_url, result_url, filename, raw["model_name"],
                current_user.username, current_user.id, preview_image_url=preview_url)

    logger.info("单图检测完成: %d 个目标, 耗时 %.2fs", raw["total_objects"], raw["detection_time"])
    return SingleDetectionResponse(success=True, message="检测成功", data=det_result)


# ── 批量检测 ──────────────────────────────────────

@router.post("/batch", response_model=BatchDetectionResponse)
async def detect_batch_images(
    files: list[UploadFile] = File(...),
    model_name: str = Form(settings.DEFAULT_DET_MODEL),
    conf_threshold: float = Form(0.5),
    iou_threshold: float = Form(0.45),
    use_sahi: bool = Form(False),
    current_user: User = Depends(get_current_user),
):
    if not files:
        raise HTTPException(400, "请至少上传一张图片")

    t_total = time.time()
    results = []

    # 先保存所有文件到本地及 MinIO；引擎会自己生成文件名，我们按 index 配对
    saved_info = []  # [(original_name, our_saved_filename), ...]
    engine_files = []
    for f in files:
        content = await f.read()
        ext = Path(f.filename).suffix.lower() or ".jpg"
        fn = f"{uuid.uuid4().hex}{ext}"
        fp = Paths.uploads() / fn
        with open(fp, "wb") as wf:
            wf.write(content)
        minio_service.upload_file(str(fp), f"uploads/{fn}", f.content_type or "image/jpeg")
        saved_info.append((f.filename, fn))
        engine_files.append(("files", (f.filename, content, f.content_type or "image/jpeg")))

    data = {"model_name": model_name, "conf_threshold": conf_threshold,
            "iou_threshold": iou_threshold, "use_sahi": str(use_sahi).lower()}

    async with httpx.AsyncClient(timeout=300) as c:
        r = await c.post(f"{DET_ENGINE}/detect/batch", files=engine_files, data=data)
    if r.status_code != 200:
        logger.error("批量检测引擎返回 %d: %s", r.status_code, r.text[:200])
        raise HTTPException(502, "检测服务暂时不可用，请稍后重试")
    items = r.json()["results"]

    # 引擎按顺序处理，results[i] 对应 saved_info[i]
    for i, item in enumerate(items):
        if "error" in item:
            continue
        orig_name, saved_fn = saved_info[i]
        img_path = Paths.uploads() / saved_fn
        result_filename = f"result_{item['detection_id'][:8]}.jpg"
        result_path = Paths.results() / result_filename
        orig = _imread(img_path) if img_path.exists() else None
        if orig is not None:
            _draw_annotations(orig, item["boxes"])
            _imwrite(result_path, orig)
        else:
            _imwrite(result_path, np.zeros((256, 256, 3), dtype=np.uint8))
        minio_service.upload_file(str(result_path), f"results/{result_filename}", "image/jpeg")

        img_url = get_file_url(saved_fn, "static/uploads")
        res_url = get_file_url(result_filename, "static/results")
        preview_url = _generate_tif_preview(img_path)
        if not preview_url and img_path.suffix.lower() not in GEOSPATIAL:
            preview_url = img_url
        preview_url = preview_url or ""
        boxes = [DetectionBox(**b) for b in item["boxes"]]

        det_result = DetectionResult(
            detection_id=item["detection_id"], image_url=img_url,
            result_image_url=res_url, preview_image_url=preview_url,
            boxes=boxes, total_objects=item["total_objects"],
            detection_time=item["detection_time"], model_name=item["model_name"],
            created_at=datetime.now(),
        )
        save_record(det_result, img_url, res_url, saved_fn, item["model_name"],
                    current_user.username, current_user.id, preview_image_url=preview_url)

        results.append(BatchDetectionItem(
            filename=orig_name, image_url=img_url, result_image_url=res_url,
            preview_image_url=preview_url,
            total_objects=item["total_objects"], detection_time=item["detection_time"],
            boxes=boxes, detection_id=item["detection_id"],
        ))

    total_time = round(time.time() - t_total, 3)
    return BatchDetectionResponse(
        success=True, message=f"批量检测完成，共 {len(results)} 张图片",
        data=results, total_files=len(results),
        total_objects=sum(r.total_objects for r in results),
        total_time=total_time,
    )


# ── 标注导出 ──────────────────────────────────────

@router.post("/export")
async def export_detection(data: ExportRequest):
    record = get_record(data.record_id)
    if not record:
        raise HTTPException(404, "记录不存在")
    boxes = [DetectionBox(**b) for b in record.get("boxes", [])]

    fmt_map = {
        "coco": ("json", lambda: json.dumps(_export_coco(boxes), ensure_ascii=False, indent=2)),
        "yolo": ("txt", lambda: _export_yolo(boxes)),
        "geojson": ("geojson", lambda: json.dumps(_export_geojson(boxes), ensure_ascii=False, indent=2)),
    }
    ext, fn = fmt_map.get(data.format, (None, None))
    if not ext:
        raise HTTPException(400, f"不支持的格式: {data.format}")

    content = fn()
    return StreamingResponse(io.BytesIO(content.encode("utf-8")), media_type="application/octet-stream",
                             headers={"Content-Disposition": f'attachment; filename="detection_{data.record_id[:8]}.{ext}"'})


# ── 批量下载结果图 (ZIP) ──────────────────────────

@router.post("/download-results")
async def download_results(data: dict):
    import zipfile
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        added = 0
        for rid in data.get("record_ids", []):
            rec = get_record(rid)
            if not rec:
                continue
            parsed = urlparse(rec.get("result_image_url", ""))
            rp = Paths.results() / Path(parsed.path).name
            if rp.exists():
                base = Path(rec.get("filename", "image")).stem
                zf.write(str(rp), f"{base}_{rid[:8]}.jpg")
                added += 1
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/zip",
                             headers={"Content-Disposition": f"attachment; filename=results_{len(data.get('record_ids', []))}.zip"})


# ── 统计 + 历史（不变，读 DB）──────────────────────

@router.get("/statistics", response_model=EvaluationResponse)
async def get_statistics(current_user: User = Depends(get_current_user)):
    all_records = get_all_records(user_id=current_user.id)
    if not all_records:
        return EvaluationResponse(success=True, message="暂无检测数据", data=None)

    total_objects = sum(r.get("total_objects", 0) for r in all_records)
    total_time = sum(r.get("detection_time", 0) for r in all_records)
    ch_names = {"plane": "飞机", "ship": "船舶", "storage-tank": "储罐", "baseball-diamond": "棒球场",
                "tennis-court": "网球场", "basketball-court": "篮球场", "ground-track-field": "田径场",
                "harbor": "港口", "bridge": "桥梁", "large-vehicle": "大型车辆", "small-vehicle": "小型车辆",
                "helicopter": "直升机", "roundabout": "环岛", "soccer-ball-field": "足球场", "swimming-pool": "游泳池"}

    per_class, per_conf = {}, {}
    daily, models = {}, {}
    bins = {f"{i/10:.1f}-{(i+1)/10:.1f}": 0 for i in range(10)}

    for r in all_records:
        d = (r.get("created_at", "")[:10])
        daily[d] = daily.get(d, {"count": 0, "objects": 0})
        daily[d]["count"] += 1
        daily[d]["objects"] += r.get("total_objects", 0)

        m = r.get("model_name", "unknown")
        models[m] = models.get(m, {"count": 0, "objects": 0})
        models[m]["count"] += 1
        models[m]["objects"] += r.get("total_objects", 0)

        for b in r.get("boxes", []):
            cls = b.get("class_name", "unknown")
            c = b.get("confidence", 0)
            per_class[cls] = per_class.get(cls, 0) + 1
            per_conf.setdefault(cls, []).append(c)
            bins[f"{int(c * 10) / 10:.1f}-{int(c * 10 + 1) / 10:.1f}"] += 1

    pc = [ClassMetrics(class_name=k, chinese_name=ch_names.get(k, k), count=v,
                       avg_confidence=round(float(np.mean(per_conf[k])), 4),
                       confidence_std=round(float(np.std(per_conf[k])), 4))
          for k, v in sorted(per_class.items(), key=lambda x: -x[1])]

    n = len(all_records)
    stats = EvaluationStats(
        total_images=n, total_objects=total_objects,
        avg_objects_per_image=round(total_objects / n, 2) if n else 0,
        avg_detection_time=round(total_time / n, 3) if n else 0,
        per_class=pc,
        daily_trend=[DailyTrend(date=d, count=v["count"], objects=v["objects"]) for d, v in sorted(daily.items())],
        model_distribution=[ModelUsage(model=m, count=v["count"], objects=v["objects"]) for m, v in sorted(models.items(), key=lambda x: -x[1]["count"])],
        confidence_distribution=[ConfBin(range=k, count=v) for k, v in bins.items()],
    )
    return EvaluationResponse(success=True, message="统计完成", data=stats)


@router.get("/history", response_model=HistoryListResponse)
async def get_history(page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100),
                      keyword: str = Query(""), status: str = Query(""),
                      current_user: User = Depends(get_current_user)):
    records, total = list_records(page, page_size, keyword, status, user_id=current_user.id)
    return HistoryListResponse(success=True, message="获取成功",
                               data=[HistoryRecord(**r) for r in records],
                               total=total, page=page, page_size=page_size)


@router.get("/history/{record_id}", response_model=HistoryDetailResponse)
async def get_history_detail(record_id: str):
    r = get_record(record_id)
    if not r:
        raise HTTPException(404, "记录不存在")
    boxes = [DetectionBox(**b) for b in r.get("boxes", [])]
    detail = DetectionResult(detection_id=r.get("detection_id", r["id"]),
                             image_url=r.get("image_url", ""),
                             result_image_url=r.get("result_image_url", ""),
                             preview_image_url=r.get("preview_image_url", ""),
                             boxes=boxes, total_objects=r.get("total_objects", 0),
                             detection_time=r.get("detection_time", 0.0),
                             model_name=r.get("model_name", ""),
                             created_at=datetime.fromisoformat(r["created_at"]) if r.get("created_at") else datetime.now())
    return HistoryDetailResponse(success=True, message="获取成功", data=detail)


@router.delete("/history/{record_id}")
async def delete_history_record(record_id: str):
    if not delete_record(record_id):
        raise HTTPException(404, "记录不存在")
    return {"success": True, "message": "删除成功"}


@router.get("/targets/list", response_model=TargetListResponse)
async def get_target_list():
    targets = [
        TargetItem(id=0, name="plane"),
        TargetItem(id=1, name="ship"),
        TargetItem(id=2, name="storage-tank"),
        TargetItem(id=3, name="baseball-diamond"),
        TargetItem(id=4, name="tennis-court"),
        TargetItem(id=5, name="basketball-court"),
        TargetItem(id=6, name="ground-track-field"),
        TargetItem(id=7, name="harbor"),
        TargetItem(id=8, name="bridge"),
        TargetItem(id=9, name="large-vehicle"),
        TargetItem(id=10, name="small-vehicle"),
        TargetItem(id=11, name="helicopter"),
        TargetItem(id=12, name="roundabout"),
        TargetItem(id=13, name="soccer-ball-field"),
        TargetItem(id=14, name="swimming-pool"),
    ]
    return TargetListResponse(success=True, message="获取成功", data=targets)
