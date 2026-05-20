from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class DetectionBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float
    class_id: int
    class_name: str


class DetectionResult(BaseModel):
    detection_id: str
    image_url: str
    result_image_url: str
    boxes: List[DetectionBox]
    total_objects: int
    detection_time: float
    model_name: str
    created_at: datetime


class SingleDetectionResponse(BaseModel):
    success: bool
    message: str
    data: Optional[DetectionResult] = None


class BatchDetectionItem(BaseModel):
    """批量检测中每张图的结果"""
    filename: str
    image_url: str
    result_image_url: str
    total_objects: int
    detection_time: float
    boxes: List[DetectionBox] = []


class BatchDetectionResponse(BaseModel):
    success: bool
    message: str
    data: List[BatchDetectionItem]
    total_files: int
    total_objects: int
    total_time: float


# ── 历史记录 ──────────────────────────────────────

class HistoryItem(BaseModel):
    id: str
    image_url: str
    result_image_url: str
    total_objects: int
    created_at: datetime
    model_name: str


class HistoryRecord(BaseModel):
    """单条检测历史记录"""
    id: str
    filename: str
    image_url: str
    result_image_url: str
    type: str                        # single / batch
    status: str                      # completed / processing / failed
    created_at: datetime
    total_objects: int
    detected_classes: List[str]      # 检测到的类别名称列表
    detection_time: float
    model_name: str


class HistoryListResponse(BaseModel):
    success: bool
    message: str
    data: List[HistoryRecord]
    total: int
    page: int
    page_size: int


class HistoryDetailResponse(BaseModel):
    success: bool
    message: str
    data: Optional[DetectionResult] = None


# ── AI 问答 ──────────────────────────────────────

class QAMessage(BaseModel):
    role: str                       # user / assistant
    content: str


class QARequest(BaseModel):
    question: str
    history: Optional[List[QAMessage]] = []


class QAResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None     # { "answer": "...", "references": [...] }


# ── 目标库 ──────────────────────────────────────

class TargetItem(BaseModel):
    id: int
    name: str
    chinese_name: str
    description: Optional[str] = None


class TargetListResponse(BaseModel):
    success: bool
    message: str
    data: List[TargetItem]