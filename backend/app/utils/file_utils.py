import os
import uuid
import aiofiles
from pathlib import Path
from fastapi import UploadFile
from app.config import settings


async def save_upload_file(file: UploadFile, upload_dir: str) -> str:
    """
    保存上传的文件到指定目录。

    参数:
        file: FastAPI UploadFile 对象
        upload_dir: 上传目录路径（相对于项目根目录）

    返回:
        str: 保存后的文件名
    """
    # 确保上传目录存在
    os.makedirs(upload_dir, exist_ok=True)

    # 生成唯一文件名，防止重名覆盖
    ext = Path(file.filename).suffix if file.filename else ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(upload_dir, filename)

    # 异步写入文件
    async with aiofiles.open(file_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    return filename


def ensure_directories():
    """
    确保应用运行所需的目录结构存在。
    根据 settings 配置创建 static、uploads、results 等目录。
    """
    directories = [
        settings.STATIC_DIR,
        settings.UPLOAD_DIR,
        settings.RESULT_DIR,
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)


def get_file_url(filename: str, subdir: str) -> str:
    """
    根据文件名和子目录生成静态文件的可访问 URL。

    参数:
        filename: 文件名
        subdir: 子目录路径，例如 "static/uploads" 或 "static/results"

    返回:
        str: 文件的 URL 路径（相对于静态文件挂载点）
    """
    # subdir 已经是相对于项目的路径（如 "static/uploads"），
    # 根据 FastAPI 的 StaticFiles 挂载，URL 路径需要去除 "static/" 前缀
    url_path = subdir.replace("static/", "", 1) if subdir.startswith("static/") else subdir
    return f"/static/{url_path}/{filename}"
