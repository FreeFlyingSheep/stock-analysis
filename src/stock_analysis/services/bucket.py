"""MinIO data store bucket service."""

import io
from typing import TYPE_CHECKING

from minio import Minio

from stock_analysis.settings import get_settings

if TYPE_CHECKING:
    from minio.helpers import ObjectWriteResult
    from urllib3 import BaseHTTPResponse

    from stock_analysis.settings import Settings


def init_buckets() -> Minio:
    """Initialize MinIO buckets for raw and processed data.

    Returns:
        MinIO client instance.
    """
    settings: Settings = get_settings()
    client = Minio(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_user,
        secret_key=settings.minio_password.get_secret_value(),
        secure=settings.minio_secure,
    )

    raw_bucket: str = settings.minio_bucket_raw
    processed_bucket: str = settings.minio_bucket_processed
    if not client.bucket_exists(raw_bucket):
        client.make_bucket(raw_bucket)
    if not client.bucket_exists(processed_bucket):
        client.make_bucket(processed_bucket)

    return client


class MinioBucketService:
    """MinIO bucket service for managing data storage."""

    _client: Minio
    """MinIO client instance."""

    def __init__(self, client: Minio) -> None:
        """Initialize the MinIO bucket service.

        Args:
            client: MinIO client instance.
        """
        self._client = client

    def get_object(self, bucket_name: str, object_name: str) -> bytes:
        """Retrieve an object from a MinIO bucket.

        Args:
            bucket_name: Name of the MinIO bucket.
            object_name: Name of the object to retrieve.

        Returns:
            The requested object data.
        """
        response: BaseHTTPResponse | None = None
        try:
            response = self._client.get_object(bucket_name, object_name)
            data: bytes = response.read()
        finally:
            if response is not None:
                response.close()
        return data

    def put_object(
        self, bucket_name: str, object_name: str, data: bytes, content_type: str
    ) -> ObjectWriteResult:
        """Store an object in a MinIO bucket.

        Args:
            bucket_name: Name of the MinIO bucket.
            object_name: Name of the object to store.
            data: Data to store in the object.
            content_type: MIME type of the object.

        Returns:
            Result of the object write operation.
        """
        result: ObjectWriteResult = self._client.put_object(
            bucket_name,
            object_name,
            io.BytesIO(data),
            length=len(data),
            content_type=content_type,
        )
        return result
