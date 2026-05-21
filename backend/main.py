from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.api.detection import router as detection_router
from app.api.qa import router as qa_router
from app.api.user import router as user_router
from app.api.auth import router as auth_router
from app.api.video import router as video_router
try:
    from app.api.change_detection import router as cd_router
    _CD_AVAILABLE = True
except ImportError as e:
    print(f"[WARN] 变化检测模块加载失败: {e}")
    print("[WARN] 请先安装 Open-CD 依赖: cd engines/open-cd && pip install -e .")
    _CD_AVAILABLE = False
from app.utils.file_utils import ensure_directories

ensure_directories()

# --- 数据库初始化 ---
from app.database import engine, Base, SessionLocal
import app.models.db_models  # noqa: F401 — 注册 ORM 模型到 Base.metadata

# Debug 模式下热重载, 生产环境关闭
Base.metadata.create_all(bind=engine)


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
    finally:
        db.close()


seed_default_user()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="遥感目标检测平台后端API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")

app.include_router(detection_router, prefix="/api")
app.include_router(qa_router, prefix="/api")
app.include_router(user_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
if _CD_AVAILABLE:
    app.include_router(cd_router, prefix="/api")
app.include_router(video_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )