from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.utils.logging_config import setup_logging, setup_debug_logging, setup_production_logging
from app.utils.paths import Paths
from app.api.detection import router as detection_router
from app.api.qa import router as qa_router
from app.api.user import router as user_router
from app.api.auth import router as auth_router
from app.api.video import router as video_router

try:
    from app.api.change_detection import router as cd_router
    _CD_AVAILABLE = True
except ImportError as e:
    _CD_AVAILABLE = False

from app.utils.file_utils import ensure_directories
from app.services.redis_service import redis_service

# ── 统一日志初始化 ──
if settings.DEBUG:
    logger = setup_debug_logging()
else:
    logger = setup_production_logging()

logger.info("启动 %s v%s (env=%s)", settings.APP_NAME, settings.APP_VERSION, settings.ENV)

# ── 安全校验 ──
if settings.ENV != "development" and settings.SECRET_KEY == "change-me-in-production":
    logger.critical("生产模式下 SECRET_KEY 仍为默认值，拒绝启动！请设置环境变量 SECRET_KEY")
    raise RuntimeError("SECRET_KEY 必须配置为非默认值")
if settings.SECRET_KEY == "change-me-in-production":
    logger.warning("⚠ SECRET_KEY 为默认值，仅开发模式允许，生产环境务必修改！")

# ── 目录初始化 ──
Paths.init_all_dirs()
logger.info("目录结构初始化完成")

# ── 数据库初始化 ──
from app.database import engine, Base, SessionLocal
from sqlalchemy import text
import app.models.db_models  # noqa: F401

Base.metadata.create_all(bind=engine)
logger.info("数据库表初始化完成")

# ── 数据库迁移（补已存在表的新增字段）──
def _migrate_db():
    """对存量表补新增字段，幂等执行。"""
    migrations = {
        "detection_records": [
            ("preview_image_url", "VARCHAR(500) DEFAULT ''"),
        ],
        "video_records": [
            ("source_type", "VARCHAR(20) DEFAULT 'video'"),
            ("result_url", "VARCHAR(500) DEFAULT ''"),
        ],
    }
    with engine.connect() as conn:
        for table, cols in migrations.items():
            for col_name, col_def in cols:
                    try:
                        conn.execute(text(
                            f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col_name} {col_def}"
                        ))
                        conn.commit()
                    except Exception:
                        conn.rollback()
_migrate_db()
logger.info("数据库迁移检查完成")


def seed_default_user():
    """确保默认管理员账号存在 (admin/admin123)"""
    from app.models.db_models import User
    from app.services.auth_service import hash_password

    db = SessionLocal()
    try:
        if not db.query(User).filter(User.username == "admin").first():
            db.add(User(
                username="admin",
                email="admin@rsod.cn",
                hashed_password=hash_password("admin123"),
                role="admin",
            ))
            db.commit()
            logger.info("默认管理员账号已创建")
    finally:
        db.close()


seed_default_user()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="遥感目标检测平台后端API",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 全局异常处理器 ──
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.exceptions import (
    http_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler,
)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)
logger.info("全局异常处理器已注册")

app.mount("/static", StaticFiles(directory=str(Paths.static())), name="static")

app.include_router(detection_router, prefix="/api")
app.include_router(qa_router, prefix="/api")
app.include_router(user_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
if _CD_AVAILABLE:
    app.include_router(cd_router, prefix="/api")
    logger.info("变化检测模块已加载")
else:
    logger.warning("变化检测模块加载失败: Open-CD 依赖未安装")

app.include_router(video_router, prefix="/api")
logger.info("视频检测模块已加载")


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.on_event("startup")
async def startup():
    await redis_service.connect()


@app.on_event("shutdown")
async def shutdown():
    await redis_service.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
