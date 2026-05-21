import os
import uuid
import aiofiles
from pathlib import Path
from fastapi import UploadFile
from app.config import settings
from app.services.minio_service import minio_service


async def save_upload_file(file: UploadFile, upload_dir: str) -> str:
    """
    保存上传的文件到本地临时目录, 同时上传到 MinIO。

    返回: 文件名 (不含路径)
    """
    os.makedirs(upload_dir, exist_ok=True)

    ext = Path(file.filename).suffix if file.filename else ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(upload_dir, filename)

    async with aiofiles.open(file_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    # 上传到 MinIO
    object_name = f"{upload_dir.replace('static/', '')}/{filename}"
    content_type = file.content_type or "application/octet-stream"
    minio_service.upload_file(file_path, object_name, content_type)

    return filename


def ensure_directories():
    """确保应用运行所需的本地目录结构存在。"""
    directories = [settings.STATIC_DIR, settings.UPLOAD_DIR, settings.RESULT_DIR]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)


def get_file_url(filename: str, subdir: str) -> str:
    """
    返回文件的 MinIO 预签名 URL。

    参数:
        filename: 文件名
        subdir: 子目录路径，例如 "static/uploads" 或 "static/results"

    返回:
        str: MinIO 预签名 URL (绝对路径)
    """
    object_name = f"{subdir.replace('static/', '')}/{filename}"
    return minio_service.get_presigned_url(object_name)
