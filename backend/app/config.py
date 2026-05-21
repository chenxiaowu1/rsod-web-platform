# from pydantic import BaseModel
# from typing import Optional
# import os


# class Settings(BaseModel):
#     APP_NAME: str = "RSOD Detection Platform"
#     APP_VERSION: str = "1.0.0"
#     DEBUG: bool = True
    
#     HOST: str = "0.0.0.0"
#     PORT: int = 8000
    
#     STATIC_DIR: str = "static"
#     UPLOAD_DIR: str = "static/uploads"
#     RESULT_DIR: str = "static/results"
    
#     YOLO_MODEL_PATH: str = "yolo11n.pt"
#     CONFIDENCE_THRESHOLD: float = 0.5
#     IOU_THRESHOLD: float = 0.45
    
#     CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]


# def get_settings() -> Settings:
#     settings = Settings()
    
#     env_file = ".env"
#     if os.path.exists(env_file):
#         with open(env_file, "r") as f:
#             for line in f:
#                 line = line.strip()
#                 if line and not line.startswith("#"):
#                     key, value = line.split("=", 1)
#                     if hasattr(settings, key):
#                         try:
#                             setattr(settings, key, type(getattr(settings, key))(value))
#                         except ValueError:
#                             pass
    
#     return settings


# settings = get_settings()

from pydantic import BaseModel
from typing import Optional
import os


class Settings(BaseModel):
    APP_NAME: str = "RSOD Detection Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    STATIC_DIR: str = "static"
    UPLOAD_DIR: str = "static/uploads"
    RESULT_DIR: str = "static/results"

    YOLO_MODEL_PATH: str = "app/models/detection/yolo11x-obb.pt"
    DEFAULT_MODEL: str = "yolo11m-obb"
    CONFIDENCE_THRESHOLD: float = 0.5
    IOU_THRESHOLD: float = 0.45

    # LLM 配置
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.deepseek.com"
    LLM_MODEL: str = "deepseek-chat"

    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "rsod_user"
    DB_PASSWORD: str = "rsod_password"
    DB_NAME: str = "rsod_db"

    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "rsod-bucket"

    # JWT
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Engine URLs
    DET_ENGINE_URL: str = "http://localhost:8001"
    CD_ENGINE_URL: str = "http://localhost:8002"
    VIDEO_ENGINE_URL: str = "http://localhost:8003"
    DEFAULT_DET_MODEL: str = "yolo11m-obb"
    DEFAULT_CD_MODEL: str = "ban-b0"

    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


def get_settings() -> Settings:
    settings = Settings()
    
    env_file = ".env"
    if os.path.exists(env_file):
        # 修复：显式指定 UTF-8 编码，避免 Windows 下 GBK 解码错误
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    if hasattr(settings, key):
                        try:
                            # 尝试转换值类型为当前属性类型
                            current_type = type(getattr(settings, key))
                            if current_type == bool:
                                setattr(settings, key, value.lower() in ("true", "1", "yes"))
                            elif current_type == list:
                                # 简单处理：假设列表用逗号分隔，例如 ["a","b"]
                                if value.startswith("[") and value.endswith("]"):
                                    import ast
                                    setattr(settings, key, ast.literal_eval(value))
                                else:
                                    setattr(settings, key, [v.strip() for v in value.split(",") if v.strip()])
                            else:
                                setattr(settings, key, current_type(value))
                        except (ValueError, SyntaxError):
                            # 转换失败则保留默认值
                            pass
    
    return settings


settings = get_settings()