from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="user")
    avatar = Column(String(500), default="")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class DetectionRecord(Base):
    __tablename__ = "detection_records"

    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    username = Column(String(50), nullable=False)
    filename = Column(String(500), nullable=False)
    image_url = Column(String(500), default="")
    result_image_url = Column(String(500), default="")
    record_type = Column(String(20), default="single")
    status = Column(String(20), default="completed")
    total_objects = Column(Integer, default=0)
    detected_classes = Column(JSON, default=list)
    detection_time = Column(Float, default=0.0)
    model_name = Column(String(100), default="")
    boxes = Column(JSON, default=list)
    created_at = Column(DateTime, server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "detection_id": self.id,
            "username": self.username,
            "filename": self.filename,
            "image_url": self.image_url,
            "result_image_url": self.result_image_url,
            "type": self.record_type,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "total_objects": self.total_objects,
            "detected_classes": self.detected_classes or [],
            "detection_time": self.detection_time,
            "model_name": self.model_name,
            "boxes": self.boxes or [],
        }


class ChangeDetectionRecord(Base):
    __tablename__ = "change_detection_records"

    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    username = Column(String(50), nullable=False)
    filename_a = Column(String(500), default="")
    filename_b = Column(String(500), default="")
    image_a_url = Column(String(500), default="")
    image_b_url = Column(String(500), default="")
    result_url = Column(String(500), default="")
    record_type = Column(String(20), default="single")
    status = Column(String(20), default="completed")
    change_ratio = Column(Float, default=0.0)
    detection_time = Column(Float, default=0.0)
    model_name = Column(String(100), default="")
    created_at = Column(DateTime, server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "filename_a": self.filename_a,
            "filename_b": self.filename_b,
            "image_a_url": self.image_a_url,
            "image_b_url": self.image_b_url,
            "result_url": self.result_url,
            "type": self.record_type,
            "status": self.status,
            "change_ratio": self.change_ratio,
            "detection_time": self.detection_time,
            "model_name": self.model_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class VideoRecord(Base):
    __tablename__ = "video_records"

    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    username = Column(String(50), nullable=False)
    filename = Column(String(500), default="")
    total_frames = Column(Integer, default=0)
    total_objects = Column(Integer, default=0)
    detection_time = Column(Float, default=0.0)
    fps_original = Column(Float, default=0.0)
    model_name = Column(String(100), default="")
    status = Column(String(20), default="completed")
    created_at = Column(DateTime, server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "filename": self.filename,
            "total_frames": self.total_frames,
            "total_objects": self.total_objects,
            "detection_time": self.detection_time,
            "fps_original": self.fps_original,
            "model_name": self.model_name,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
