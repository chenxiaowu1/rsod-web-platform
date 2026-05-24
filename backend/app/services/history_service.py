"""
检测历史记录 — PostgreSQL 存储服务
"""

from typing import Optional
from sqlalchemy import desc
from app.database import SessionLocal
from app.models.db_models import DetectionRecord, ChangeDetectionRecord, VideoRecord


def save_record(detection_result, image_url: str, result_image_url: str,
                filename: str, model_name: str, username: str = "",
                user_id: int = 0, preview_image_url: str = "") -> dict:
    """保存一条检测记录到 PostgreSQL"""
    db = SessionLocal()
    try:
        boxes_data = [
            b.model_dump() if hasattr(b, 'model_dump') else b
            for b in detection_result.boxes
        ]
        record = DetectionRecord(
            id=detection_result.detection_id,
            user_id=user_id,
            username=username,
            filename=filename,
            image_url=image_url,
            result_image_url=result_image_url,
            preview_image_url=preview_image_url,
            record_type="single",
            status="completed",
            total_objects=detection_result.total_objects,
            detected_classes=list(set(b.class_name for b in detection_result.boxes)),
            detection_time=detection_result.detection_time,
            model_name=model_name,
            boxes=boxes_data,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record.to_dict()
    finally:
        db.close()


def list_records(page: int = 1, page_size: int = 10,
                 keyword: str = "", status: str = "",
                 username: str = "", user_id: int = 0) -> tuple[list[dict], int]:
    """分页查询记录"""
    db = SessionLocal()
    try:
        q = db.query(DetectionRecord)
        if user_id:
            q = q.filter(DetectionRecord.user_id == user_id)
        elif username:
            q = q.filter(DetectionRecord.username == username)
        if keyword:
            q = q.filter(DetectionRecord.filename.ilike(f"%{keyword}%"))
        if status:
            q = q.filter(DetectionRecord.status == status)

        total = q.count()
        records = (
            q.order_by(desc(DetectionRecord.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return [r.to_dict() for r in records], total
    finally:
        db.close()


def get_record(record_id: str) -> Optional[dict]:
    """获取单条记录"""
    db = SessionLocal()
    try:
        record = db.query(DetectionRecord).filter(DetectionRecord.id == record_id).first()
        return record.to_dict() if record else None
    finally:
        db.close()


def get_all_records(username: str = "", user_id: int = 0) -> list[dict]:
    """获取全部记录 (不分页), 用于统计"""
    db = SessionLocal()
    try:
        q = db.query(DetectionRecord)
        if user_id:
            q = q.filter(DetectionRecord.user_id == user_id)
        elif username:
            q = q.filter(DetectionRecord.username == username)
        records = q.order_by(desc(DetectionRecord.created_at)).all()
        return [r.to_dict() for r in records]
    finally:
        db.close()


def delete_record(record_id: str) -> bool:
    """删除单条记录"""
    db = SessionLocal()
    try:
        record = db.query(DetectionRecord).filter(DetectionRecord.id == record_id).first()
        if not record:
            return False
        db.delete(record)
        db.commit()
        return True
    finally:
        db.close()


# ── 变化检测记录 ───────────────────────────────

def save_cd_record(detection_id: str, user_id: int, username: str,
                   filename_a: str, filename_b: str,
                   image_a_url: str, image_b_url: str, result_url: str,
                   change_ratio: float, detection_time: float,
                   model_name: str) -> dict:
    db = SessionLocal()
    try:
        record = ChangeDetectionRecord(
            id=detection_id,
            user_id=user_id,
            username=username,
            filename_a=filename_a,
            filename_b=filename_b,
            image_a_url=image_a_url,
            image_b_url=image_b_url,
            result_url=result_url,
            record_type="single",
            status="completed",
            change_ratio=change_ratio,
            detection_time=detection_time,
            model_name=model_name,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record.to_dict()
    finally:
        db.close()


def list_cd_records(page: int = 1, page_size: int = 10,
                    username: str = "", user_id: int = 0) -> tuple[list[dict], int]:
    db = SessionLocal()
    try:
        q = db.query(ChangeDetectionRecord)
        if user_id:
            q = q.filter(ChangeDetectionRecord.user_id == user_id)
        elif username:
            q = q.filter(ChangeDetectionRecord.username == username)
        total = q.count()
        records = (
            q.order_by(desc(ChangeDetectionRecord.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return [r.to_dict() for r in records], total
    finally:
        db.close()


def get_cd_record(record_id: str):
    db = SessionLocal()
    try:
        record = db.query(ChangeDetectionRecord).filter(
            ChangeDetectionRecord.id == record_id).first()
        return record.to_dict() if record else None
    finally:
        db.close()


def delete_cd_record(record_id: str) -> bool:
    db = SessionLocal()
    try:
        record = db.query(ChangeDetectionRecord).filter(
            ChangeDetectionRecord.id == record_id).first()
        if not record:
            return False
        db.delete(record)
        db.commit()
        return True
    finally:
        db.close()


def get_all_cd_records(username: str = "", user_id: int = 0) -> list[dict]:
    db = SessionLocal()
    try:
        q = db.query(ChangeDetectionRecord)
        if user_id:
            q = q.filter(ChangeDetectionRecord.user_id == user_id)
        elif username:
            q = q.filter(ChangeDetectionRecord.username == username)
        return [r.to_dict() for r in q.order_by(desc(ChangeDetectionRecord.created_at)).all()]
    finally:
        db.close()


# ── 视频记录 ─────────────────────────────────

def save_video_record(video_id: str, user_id: int, username: str,
                      filename: str, total_frames: int, total_objects: int,
                      detection_time: float, fps_original: float,
                      model_name: str, source_type: str = "video",
                      result_url: str = "") -> dict:
    db = SessionLocal()
    try:
        record = VideoRecord(
            id=video_id, user_id=user_id, username=username,
            filename=filename, source_type=source_type,
            total_frames=total_frames,
            total_objects=total_objects, detection_time=detection_time,
            fps_original=fps_original, model_name=model_name,
            result_url=result_url,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record.to_dict()
    finally:
        db.close()


def list_video_records(page: int = 1, page_size: int = 10,
                       username: str = "", user_id: int = 0) -> tuple[list[dict], int]:
    db = SessionLocal()
    try:
        q = db.query(VideoRecord)
        if user_id:
            q = q.filter(VideoRecord.user_id == user_id)
        elif username:
            q = q.filter(VideoRecord.username == username)
        total = q.count()
        records = q.order_by(desc(VideoRecord.created_at)).offset(
            (page - 1) * page_size).limit(page_size).all()
        return [r.to_dict() for r in records], total
    finally:
        db.close()


def get_video_record(record_id: str):
    db = SessionLocal()
    try:
        r = db.query(VideoRecord).filter(VideoRecord.id == record_id).first()
        return r.to_dict() if r else None
    finally:
        db.close()


def get_all_video_records(username: str = "", user_id: int = 0) -> list[dict]:
    db = SessionLocal()
    try:
        q = db.query(VideoRecord)
        if user_id:
            q = q.filter(VideoRecord.user_id == user_id)
        elif username:
            q = q.filter(VideoRecord.username == username)
        return [r.to_dict() for r in q.order_by(desc(VideoRecord.created_at)).all()]
    finally:
        db.close()


def delete_video_record(record_id: str) -> bool:
    db = SessionLocal()
    try:
        r = db.query(VideoRecord).filter(VideoRecord.id == record_id).first()
        if not r:
            return False
        db.delete(r)
        db.commit()
        return True
    finally:
        db.close()
