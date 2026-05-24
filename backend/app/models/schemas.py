from pydantic import BaseModel
from typing import List, Optional, Literal
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
    preview_image_url: str = ""
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
    preview_image_url: str = ""
    total_objects: int
    detection_time: float
    boxes: List[DetectionBox] = []
    detection_id: str = ""


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
    preview_image_url: str = ""
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
    chinese_name: str = ""
    description: Optional[str] = None


class TargetListResponse(BaseModel):
    success: bool
    message: str
    data: List[TargetItem]


# ── 标注导出 ──────────────────────────────────────

ExportFormat = Literal["coco", "yolo", "geojson"]


class ExportRequest(BaseModel):
    record_id: str
    format: ExportFormat = "coco"


# ── 检测统计 ──────────────────────────────────────

class ClassMetrics(BaseModel):
    class_name: str
    chinese_name: str
    count: int
    avg_confidence: float
    confidence_std: float


class DailyTrend(BaseModel):
    date: str
    count: int
    objects: int


class ModelUsage(BaseModel):
    model: str
    count: int
    objects: int


class ConfBin(BaseModel):
    range: str
    count: int


class EvaluationStats(BaseModel):
    total_images: int
    total_objects: int
    avg_objects_per_image: float
    avg_detection_time: float
    per_class: List[ClassMetrics]
    daily_trend: List[DailyTrend] = []
    model_distribution: List[ModelUsage] = []
    confidence_distribution: List[ConfBin] = []


class EvaluationResponse(BaseModel):
    success: bool
    message: str
    data: Optional[EvaluationStats] = None


# ── 认证 ──────────────────────────────────────

class LoginRequest(BaseModel):
    account: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


# ── 变化检测 ──────────────────────────────────────

class ChangeDetectionResult(BaseModel):
    detection_id: str
    image_a_url: str
    image_b_url: str
    result_url: str
    change_ratio: float
    detection_time: float
    model_name: str
    created_at: datetime


class ChangeDetectionResponse(BaseModel):
    success: bool
    message: str
    data: Optional[ChangeDetectionResult] = None


class BatchChangeItem(BaseModel):
    filename_a: str
    filename_b: str
    image_a_url: str
    image_b_url: str
    result_url: str
    change_ratio: float
    detection_time: float


class BatchChangeResponse(BaseModel):
    success: bool
    message: str
    data: List[BatchChangeItem]
    total_pairs: int
    total_time: float


class ChangeHistoryRecord(BaseModel):
    id: str
    filename_a: str
    filename_b: str
    image_a_url: str
    image_b_url: str
    result_url: str
    type: str
    status: str
    change_ratio: float
    detection_time: float
    model_name: str
    created_at: datetime


class ChangeHistoryListResponse(BaseModel):
    success: bool
    message: str
    data: List[ChangeHistoryRecord]
    total: int
    page: int
    page_size: int


class ChangeHistoryDetailResponse(BaseModel):
    success: bool
    message: str
    data: Optional[ChangeDetectionResult] = None