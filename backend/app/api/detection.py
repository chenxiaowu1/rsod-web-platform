import os
import time
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from app.services.detection_service import detection_service
from app.services.history_service import list_records, get_record, delete_record, save_record
from app.utils.file_utils import save_upload_file, ensure_directories, get_file_url
from app.config import settings
from app.models.schemas import (
    SingleDetectionResponse, BatchDetectionResponse, BatchDetectionItem,
    HistoryListResponse, HistoryDetailResponse, HistoryRecord,
    TargetListResponse, TargetItem,
)

router = APIRouter(prefix="/detection", tags=["detection"])

ensure_directories()


@router.post("/single", response_model=SingleDetectionResponse)
async def detect_single_image(
    file: UploadFile = File(...),
    model_name: str = Form("pest-v1"),
    username: str = Form(""),
):
    try:
        filename = await save_upload_file(file, settings.UPLOAD_DIR)
        image_path = os.path.join(settings.UPLOAD_DIR, filename)

        result = detection_service.detect_single_image(image_path, model_name)

        image_url = get_file_url(filename, "static/uploads")
        result_image_url = result.result_image_url
        save_record(result, image_url, result_image_url, filename, model_name, username)

        return SingleDetectionResponse(
            success=True,
            message="检测成功",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检测失败: {str(e)}")


@router.post("/batch", response_model=BatchDetectionResponse)
async def detect_batch_images(
    files: list[UploadFile] = File(...),
    model_name: str = Form("pest-v1"),
    username: str = Form(""),
):
    """
    批量检测多张图片
    接收多个文件，顺序处理，返回每张图的结果
    """
    if not files:
        raise HTTPException(status_code=400, detail="请至少上传一张图片")

    t_total = time.time()

    image_paths = []
    saved_files = []
    for file in files:
        filename = await save_upload_file(file, settings.UPLOAD_DIR)
        image_paths.append(os.path.join(settings.UPLOAD_DIR, filename))
        saved_files.append(filename)

    try:
        batch_results = detection_service.detect_batch_images(image_paths, model_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量检测失败: {str(e)}")

    # 保存历史记录
    for i, item in enumerate(batch_results):
        from app.services.history_service import save_record
        from app.models.schemas import DetectionResult, DetectionBox
        try:
            fake_result = DetectionResult(
                detection_id=f"batch_{saved_files[i]}",
                image_url=item["image_url"],
                result_image_url=item["result_image_url"],
                boxes=[DetectionBox(**b) for b in item["boxes"]],
                total_objects=item["total_objects"],
                detection_time=item["detection_time"],
                model_name=model_name,
                created_at=datetime.now(),
            )
            save_record(fake_result, item["image_url"], item["result_image_url"],
                        saved_files[i], model_name, username)
        except Exception:
            pass

    total_time = round(time.time() - t_total, 3)

    return BatchDetectionResponse(
        success=True,
        message=f"批量检测完成，共 {len(batch_results)} 张图片",
        data=[BatchDetectionItem(**item) for item in batch_results],
        total_files=len(batch_results),
        total_objects=sum(item["total_objects"] for item in batch_results),
        total_time=total_time,
    )


# ── 历史记录 API ────────────────────────────────────

@router.get("/history", response_model=HistoryListResponse)
async def get_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: str = Query("", description="搜索关键词"),
    status: str = Query("", description="状态筛选: completed / failed"),
    username: str = Query(""),
):
    records, total = list_records(page, page_size, keyword, status, username=username)
    return HistoryListResponse(
        success=True,
        message="获取成功",
        data=[HistoryRecord(**r) for r in records],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/history/{record_id}", response_model=HistoryDetailResponse)
async def get_history_detail(record_id: str):
    record = get_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")

    from app.models.schemas import DetectionBox, DetectionResult
    boxes = [DetectionBox(**b) for b in record.get("boxes", [])]
    detail = DetectionResult(
        detection_id=record.get("detection_id", record["id"]),
        image_url=record.get("image_url", ""),
        result_image_url=record.get("result_image_url", ""),
        boxes=boxes,
        total_objects=record.get("total_objects", 0),
        detection_time=record.get("detection_time", 0.0),
        model_name=record.get("model_name", ""),
        created_at=datetime.fromisoformat(record["created_at"]) if record.get("created_at") else datetime.now(),
    )
    return HistoryDetailResponse(
        success=True,
        message="获取成功",
        data=detail,
    )


@router.delete("/history/{record_id}")
async def delete_history_record(record_id: str):
    ok = delete_record(record_id)
    if not ok:
        raise HTTPException(status_code=404, detail="记录不存在")
    return {"success": True, "message": "删除成功"}


# ── 模型管理 ──────────────────────────────────────

@router.get("/models")
async def get_models():
    """获取可用模型列表"""
    return {
        "success": True,
        "data": detection_service.get_models(),
    }


@router.post("/model/switch")
async def switch_model(data: dict):
    """切换当前模型: {"model_key": "yolo11m-obb"}"""
    key = data.get("model_key", "")
    result = detection_service.switch_model(key)
    return result


# ── 目标库 ────────────────────────────────────────

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
    return TargetListResponse(
        success=True,
        message="获取成功",
        data=targets
    )
