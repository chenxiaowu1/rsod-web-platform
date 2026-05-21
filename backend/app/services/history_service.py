"""
检测历史记录 — 文件存储服务

每条检测记录保存为 history/{record_id}.json
"""

import os
import json
import uuid
import glob
from datetime import datetime
from typing import Optional

HISTORY_DIR = "history"


def _ensure_dir():
    os.makedirs(HISTORY_DIR, exist_ok=True)


def save_record(detection_result, image_url: str, result_image_url: str,
                filename: str, model_name: str, username: str = "") -> dict:
    """保存一条检测记录，返回 record dict"""
    _ensure_dir()

    record_id = detection_result.detection_id
    boxes_data = [b.model_dump() if hasattr(b, 'model_dump') else b for b in detection_result.boxes]
    record = {
        "id": record_id,
        "detection_id": record_id,
        "username": username,
        "filename": filename,
        "image_url": image_url,
        "result_image_url": result_image_url,
        "type": "single",
        "status": "completed",
        "created_at": detection_result.created_at.isoformat(),
        "total_objects": detection_result.total_objects,
        "detected_classes": list(set(b.class_name for b in detection_result.boxes)),
        "detection_time": detection_result.detection_time,
        "model_name": model_name,
        "boxes": boxes_data,
    }
    with open(os.path.join(HISTORY_DIR, f"{record_id}.json"), "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    return record


def list_records(page: int = 1, page_size: int = 10,
                 keyword: str = "", status: str = "",
                 username: str = "") -> tuple[list[dict], int]:
    """分页查询记录，返回 (records, total)"""
    _ensure_dir()

    files = sorted(
        glob.glob(os.path.join(HISTORY_DIR, "*.json")),
        key=os.path.getmtime,
        reverse=True,
    )
    all_records = []
    for fp in files:
        try:
            with open(fp, "r", encoding="utf-8") as f:
                r = json.load(f)
        except Exception:
            continue

        # 用户隔离
        if username and r.get("username", "") != username:
            continue
        # 筛选
        if keyword and keyword.lower() not in r.get("filename", "").lower():
            continue
        if status and r.get("status", "") != status:
            continue
        all_records.append(r)

    total = len(all_records)
    start = (page - 1) * page_size
    end = start + page_size
    return all_records[start:end], total


def get_record(record_id: str) -> Optional[dict]:
    """获取单条记录"""
    fp = os.path.join(HISTORY_DIR, f"{record_id}.json")
    if not os.path.exists(fp):
        return None
    with open(fp, "r", encoding="utf-8") as f:
        return json.load(f)


def delete_record(record_id: str) -> bool:
    """删除单条记录"""
    fp = os.path.join(HISTORY_DIR, f"{record_id}.json")
    if not os.path.exists(fp):
        return False
    os.remove(fp)
    return True
