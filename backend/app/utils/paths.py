"""
路径管理模块
通过 Marker File 定位项目根目录，集中管理所有路径。
"""
from pathlib import Path
from typing import Optional
import inspect


def find_project_root(start_path=None, marker_file=".rsod_platform"):
    """从当前位置向上查找项目根目录（通过 marker file）。"""

    if start_path is None:
        frame = inspect.stack()[1]
        start_path = Path(frame.filename).parent

    current = Path(start_path).resolve()
    for parent in [current] + list(current.parents):
        if (parent / marker_file).exists():
            return parent

    raise FileNotFoundError(
        f"找不到 {marker_file} 标记文件，请确认在 rsod-web-platform 项目内"
    )


class Paths:
    """项目路径集中管理。"""

    _root: Optional[Path] = None
    _env: str = "development"

    @classmethod
    def set_env(cls, env: str):
        cls._env = env
        cls._root = None

    @classmethod
    def root(cls) -> Path:
        if cls._root is None:
            cls._root = find_project_root()
        return cls._root

    # ── 后端目录 ──

    @classmethod
    def backend(cls) -> Path:
        return cls.root() / "backend"

    @classmethod
    def app(cls) -> Path:
        return cls.backend() / "app"

    # ── 静态资源 ──

    @classmethod
    def static(cls) -> Path:
        return cls.backend() / "static"

    @classmethod
    def uploads(cls) -> Path:
        return cls.static() / "uploads"

    @classmethod
    def results(cls) -> Path:
        return cls.static() / "results"

    # ── 模型文件 ──

    @classmethod
    def detection_models(cls) -> Path:
        return cls.app() / "models" / "detection"

    @classmethod
    def cd_models(cls) -> Path:
        return cls.app() / "models" / "change_detection"

    @classmethod
    def video_models(cls) -> Path:
        return cls.app() / "models" / "video"

    # ── 引擎目录 ──

    @classmethod
    def engines(cls) -> Path:
        return cls.root() / "engines"

    # ── 配置文件 ──

    @classmethod
    def env_file(cls) -> Path:
        suffix = f".{cls._env}" if cls._env != "development" else ""
        return cls.backend() / f".env{suffix}"

    # ── 日志目录 ──

    @classmethod
    def logs(cls) -> Path:
        return cls.root() / "logs"

    # ── 工具方法 ──

    @classmethod
    def ensure_dir(cls, path: Path) -> Path:
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def init_all_dirs(cls):
        for d in [cls.uploads(), cls.results(), cls.logs()]:
            cls.ensure_dir(d)
