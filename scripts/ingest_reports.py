"""Import report PDF files to MinIO based on the reports CSV."""

import asyncio
import logging
from typing import TYPE_CHECKING

from minio import Minio
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)

from stock_analysis.agent.ingest import Ingestor
from stock_analysis.services.bucket import MinioBucketService
from stock_analysis.settings import get_settings

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

    from stock_analysis.settings import Settings

logger: logging.Logger = logging.getLogger(__name__)


async def ingest_reports(db: AsyncSession, client: Minio, bucket: str) -> None:
    """Ingest report PDF files from MinIO.

    Args:
        db: AsyncSession instance for database operations.
        client: MinIO client instance.
        bucket: Name of the MinIO bucket.
    """
    prefix: str = "reports/"
    bucket_service = MinioBucketService(client)
    ingestor = Ingestor(db, bucket_service)

    for obj in bucket_service.list_objects(bucket, prefix=prefix):
        if obj.object_name is None:
            logger.warning("Object name is missing for object: %s", obj)
            continue

        if obj.is_latest != "true":
            logger.info(
                "Skipping object %s because it is not the latest version.",
                obj.object_name,
            )
            continue

        await ingestor.ingest(obj.object_name)
        logger.info("Ingested report: %s", obj.object_name)


async def main() -> None:
    """Import report files from data/reports to MinIO."""
    settings: Settings = get_settings()
    logging.basicConfig(level=settings.log_level)

    engine: AsyncEngine = create_async_engine(
        settings.database_url_with_psycopg,
        echo=settings.debug,
    )
    async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(
        engine,
        expire_on_commit=False,
    )

    client = Minio(
        settings.minio_endpoint,
        access_key=settings.minio_user,
        secret_key=settings.minio_password.get_secret_value(),
        secure=settings.minio_secure,
    )

    async with async_session() as session:
        await ingest_reports(session, client, settings.minio_bucket_raw)


if __name__ == "__main__":
    asyncio.run(main())
