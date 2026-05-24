"""
用户中心 API — 全平台综合统计、资料管理、密码修改
"""

from datetime import datetime, date
from collections import Counter
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.db_models import User
from app.services.history_service import (
    get_all_records, get_all_cd_records, get_all_video_records,
)
from app.services.auth_service import hash_password, verify_password
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/user", tags=["user"])

# 纯结构化的模型展示名映射 — 只在前端 i18n 用
MODEL_DISPLAY = {
    "yolo11n-obb": "YOLO11n-OBB", "YOLO11n-OBB": "YOLO11n-OBB",
    "yolo11m-obb": "YOLO11m-OBB", "YOLO11m-OBB": "YOLO11m-OBB",
    "yolo11x-obb": "YOLO11x-OBB", "YOLO11x-OBB": "YOLO11x-OBB",
    "BAN-B0": "BAN-B0", "BAN-L0": "BAN-L0", "BAN-L1": "BAN-L1",
    "ban-b0": "BAN-B0", "ban-l0": "BAN-L0", "ban-l1": "BAN-L1",
    "yolo11n": "YOLO11n", "YOLO11n": "YOLO11n",
    "yolo11m": "YOLO11m", "YOLO11m": "YOLO11m",
    "yolo11x": "YOLO11x", "YOLO11x": "YOLO11x",
}


def _model_display(mn: str) -> str:
    return MODEL_DISPLAY.get(mn, mn.replace("_", " ").title())


def _model_type(mn: str) -> str:
    if any(k in mn.lower() for k in ("obb", "yolo11")):
        if "obb" in mn.lower():
            return "detection"
        return "video"
    if "ban" in mn.lower():
        return "change"
    return "detection"


@router.get("/profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    """全平台综合用户概览 — 按 user_id 聚合三类记录"""
    uid = current_user.id

    det_records = get_all_records(user_id=uid)
    cd_records = get_all_cd_records(user_id=uid)
    vid_records = get_all_video_records(user_id=uid)

    total_det = len(det_records)
    total_cd = len(cd_records)
    total_vid = len(vid_records)
    total_tasks = total_det + total_cd + total_vid

    det_objects = sum(r.get("total_objects", 0) for r in det_records)
    vid_objects = sum(r.get("total_objects", 0) for r in vid_records)
    total_objects = det_objects + vid_objects

    total_time = sum(r.get("detection_time", 0) for r in det_records + cd_records + vid_records)

    active_dates = set()
    for r in det_records + cd_records + vid_records:
        try:
            active_dates.add(datetime.fromisoformat(r["created_at"]).date())
        except Exception:
            pass

    # 模型使用 — 只返回 key / type / count，不拼中文标签
    model_counter = Counter()
    for r in det_records:
        mn = r.get("model_name", "")
        if mn:
            model_counter[(mn, "detection")] += 1
    for r in cd_records:
        mn = r.get("model_name", "")
        if mn:
            model_counter[(mn, "change")] += 1
    for r in vid_records:
        mn = r.get("model_name", "")
        if mn:
            model_counter[(mn, "video")] += 1

    top_entry = model_counter.most_common(1)
    top_model = _model_display(top_entry[0][0][0]) if top_entry else "-"

    # 类别分布（仅智能检测，按 class_name key）
    class_counter = Counter()
    for r in det_records:
        for cls in r.get("detected_classes", []):
            class_counter[cls] += 1

    # 任务类型分布 — 只返回 type + count，前端 i18n 映射 label
    task_dist = [
        {"type": "detection", "count": total_det},
        {"type": "change", "count": total_cd},
        {"type": "video", "count": total_vid},
    ]

    # 模型使用 — 只返回 key / type / count
    model_usage = [
        {"key": mn, "name": _model_display(mn), "type": mt, "count": cnt}
        for (mn, mt), cnt in model_counter.most_common()
    ]

    # 最近活动
    recent = []
    for r in det_records:
        recent.append({
            "record_type": "detection", "id": r["id"],
            "filename": r.get("filename", ""),
            "model_name": _model_display(r.get("model_name", "")),
            "created_at": r.get("created_at", ""),
        })
    for r in cd_records:
        recent.append({
            "record_type": "change", "id": r["id"],
            "filename": f'{r.get("filename_a","")} ↔ {r.get("filename_b","")}',
            "model_name": _model_display(r.get("model_name", "")),
            "created_at": r.get("created_at", ""),
        })
    for r in vid_records:
        recent.append({
            "record_type": "video", "id": r["id"],
            "filename": r.get("filename", ""),
            "model_name": _model_display(r.get("model_name", "")),
            "created_at": r.get("created_at", ""),
        })
    recent.sort(key=lambda x: x["created_at"], reverse=True)
    recent = recent[:5]
    for item in recent:
        try:
            item["date"] = datetime.fromisoformat(item["created_at"]).strftime("%m-%d %H:%M")
        except Exception:
            item["date"] = "-"

    earliest = None
    for r in det_records + cd_records + vid_records:
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
            "email": current_user.email,
            "created_at": earliest.isoformat() if earliest else date.today().isoformat(),
            "stats": {
                "total_tasks": total_tasks,
                "total_detections": total_det,
                "total_change_detections": total_cd,
                "total_video_detections": total_vid,
                "total_objects": total_objects,
                "total_time": round(total_time, 1),
                "active_days": len(active_dates),
                "top_model": top_model,
            },
            "task_dist": task_dist,
            "model_usage": model_usage,
            "class_dist": [
                {"name": cls, "count": cnt}
                for cls, cnt in class_counter.most_common(10)
            ],
            "recent_activity": recent,
        },
    }


@router.put("/profile")
def update_profile(data: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(404, "用户不存在")
    new_username = data.get("username", "").strip()
    new_email = data.get("email", "").strip()
    if new_username and new_username != user.username:
        if db.query(User).filter(User.username == new_username).first():
            raise HTTPException(400, "用户名已存在")
        user.username = new_username
    if new_email and new_email != user.email:
        if db.query(User).filter(User.email == new_email).first():
            raise HTTPException(400, "邮箱已注册")
        user.email = new_email
    db.commit()
    db.refresh(user)
    return {"success": True, "message": "资料更新成功",
            "data": {"username": user.username, "email": user.email}}


@router.put("/password")
def change_user_password(data: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    old_pwd = data.get("old_password", "")
    new_pwd = data.get("new_password", "")
    if not old_pwd or not new_pwd:
        raise HTTPException(400, "请输入旧密码和新密码")
    if len(new_pwd) < 6:
        raise HTTPException(400, "新密码至少 6 位")
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(404, "用户不存在")
    if not verify_password(old_pwd, user.hashed_password):
        raise HTTPException(400, "旧密码不正确")
    user.hashed_password = hash_password(new_pwd)
    db.commit()
    return {"success": True, "message": "密码修改成功"}
