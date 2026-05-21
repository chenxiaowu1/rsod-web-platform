"""
将现有 JSON 历史记录迁移到 PostgreSQL。
用法: python scripts/migrate_data.py
"""

import os
import sys
import json
import glob

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine, Base
from app.models.db_models import DetectionRecord, User  # noqa: F401
from app.services.auth_service import hash_password

HISTORY_DIR = "history"


def migrate():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. 创建默认 admin 用户
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            db.add(User(
                username="admin",
                email="admin@rsod.cn",
                hashed_password=hash_password("admin123"),
                role="admin",
            ))
            db.flush()
            print("[OK] 已创建 admin 用户")

        # 2. 创建迁移用占位用户 (归属孤儿记录)
        migrated = db.query(User).filter(User.username == "migrated").first()
        if not migrated:
            db.add(User(
                username="migrated",
                email="migrated@rsod.cn",
                hashed_password=hash_password("migrated"),
                role="user",
            ))
            db.flush()
            print("[OK] 已创建 migrated 用户")

        # 3. 构建 username -> user_id 映射
        users_map = {}
        for u in db.query(User).all():
            users_map[u.username] = u.id

        # 4. 迁移 JSON 记录
        json_files = sorted(glob.glob(os.path.join(HISTORY_DIR, "*.json")))
        count = 0
        skipped = 0

        for fp in json_files:
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                print(f"[WARN] 无法读取: {fp}")
                continue

            record_id = data.get("id") or data.get("detection_id")
            if not record_id:
                print(f"[WARN] 缺少 ID: {fp}")
                continue

            # 跳过已存在记录
            if db.query(DetectionRecord).filter(DetectionRecord.id == record_id).first():
                skipped += 1
                continue

            username = data.get("username", "") or "migrated"
            user_id = users_map.get(username, migrated.id)

            record = DetectionRecord(
                id=record_id,
                user_id=user_id,
                username=username,
                filename=data.get("filename", ""),
                image_url=data.get("image_url", ""),
                result_image_url=data.get("result_image_url", ""),
                record_type=data.get("type", "single"),
                status=data.get("status", "completed"),
                total_objects=data.get("total_objects", 0),
                detected_classes=data.get("detected_classes", []),
                detection_time=data.get("detection_time", 0.0),
                model_name=data.get("model_name", ""),
                boxes=data.get("boxes", []),
                created_at=data.get("created_at"),
            )
            db.add(record)
            count += 1

        db.commit()
        print(f"[DONE] 已迁移 {count} 条记录, 跳过 {skipped} 条已存在记录")

    finally:
        db.close()


if __name__ == "__main__":
    migrate()
