from typing import TYPE_CHECKING

from stock_analysis.services.bucket import MinioBucketService

if TYPE_CHECKING:
    from minio import Minio
    from minio.helpers import ObjectWriteResult


def test_put_and_get_object(minio_client: Minio) -> None:
    bucket_service = MinioBucketService(minio_client)
    bucket_name = "test-bucket"
    object_name = "test-object.txt"
    data = b"Hello, MinIO!"
    content_type = "text/plain"

    assert not minio_client.bucket_exists(bucket_name)
    minio_client.make_bucket(bucket_name)
    assert minio_client.bucket_exists(bucket_name)

    result: ObjectWriteResult = bucket_service.put_object(
        bucket_name, object_name, data, content_type
    )
    assert result.bucket_name == bucket_name
    assert result.object_name == object_name

    retrieved_data: bytes = bucket_service.get_object(bucket_name, object_name)
    assert retrieved_data == data
