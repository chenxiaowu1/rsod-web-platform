import os, io, json, time, cv2, httpx
from datetime import datetime
from urllib.parse import urlparse
import numpy as np
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import StreamingResponse
from app.services.history_service import list_records, get_record, delete_record, save_record, get_all_records
from app.utils.file_utils import save_upload_file, ensure_directories, get_file_url
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

router = APIRouter(prefix="/detection", tags=["detection"])
ensure_directories()

ALLOWED = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tif', '.tiff', '.geotiff', '.ntf', '.img'}
DET_ENGINE = settings.DET_ENGINE_URL


def _valid_ext(name):
    ext = os.path.splitext(name)[1].lower()
    if ext not in ALLOWED:
        raise HTTPException(400, f"不支持的文件格式: {ext}")
    return ext


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
    _valid_ext(file.filename)
    filename = await save_upload_file(file, settings.UPLOAD_DIR)
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
    _valid_ext(file.filename)
    filename = await save_upload_file(file, settings.UPLOAD_DIR)
    image_path = os.path.join(settings.UPLOAD_DIR, filename)

    data = {"model_name": model_name, "conf_threshold": conf_threshold,
            "iou_threshold": iou_threshold, "use_sahi": str(use_sahi).lower()}
    with open(image_path, "rb") as f:
        content = f.read()
    fd = {"file": (filename, content, file.content_type or "image/jpeg")}

    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.post(f"{DET_ENGINE}/detect/single", files=fd, data=data)
    if r.status_code != 200:
        raise HTTPException(r.status_code, detail=f"检测引擎错误: {r.text}")

    raw = r.json()

    # 绘制结果图（安全画框）
    result_filename = f"result_{raw['detection_id'][:8]}.jpg"
    result_path = os.path.join(settings.RESULT_DIR, result_filename)
    orig = cv2.imread(image_path)
    if orig is not None:
        bgr_colors = [(0, 0, 255), (0, 255, 0), (255, 0, 0), (0, 255, 255),
                       (255, 255, 0), (255, 0, 255), (128, 0, 255), (255, 128, 0),
                       (0, 128, 255), (128, 255, 0), (0, 255, 128), (255, 0, 128),
                       (128, 128, 255), (255, 128, 128), (128, 255, 128)]
        for b in raw["boxes"]:
            color = bgr_colors[b["class_id"] % 15]
            cv2.rectangle(orig, (int(b["x1"]), int(b["y1"])),
                          (int(b["x2"]), int(b["y2"])), color, 2)
            label = f'{b["class_name"]} {b["confidence"]:.2f}'
            cv2.putText(orig, label, (int(b["x1"]), max(int(b["y1"]) - 5, 15)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        cv2.imwrite(result_path, orig)
    else:
        cv2.imwrite(result_path, np.zeros((256, 256, 3), dtype=np.uint8))

    minio_service.upload_file(result_path, f"results/{result_filename}", "image/jpeg")

    image_url = get_file_url(filename, "static/uploads")
    result_url = get_file_url(result_filename, "static/results")

    boxes = [DetectionBox(**b) for b in raw["boxes"]]
    det_result = DetectionResult(
        detection_id=raw["detection_id"], image_url=image_url, result_image_url=result_url,
        boxes=boxes, total_objects=raw["total_objects"],
        detection_time=raw["detection_time"], model_name=raw["model_name"],
        created_at=datetime.now(),
    )
    save_record(det_result, image_url, result_url, filename, raw["model_name"],
                current_user.username, current_user.id)

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
    engine_files = [("files", (f.filename, await f.read(), f.content_type or "image/jpeg")) for f in files]
    data = {"model_name": model_name, "conf_threshold": conf_threshold,
            "iou_threshold": iou_threshold, "use_sahi": str(use_sahi).lower()}

    async with httpx.AsyncClient(timeout=300) as c:
        r = await c.post(f"{DET_ENGINE}/detect/batch", files=engine_files, data=data)
    if r.status_code != 200:
        raise HTTPException(r.status_code, detail=f"检测引擎错误: {r.text}")
    items = r.json()["results"]

    bgr_colors = [(0, 0, 255), (0, 255, 0), (255, 0, 0), (0, 255, 255),
                   (255, 255, 0), (255, 0, 255), (128, 0, 255), (255, 128, 0),
                   (0, 128, 255), (128, 255, 0), (0, 255, 128), (255, 0, 128),
                   (128, 128, 255), (255, 128, 128), (128, 255, 128)]

    for item in items:
        if "error" in item:
            continue
        img_path = os.path.join(settings.UPLOAD_DIR, item.get("filename", ""))
        result_filename = f"result_{item['detection_id'][:8]}.jpg"
        result_path = os.path.join(settings.RESULT_DIR, result_filename)
        orig = cv2.imread(img_path) if os.path.exists(img_path) else None
        if orig is not None:
            for b in item["boxes"]:
                color = bgr_colors[b["class_id"] % 15]
                cv2.rectangle(orig, (int(b["x1"]), int(b["y1"])),
                              (int(b["x2"]), int(b["y2"])), color, 2)
            cv2.imwrite(result_path, orig)
        else:
            cv2.imwrite(result_path, np.zeros((256, 256, 3), dtype=np.uint8))
        minio_service.upload_file(result_path, f"results/{result_filename}", "image/jpeg")

        fn = item.get("filename", "")
        img_url = get_file_url(fn, "static/uploads") if fn else ""
        res_url = get_file_url(result_filename, "static/results")
        boxes = [DetectionBox(**b) for b in item["boxes"]]

        det_result = DetectionResult(
            detection_id=item["detection_id"], image_url=img_url, result_image_url=res_url,
            boxes=boxes, total_objects=item["total_objects"],
            detection_time=item["detection_time"], model_name=item["model_name"],
            created_at=datetime.now(),
        )
        save_record(det_result, img_url, res_url, fn, item["model_name"],
                    current_user.username, current_user.id)

        results.append(BatchDetectionItem(
            filename=fn, image_url=img_url, result_image_url=res_url,
            total_objects=item["total_objects"], detection_time=item["detection_time"],
            boxes=boxes,
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
            rp = os.path.join(settings.RESULT_DIR, os.path.basename(parsed.path))
            if os.path.exists(rp):
                base = os.path.splitext(rec.get("filename", "image"))[0]
                zf.write(rp, f"{base}_{rid[:8]}.jpg")
                added += 1
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/zip",
                             headers={"Content-Disposition": f"attachment; filename=results_{len(data.get('record_ids', []))}.zip"})


# ── 统计 + 历史（不变，读 DB）──────────────────────

@router.get("/statistics", response_model=EvaluationResponse)
async def get_statistics(current_user: User = Depends(get_current_user)):
    all_records = get_all_records(username=current_user.username)
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
    records, total = list_records(page, page_size, keyword, status, username=current_user.username)
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
                             image_url=r.get("image_url", ""), result_image_url=r.get("result_image_url", ""),
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
        TargetItem(id=0, name="plane", chinese_name="飞机", description="固定翼飞机、客机、战斗机等"),
        TargetItem(id=1, name="ship", chinese_name="船舶", description="货船、渔船、军舰等"),
        TargetItem(id=2, name="storage-tank", chinese_name="储罐", description="储油罐、储气罐等圆形储罐"),
        TargetItem(id=3, name="baseball-diamond", chinese_name="棒球场", description="棒球场、垒球场等"),
        TargetItem(id=4, name="tennis-court", chinese_name="网球场", description="网球场"),
        TargetItem(id=5, name="basketball-court", chinese_name="篮球场", description="篮球场"),
        TargetItem(id=6, name="ground-track-field", chinese_name="田径场", description="田径运动场"),
        TargetItem(id=7, name="harbor", chinese_name="港口", description="港口、码头"),
        TargetItem(id=8, name="bridge", chinese_name="桥梁", description="公路桥、铁路桥等"),
        TargetItem(id=9, name="large-vehicle", chinese_name="大型车辆", description="卡车、公交车等大型车辆"),
        TargetItem(id=10, name="small-vehicle", chinese_name="小型车辆", description="轿车、SUV等小型车辆"),
        TargetItem(id=11, name="helicopter", chinese_name="直升机", description="各类直升机"),
        TargetItem(id=12, name="roundabout", chinese_name="环岛", description="交通环岛、转盘"),
        TargetItem(id=13, name="soccer-ball-field", chinese_name="足球场", description="足球场"),
        TargetItem(id=14, name="swimming-pool", chinese_name="游泳池", description="游泳池"),
    ]
    return TargetListResponse(success=True, message="获取成功", data=targets)
