import io
import json
from typing import TYPE_CHECKING

import pymupdf  # type: ignore[import-untyped]
import pytest
from minio.commonconfig import ENABLED
from minio.versioningconfig import VersioningConfig

from stock_analysis.agent.ingest import Ingestor
from stock_analysis.agent.model import Embeddings
from stock_analysis.services.bucket import MinioBucketService
from stock_analysis.settings import get_settings

if TYPE_CHECKING:
    from langchain_community.embeddings import FakeEmbeddings
    from minio import Minio
    from sqlalchemy.ext.asyncio import AsyncSession

    from stock_analysis.models.stock import Stock
    from stock_analysis.settings import Settings


@pytest.fixture
def tiny_pdf_bytes() -> bytes:
    """Create a minimal single-page PDF and return its bytes."""
    doc: pymupdf.Document = pymupdf.open()
    page: pymupdf.Page = doc.new_page()
    page.insert_text((50, 50), "Test content for PDF")
    return doc.write()


@pytest.fixture
def bucket_service(minio_client: Minio, tiny_pdf_bytes: bytes) -> MinioBucketService:
    settings: Settings = get_settings()
    minio_client.make_bucket(settings.minio_bucket_raw)
    minio_client.set_bucket_versioning(
        settings.minio_bucket_raw, VersioningConfig(ENABLED)
    )
    minio_client.make_bucket(settings.minio_bucket_processed)
    minio_client.put_object(
        settings.minio_bucket_raw,
        "test.pdf",
        io.BytesIO(tiny_pdf_bytes),
        len(tiny_pdf_bytes),
        content_type="application/pdf",
    )
    return MinioBucketService(mc=minio_client)


@pytest.fixture
def embeddings(fake_embeddings: FakeEmbeddings) -> Embeddings:
    return Embeddings(embeddings=fake_embeddings)


@pytest.mark.asyncio
async def test_ingest(
    seed_stocks: list[Stock],
    bucket_service: MinioBucketService,
    async_session: AsyncSession,
    embeddings: Embeddings,
) -> None:
    ingestor = Ingestor(
        db=async_session,
        bucket_service=bucket_service,
        embeddings=embeddings,
    )
    count: int = await ingestor.ingest(
        stock_id=seed_stocks[0].id, fiscal_year=2024, report_type="annual"
    )
    assert count == 1

    manifest_bytes: bytes = bucket_service.get_object(
        bucket_name=get_settings().minio_bucket_processed,
        object_name="test/manifest.json",
    )
    manifest: dict = json.loads(manifest_bytes.decode("utf-8"))
    assert manifest is not None
    assert manifest["status"] == "success"
    assert manifest["chunk_count"] >= 1
    assert manifest["inserted_rows"] >= 1
