import io
from datetime import timedelta
from typing import Any

from minio import Minio
from minio.error import S3Error

from packages.core.exceptions import StorageError


class MinIOStorage:
    """Object storage backed by MinIO (S3-compatible)."""

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        secure: bool = False,
    ) -> None:
        self._client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)

    @classmethod
    def from_settings(cls, bucket: str | None = None) -> "MinIOStorage":
        """Build a MinIOStorage directly from app settings, for contexts
        without FastAPI DI (e.g. Celery workers). Ensures the given bucket
        (default: settings.MINIO_BUCKET_ASSETS) exists before returning."""
        from apps.api.config import get_settings

        settings = get_settings()
        storage = cls(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        storage.ensure_bucket(bucket or settings.MINIO_BUCKET_ASSETS)
        return storage

    def ensure_bucket(self, bucket: str) -> None:
        try:
            if not self._client.bucket_exists(bucket):
                self._client.make_bucket(bucket)
        except S3Error as e:
            raise StorageError(f"Cannot ensure bucket '{bucket}': {e}") from e

    def upload_bytes(
        self,
        bucket: str,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
    ) -> str:
        try:
            self._client.put_object(
                bucket,
                key,
                io.BytesIO(data),
                length=len(data),
                content_type=content_type,
                metadata=metadata or {},
            )
            return key
        except S3Error as e:
            raise StorageError(f"Upload failed for '{key}': {e}") from e

    def get_object_bytes(self, bucket: str, key: str) -> bytes:
        try:
            response = self._client.get_object(bucket, key)
            try:
                return response.read()
            finally:
                response.close()
                response.release_conn()
        except S3Error as e:
            raise StorageError(f"Cannot read object '{key}': {e}") from e

    def get_presigned_url(self, bucket: str, key: str, expires: int = 3600) -> str:
        try:
            return self._client.presigned_get_object(bucket, key, expires=timedelta(seconds=expires))
        except S3Error as e:
            raise StorageError(f"Cannot generate presigned URL for '{key}': {e}") from e

    def delete_object(self, bucket: str, key: str) -> None:
        try:
            self._client.remove_object(bucket, key)
        except S3Error as e:
            raise StorageError(f"Cannot delete '{key}': {e}") from e

    def object_exists(self, bucket: str, key: str) -> bool:
        try:
            self._client.stat_object(bucket, key)
            return True
        except S3Error:
            return False
