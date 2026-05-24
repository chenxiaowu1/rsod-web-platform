"""
数据验证子系统
可扩展的验证管道：CheckContext → 验证器注册表 → 分级报告。
"""
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
import logging

logger = logging.getLogger("rsod.validation")

# ── 常量 ────────────────────────────────────────

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tif', '.tiff', '.geotiff', '.ntf', '.img'}
MAX_FILE_SIZE_MB = 500


class CheckLevel(Enum):
    PASS = "pass"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class CheckResult:
    level: CheckLevel
    message: str
    check_name: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CheckContext:
    """验证上下文 — 验证器的输入数据。"""
    file_path: Optional[Path] = None
    file_bytes: Optional[bytes] = None
    model_name: Optional[str] = None
    conf_threshold: Optional[float] = None
    iou_threshold: Optional[float] = None
    extra: Dict[str, Any] = field(default_factory=dict)


# ── 验证器注册表 ──────────────────────────────────

_validators: Dict[str, Callable] = {}


def register_validator(name: str):
    """装饰器：注册验证器到全局注册表。"""
    def decorator(func):
        _validators[name] = func
        func._validator_name = name
        return func
    return decorator


def list_validators() -> List[str]:
    return list(_validators.keys())


def run_validators(ctx: CheckContext, validator_names: Optional[List[str]] = None) -> List[CheckResult]:
    """运行指定（或全部注册的）验证器。"""
    names = validator_names or list_validators()
    results = []
    for name in names:
        validator = _validators.get(name)
        if not validator:
            continue
        try:
            check_results = validator(ctx)
            for r in check_results:
                if not r.check_name:
                    r.check_name = name
            results.extend(check_results)
        except Exception as e:
            results.append(CheckResult(
                level=CheckLevel.ERROR,
                message=f"验证器 {name} 执行异常: {e}",
                check_name=name,
            ))
    return results


def has_errors(results: List[CheckResult]) -> bool:
    return any(r.level == CheckLevel.ERROR for r in results)


class DataValidator:
    """数据验证器主类。"""

    def __init__(self, ctx: CheckContext):
        self.ctx = ctx

    def validate(self, validator_names: Optional[List[str]] = None) -> List[CheckResult]:
        return run_validators(self.ctx, validator_names)

    def validate_and_report(self, validator_names: Optional[List[str]] = None) -> bool:
        """执行验证并输出报告，返回是否通过（无 ERROR）。"""
        results = self.validate(validator_names)
        self._print_report(results)
        return not has_errors(results)

    def _print_report(self, results: List[CheckResult]):
        icons = {CheckLevel.PASS: "PASS", CheckLevel.INFO: "INFO",
                 CheckLevel.WARNING: "WARN", CheckLevel.ERROR: "ERROR"}
        logger.info("=" * 60)
        logger.info("数据验证报告")
        logger.info("=" * 60)
        for r in results:
            logger.info("[%s] %s: %s", icons.get(r.level, "?"), r.check_name, r.message)
        errors = sum(1 for r in results if r.level == CheckLevel.ERROR)
        warnings = sum(1 for r in results if r.level == CheckLevel.WARNING)
        logger.info("总计: %d 项 | 错误: %d | 警告: %d", len(results), errors, warnings)
        logger.info("-" * 60)


# ── 内置验证器 ─────────────────────────────────────

@register_validator("file_extension")
def check_file_extension(ctx: CheckContext) -> List[CheckResult]:
    """检查文件扩展名是否在支持列表中。"""
    if not ctx.file_path:
        return []
    ext = ctx.file_path.suffix.lower()
    if ext in ALLOWED_EXTENSIONS:
        return [CheckResult(CheckLevel.PASS, f"文件格式 {ext} 受支持")]
    return [CheckResult(CheckLevel.ERROR, f"不支持的文件格式: {ext}，支持: {sorted(ALLOWED_EXTENSIONS)}")]


@register_validator("file_size")
def check_file_size(ctx: CheckContext) -> List[CheckResult]:
    """检查文件大小是否在限制内。"""
    size_bytes = None
    if ctx.file_path and ctx.file_path.exists():
        size_bytes = ctx.file_path.stat().st_size
    elif ctx.file_bytes:
        size_bytes = len(ctx.file_bytes)

    if size_bytes is None:
        return []

    size_mb = size_bytes / (1024 * 1024)
    if size_mb <= MAX_FILE_SIZE_MB:
        return [CheckResult(CheckLevel.PASS, f"文件大小 {size_mb:.1f}MB，在限制内")]
    return [CheckResult(CheckLevel.ERROR, f"文件过大: {size_mb:.1f}MB > {MAX_FILE_SIZE_MB}MB")]


@register_validator("image_readable")
def check_image_readable(ctx: CheckContext) -> List[CheckResult]:
    """检查图片是否可被 OpenCV 正常读取。"""
    if not ctx.file_path or not ctx.file_path.exists():
        return []

    try:
        import cv2
        img = cv2.imread(str(ctx.file_path))
        if img is None:
            return [CheckResult(CheckLevel.ERROR, f"无法读取图片: {ctx.file_path.name}，文件可能已损坏")]
        h, w = img.shape[:2]
        channels = img.shape[2] if len(img.shape) > 2 else 1
        return [CheckResult(CheckLevel.PASS, f"图片可读，尺寸: {w}x{h}，通道: {channels}")]
    except Exception as e:
        return [CheckResult(CheckLevel.ERROR, f"读取图片异常: {e}")]


@register_validator("detection_params")
def check_detection_params(ctx: CheckContext) -> List[CheckResult]:
    """检查检测参数是否在有效范围内。"""
    results = []
    if ctx.conf_threshold is not None:
        if 0 < ctx.conf_threshold < 1:
            results.append(CheckResult(CheckLevel.PASS, f"置信度阈值 {ctx.conf_threshold} 有效"))
        else:
            results.append(CheckResult(CheckLevel.ERROR, f"置信度阈值 {ctx.conf_threshold} 不在 (0, 1) 范围内"))
    if ctx.iou_threshold is not None:
        if 0 < ctx.iou_threshold < 1:
            results.append(CheckResult(CheckLevel.PASS, f"IoU 阈值 {ctx.iou_threshold} 有效"))
        else:
            results.append(CheckResult(CheckLevel.ERROR, f"IoU 阈值 {ctx.iou_threshold} 不在 (0, 1) 范围内"))
    return results


@register_validator("model_exists")
def check_model_exists(ctx: CheckContext) -> List[CheckResult]:
    """检查指定模型文件是否存在。"""
    if not ctx.model_name:
        return []

    from app.utils.paths import Paths
    candidates = [
        Paths.detection_models() / f"{ctx.model_name}.pt",
        Paths.detection_models() / f"{ctx.model_name}.pth",
        Paths.cd_models() / f"{ctx.model_name}.pth",
        Paths.video_models() / f"{ctx.model_name}.pt",
    ]
    for mp in candidates:
        if mp.exists():
            return [CheckResult(CheckLevel.PASS, f"模型文件存在: {mp.relative_to(Paths.root())}")]

    return [CheckResult(CheckLevel.ERROR,
            f"未找到模型文件: {ctx.model_name}，已搜索: {[p.name for p in candidates]}")]
