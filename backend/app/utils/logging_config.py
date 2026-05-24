"""
统一日志配置
支持彩色控制台输出 + 文件持久化。
"""
import logging
import sys
from pathlib import Path
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器 — 终端有颜色，文件中无颜色。"""

    COLORS = {
        'DEBUG': '\033[36m',     # 青色
        'INFO': '\033[32m',      # 绿色
        'WARNING': '\033[33m',   # 黄色
        'ERROR': '\033[31m',     # 红色
        'CRITICAL': '\033[35m',  # 紫色
        'RESET': '\033[0m',
    }

    def format(self, record):
        if record.levelname in self.COLORS and sys.stdout.isatty():
            record.levelname = (
                f"{self.COLORS[record.levelname]}"
                f"{record.levelname}"
                f"{self.COLORS['RESET']}"
            )
        return super().format(record)


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    log_dir: Optional[Path] = None,
    use_colors: bool = True,
    name: Optional[str] = "rsod",
) -> logging.Logger:
    """
    统一日志配置。

    参数:
        level: DEBUG / INFO / WARNING / ERROR / CRITICAL
        log_file: 日志文件名，None 则仅控制台输出
        log_dir: 日志目录，None 则使用项目 logs/
        use_colors: 是否使用 ANSI 彩色输出
        name: logger 名称
    """
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    if use_colors and sys.stdout.isatty():
        formatter = ColoredFormatter(log_format, datefmt=date_format)
    else:
        formatter = logging.Formatter(log_format, datefmt=date_format)

    log_level = getattr(logging, level.upper(), logging.INFO)

    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    logger.handlers.clear()

    # 控制台 handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(log_level)
    console.setFormatter(formatter)
    logger.addHandler(console)

    # 文件 handler
    if log_file:
        if log_dir is None:
            from app.utils.paths import Paths
            log_dir = Paths.logs()
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_dir / log_file, encoding='utf-8')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
        logger.addHandler(file_handler)

    return logger


def setup_production_logging() -> logging.Logger:
    """生产环境：INFO 级别 + 文件持久化。"""
    return setup_logging(level="INFO", log_file="app.log")


def setup_debug_logging() -> logging.Logger:
    """调试环境：DEBUG 级别 + 文件持久化。"""
    return setup_logging(level="DEBUG", log_file="debug.log")
