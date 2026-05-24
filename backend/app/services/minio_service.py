import logging
from datetime import timedelta
from minio import Minio
from minio.error import S3Error
from app.config import settings

logger = logging.getLogger("rsod.minio")


class MinIOService:
    """MinIO 对象存储服务。"""

    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False,
        )
        if not self.client.bucket_exists(settings.MINIO_BUCKET):
            self.client.make_bucket(settings.MINIO_BUCKET)
            logger.info("创建 MinIO Bucket: %s", settings.MINIO_BUCKET)
        logger.info("MinIO 连接成功: %s/%s", settings.MINIO_ENDPOINT, settings.MINIO_BUCKET)

    def upload_file(self, local_path: str, object_name: str, content_type: str = "image/jpeg") -> str:
        """上传本地文件到 MinIO，返回 object_name。"""
        self.client.fput_object(
            settings.MINIO_BUCKET, object_name, local_path,
            content_type=content_type,
        )
        return object_name

    def get_presigned_url(self, object_name: str, expires_days: int = 7) -> str:
        """生成预签名 GET URL，有效期 N 天。"""
        return self.client.presigned_get_object(
            settings.MINIO_BUCKET, object_name,
            expires=timedelta(days=expires_days),
        )

    def get_public_url(self, object_name: str) -> str:
        """返回直接访问 URL（MinIO bucket 需设为 public）。"""
        return f"http://{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET}/{object_name}"


minio_service = MinIOService()
