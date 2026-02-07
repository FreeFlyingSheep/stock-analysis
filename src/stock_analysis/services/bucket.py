"""MinIO data store bucket service."""

import io
from typing import TYPE_CHECKING

from minio import Minio

from stock_analysis.settings import get_settings

if TYPE_CHECKING:
    from collections.abc import Iterator

    from minio.datatypes import Object as MinioObject
    from minio.helpers import ObjectWriteResult
    from urllib3 import BaseHTTPResponse

    from stock_analysis.settings import Settings


class MinioBucketService:
    """MinIO bucket service for managing data storage.

    Attributes:
        _mc: MinIO client instance.
    """

    _mc: Minio

    def __init__(self, mc: Minio | None = None) -> None:
        """Initialize the MinIO bucket service.

        Args:
            mc: MinIO client instance.
        """
        if mc is not None:
            self._mc = mc
            return

        settings: Settings = get_settings()
        self._mc = Minio(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_user,
            secret_key=settings.minio_password.get_secret_value(),
            secure=settings.minio_secure,
        )

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
            response = self._mc.get_object(bucket_name, object_name)
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
        result: ObjectWriteResult = self._mc.put_object(
            bucket_name,
            object_name,
            io.BytesIO(data),
            length=len(data),
            content_type=content_type,
        )
        return result

    def list_objects(
        self, bucket_name: str, prefix: str | None = None
    ) -> Iterator[MinioObject]:
        """List objects from a MinIO bucket."""
        return self._mc.list_objects(
            bucket_name=bucket_name,
            prefix=prefix,
            recursive=True,
            include_version=True,
        )
