import uuid
import aiofiles
from pathlib import Path
from fastapi import UploadFile
from app.config import settings
from app.services.minio_service import minio_service


async def save_upload_file(file: UploadFile, upload_dir: str) -> str:
    """
    保存上传文件到本地目录，同时上传到 MinIO。

    返回: 文件名（不含路径）
    """
    upload_path = Path(upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename).suffix if file.filename else ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = upload_path / filename

    async with aiofiles.open(file_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    object_name = f"{upload_path.name}/{filename}"
    content_type = file.content_type or "application/octet-stream"
    minio_service.upload_file(str(file_path), object_name, content_type)

    return filename


def ensure_directories():
    """确保应用运行所需的本地目录结构存在。"""
    from app.utils.paths import Paths
    Paths.init_all_dirs()


def get_file_url(filename: str, subdir: str) -> str:
    """
    返回文件的 MinIO 预签名 URL。

    参数:
        filename: 文件名
        subdir: 子目录路径，例如 "static/uploads" 或 "static/results"

    返回:
        str: MinIO 预签名 URL (绝对路径)
    """
    dir_name = Path(subdir).name
    object_name = f"{dir_name}/{filename}"
    return minio_service.get_presigned_url(object_name)
