"""
用户中心 API — 个人资料与统计数据 (按 JWT 用户隔离)
"""

from datetime import datetime, date
from collections import Counter
from fastapi import APIRouter, Depends
from app.models.db_models import User
from app.services.history_service import get_all_records
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/user", tags=["user"])

CLASS_CN = {
    "plane": "飞机", "ship": "船舶", "storage-tank": "储罐",
    "baseball-diamond": "棒球场", "tennis-court": "网球场",
    "basketball-court": "篮球场", "ground-track-field": "田径场",
    "harbor": "港口", "bridge": "桥梁", "large-vehicle": "大型车辆",
    "small-vehicle": "小型车辆", "helicopter": "直升机",
    "roundabout": "环岛", "soccer-ball-field": "足球场", "swimming-pool": "游泳池",
}

MODEL_DISPLAY = {
    "yolo11n-obb": "YOLO11 Nano",
    "yolo11m-obb": "YOLO11 Medium",
    "yolo11x-obb": "YOLO11 XLarge",
}


@router.get("/profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    """获取当前用户的个人资料与检测统计"""
    records = get_all_records(username=current_user.username)

    total_detections = len(records)
    total_objects = sum(r.get("total_objects", 0) for r in records)
    success_count = sum(1 for r in records if r.get("status") == "completed")

    active_dates = set()
    for r in records:
        try:
            active_dates.add(datetime.fromisoformat(r["created_at"]).date())
        except Exception:
            pass

    class_counter = Counter()
    for r in records:
        for cls in r.get("detected_classes", []):
            class_counter[cls] += 1

    model_counter = Counter()
    for r in records:
        mn = r.get("model_name", "")
        if mn:
            model_counter[mn] += 1

    top = model_counter.most_common(1)
    top_model = MODEL_DISPLAY.get(top[0][0], top[0][0]) if top else "-"

    earliest = None
    for r in records:
        try:
            d = datetime.fromisoformat(r["created_at"]).date()
            if earliest is None or d < earliest:
                earliest = d
        except Exception:
            pass

    return {
        "success": True,
        "data": {
            "username": current_user.username,
            "role": current_user.role,
            "avatar": current_user.avatar,
            "created_at": earliest.isoformat() if earliest else date.today().isoformat(),
            "stats": {
                "total_detections": total_detections,
                "total_objects": total_objects,
                "active_days": len(active_dates),
                "success_rate": round(success_count / total_detections * 100, 1) if total_detections else 0,
                "top_model": top_model,
            },
            "class_dist": [{"name": cls, "cn_name": CLASS_CN.get(cls, cls), "count": cnt}
                           for cls, cnt in class_counter.most_common(10)],
            "model_usage": [{"key": mn, "name": MODEL_DISPLAY.get(mn, mn), "count": cnt}
                            for mn, cnt in model_counter.most_common()],
        },
    }
