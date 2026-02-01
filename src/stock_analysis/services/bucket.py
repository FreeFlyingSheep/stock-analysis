"""MinIO data store bucket service."""

import io
from http import HTTPStatus
from typing import TYPE_CHECKING

from fastapi import (
    HTTPException,
    Request,  # noqa: TC002
)

if TYPE_CHECKING:
    from minio import Minio
    from minio.helpers import ObjectWriteResult
    from urllib3 import BaseHTTPResponse


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


async def get_minio(request: Request) -> Minio:
    """Get MinIO client.

    Args:
        request: FastAPI request object for accessing app state.

    Returns:
        MinIO client instance.

    Raises:
        HTTPException: If MinIO client is not available.
    """
    bucket: Minio | None = getattr(request.app.state, "mc", None)
    if bucket is None:
        raise HTTPException(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            detail="Data store unavailable",
        )

    return bucket
