"""Ingestion module for stock analysis agent."""

import hashlib
import json
import re
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pymupdf  # type: ignore[import-untyped]
from minio.error import MinioException
from sqlalchemy.dialects.postgresql import insert

from stock_analysis.agent.model import Embeddings
from stock_analysis.models.report import ReportChunk
from stock_analysis.schemas.report import RawChunk, ReportChunkIn
from stock_analysis.services.bucket import MinioBucketService
from stock_analysis.settings import get_settings

if TYPE_CHECKING:
    from minio.datatypes import Object as MinioObject
    from sqlalchemy.dialects.postgresql import Insert
    from sqlalchemy.ext.asyncio import AsyncSession

    from stock_analysis.settings import Settings


PIPELINE_VERSION: str = "v1.0.0"
CHUNK_MAX_CHARS: int = 900
CHUNK_OVERLAP: int = 120
CHUNK_HEADING_RULE: str = "rule_v1"
MAX_HEADING_LEN: int = 40
MAX_HEADING_WORDS: int = 10
CHUNK_CONF: dict[str, Any] = {
    "max_chars": CHUNK_MAX_CHARS,
    "overlap": CHUNK_OVERLAP,
    "heading_rule": CHUNK_HEADING_RULE,
}


def _now_iso() -> str:
    """Return current UTC time in ISO 8601 format.

    Returns:
        UTC timestamp string, e.g. 2026-02-07T12:00:00+00:00.
    """
    return datetime.now(UTC).isoformat()


def _sha1(text: str) -> str:
    """Compute SHA-1 hex digest for text.

    Args:
        text: Input text to hash.

    Returns:
        SHA-1 hex digest string.
    """
    return hashlib.sha1(text.encode("utf-8")).hexdigest()  # noqa: S324


def _make_doc_id(object_key: str, doc_version: str) -> str:
    """Derive a stable document ID from source key and source version.

    Args:
        object_key: MinIO object key.
        doc_version: Version of the document.

    Returns:
        Deterministic document identifier.
    """
    return _sha1(f"{object_key}||{doc_version}")


def _clean_text(text: str) -> str:
    """Normalize whitespace in text.

    Args:
        text: Raw text.

    Returns:
        Text with compacted spaces/newlines and trimmed edges.
    """
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _is_heading(line: str) -> bool:
    """Check whether a line looks like a section heading.

    Args:
        line: Single line text.

    Returns:
        True if the line matches heading heuristics; otherwise False.
    """
    t: str = line.strip()
    if not t:
        return False
    if re.match(r"^\d+(\.\d+)*[\)\.]?\s+\S+", t):
        return True
    if re.match(
        r"^(第[一二三四五六七八九十百]+[章节]|Chapter|Part)\b",
        t,
        flags=re.IGNORECASE,
    ):
        return True
    return (
        len(t) <= MAX_HEADING_LEN
        and not re.search(r"[。.!?;\uFF1B]$", t)
        and t.isupper()
        and len(t.split()) <= MAX_HEADING_WORDS
    )


def _split_by_heading_paragraph(page_text: str) -> list[tuple[str, str]]:
    """Split page text into (heading, paragraph) units.

    Args:
        page_text: Raw text extracted from one PDF page.

    Returns:
        List of heading/paragraph pairs.
    """
    text: str = _clean_text(page_text)
    if not text:
        return []

    heading: str = "未命名章节"
    buf: list[str] = []
    units: list[tuple[str, str]] = []

    for line in text.splitlines():
        stripped: str = line.strip()
        if not stripped:
            buf = _append_unit(units, heading, buf)
            continue

        if _is_heading(stripped):
            buf = _append_unit(units, heading, buf)
            heading = stripped
            continue

        buf.append(stripped)

    _append_unit(units, heading, buf)
    return units


def _append_unit(
    units: list[tuple[str, str]],
    heading: str,
    buf: list[str],
) -> list[str]:
    """Append one cleaned paragraph unit and reset buffer.

    Args:
        units: Output (heading, paragraph) collection.
        heading: Current heading for buffered paragraph lines.
        buf: Buffered paragraph lines.

    Returns:
        Always returns a new empty list for caller-side buffer reset.
    """
    paragraph: str = _clean_text("\n".join(buf))
    if paragraph:
        units.append((heading, paragraph))
    return []


def _enforce_chunk_size(text: str, max_chars: int, overlap: int) -> list[str]:
    """Split text into bounded chunks with overlap.

    Args:
        text: Source text.
        max_chars: Maximum characters per chunk.
        overlap: Overlap size between adjacent chunks.

    Returns:
        Chunked text list.
    """
    text = _clean_text(text)
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    out: list[str] = []
    start: int = 0
    length: int = len(text)
    while start < length:
        end: int = min(start + max_chars, length)
        out.append(text[start:end])
        if end == length:
            break
        start = max(0, end - overlap)
    return out


def _stable_chunk_id(
    doc_id: str, page: int, heading: str, idx: int, content: str
) -> str:
    """Compute deterministic chunk ID.

    Args:
        doc_id: Document identifier.
        page: One-based page number.
        heading: Section heading.
        idx: Chunk index within document.
        content: Chunk content.

    Returns:
        Stable chunk identifier.
    """
    return _sha1(f"{doc_id}||{page}||{heading}||{idx}||{content[:120]}")


def _parse_pdf(
    pdf_path: str,
    doc_id: str,
    source_key: str,
    doc_version: str,
) -> list[RawChunk]:
    """Extract raw chunk schemas from a PDF file.

    Args:
        pdf_path: Local filesystem path to the PDF.
        doc_id: Document identifier.
        source_key: MinIO object key.
        doc_version: Version of the document.

    Returns:
        List of raw chunk schemas extracted from the PDF.
    """
    doc: pymupdf.Document = pymupdf.open(pdf_path)
    chunks: list[RawChunk] = []
    chunk_idx: int = 0

    for page_no in range(len(doc)):
        text = str(doc[page_no].get_text("text"))
        units: list[tuple[str, str]] = _split_by_heading_paragraph(text)
        for heading, paragraph in units:
            pieces: list[str] = _enforce_chunk_size(
                paragraph, max_chars=CHUNK_MAX_CHARS, overlap=CHUNK_OVERLAP
            )
            for piece in pieces:
                cid: str = _stable_chunk_id(
                    doc_id, page_no + 1, heading, chunk_idx, piece
                )
                chunks.append(
                    RawChunk(
                        chunk_id=cid,
                        doc_id=doc_id,
                        source_key=source_key,
                        source_version=doc_version,
                        page=page_no + 1,
                        heading=heading,
                        chunk_index=chunk_idx,
                        content=piece,
                    )
                )
                chunk_idx += 1
    doc.close()
    return chunks


class Ingestor:
    """Ingests PDF reports from MinIO into the vector database.

    Attributes:
        _db: Async database session for upserting report chunks.
        _bucket_service: MinIO bucket service instance.
        _embeddings: Embedding model wrapper.
        _raw_bucket: Name of the raw bucket containing PDFs.
        _processed_bucket: Name of the bucket for storing manifests and parsed data.
    """

    _db: AsyncSession
    _bucket_service: MinioBucketService
    _embeddings: Embeddings
    _raw_bucket: str
    _processed_bucket: str

    def __init__(
        self,
        db: AsyncSession,
        bucket_service: MinioBucketService | None = None,
        embeddings: Embeddings | None = None,
    ) -> None:
        """Initialize the ingestor.

        Args:
            db: Async database session for upserting report chunks.
            bucket_service: Optional MinIO bucket service.
            embeddings: Optional embeddings wrapper.
        """
        settings: Settings = get_settings()
        self._db = db
        self._bucket_service = bucket_service or MinioBucketService()
        self._embeddings = embeddings or Embeddings()
        self._raw_bucket = settings.minio_bucket_raw
        self._processed_bucket = settings.minio_bucket_processed

    def _list_raw_pdfs(self, prefix: str | None = None) -> list[MinioObject]:
        """List PDF objects in the raw bucket.

        Args:
            prefix: Optional key prefix filter.

        Returns:
            List of MinIO objects whose keys end with ".pdf".
        """
        return [
            obj
            for obj in self._bucket_service.list_objects(
                self._raw_bucket, prefix=prefix
            )
            if obj.object_name and obj.object_name.lower().endswith(".pdf")
        ]

    def _download_to_tempfile(self, object_key: str) -> str:
        """Download an object from the raw bucket to a temporary file.

        Args:
            object_key: MinIO object key.

        Returns:
            Path to the temporary file.
        """
        data: bytes = self._bucket_service.get_object(self._raw_bucket, object_key)
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(data)
            return tmp.name

    def _put_json(self, key: str, payload: dict[str, Any]) -> None:
        """Store a JSON document in the processed bucket.

        Args:
            key: Object key.
            payload: JSON-serialisable dictionary.
        """
        data: bytes = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self._bucket_service.put_object(
            self._processed_bucket, key, data, "application/json"
        )

    def _put_jsonl(self, key: str, rows: list[dict[str, Any]]) -> None:
        """Store JSONL data in the processed bucket.

        Args:
            key: Object key.
            rows: List of dictionaries, one per line.
        """
        body: bytes = "\n".join(json.dumps(r, ensure_ascii=False) for r in rows).encode(
            "utf-8"
        )
        self._bucket_service.put_object(
            self._processed_bucket, key, body, "application/x-ndjson"
        )

    def _get_json_or_none(self, key: str) -> dict[str, Any] | None:
        """Retrieve a JSON document from the processed bucket, or None.

        Args:
            key: Object key.

        Returns:
            Parsed JSON dictionary or None if not found.
        """
        try:
            data: bytes = self._bucket_service.get_object(self._processed_bucket, key)
            return json.loads(data.decode("utf-8"))
        except (MinioException, UnicodeDecodeError, json.JSONDecodeError):
            return None

    def _manifest_fields(
        self,
        object_key: str,
        doc_version: str,
        settings: Settings,
    ) -> dict[str, Any]:
        """Build shared manifest fields.

        Args:
            object_key: Source MinIO object key.
            doc_version: Version of the document.
            settings: Application settings.

        Returns:
            Common manifest fields used for success/failed records.
        """
        return {
            "source_key": object_key,
            "doc_version": doc_version,
            "pipeline_version": PIPELINE_VERSION,
            "embed_model": settings.llm_embedding_model,
            "embed_dim": settings.llm_embedding_dimension,
            "chunk_conf": CHUNK_CONF,
        }

    def _should_skip(
        self, old_manifest: dict[str, Any], object_key: str, doc_version: str
    ) -> bool:
        """Check whether ingestion can be skipped for idempotency.

        Args:
            old_manifest: Existing manifest content.
            object_key: Source MinIO object key.
            doc_version: Version of the document.

        Returns:
            True when the existing manifest indicates a matching successful run.
        """
        settings: Settings = get_settings()
        expected: dict[str, Any] = {
            **self._manifest_fields(object_key, doc_version, settings),
            "status": "success",
        }
        return all(old_manifest.get(k) == v for k, v in expected.items())

    async def _upsert_chunks(  # noqa: PLR0913
        self,
        chunks: list[RawChunk],
        vectors: list[list[float]],
        stock_id: int,
        fiscal_year: int,
        report_type: str,
        content_type: str,
        doc_version: str,
    ) -> int:
        """Upsert report chunks into the database.

        Args:
            chunks: List of raw chunks.
            vectors: Corresponding embedding vectors.
            stock_id: ID of the stock this report belongs to.
            fiscal_year: Fiscal year of the report.
            report_type: Report type label.
            content_type: MIME type of the source document.
            doc_version: Version string of the pipeline run.

        Returns:
            Number of rows inserted or updated.
        """
        chunk_inputs: list[dict[str, Any]] = [
            ReportChunkIn(
                stock_id=stock_id,
                fiscal_year=fiscal_year,
                report_type=report_type,
                content_type=content_type,
                doc_id=chunk.chunk_id,
                doc_version=doc_version,
                chunk_no=chunk.chunk_index,
                content=chunk.content,
                embedding=vec,
            ).model_dump()
            for chunk, vec in zip(chunks, vectors, strict=False)
        ]

        stmt: Insert = insert(ReportChunk).values(chunk_inputs)
        stmt = stmt.on_conflict_do_update(
            index_elements=[ReportChunk.doc_id],
            set_={
                "content": stmt.excluded.content,
                "embedding": stmt.excluded.embedding,
                "doc_version": stmt.excluded.doc_version,
            },
        )
        await self._db.execute(stmt)
        await self._db.flush()
        return len(chunk_inputs)

    async def _process_one(  # noqa: PLR0913
        self,
        object_key: str,
        source_version: str,
        stock_id: int,
        fiscal_year: int,
        report_type: str,
        content_type: str = "application/pdf",
    ) -> None:
        """Process a single PDF from the raw bucket.

        Args:
            object_key: MinIO object key.
            source_version: MinIO object version ID.
            stock_id: Stock ID for the report.
            fiscal_year: Fiscal year of the report.
            report_type: Report type label.
            content_type: MIME type of the source.

        Raises:
            Exception: Re-raises any ingestion error after writing error artifacts.
        """
        settings: Settings = get_settings()
        doc_version: str = source_version
        doc_id: str = _make_doc_id(object_key, doc_version)
        artifact_prefix: str = f"{object_key.removesuffix('.pdf')}"
        mkey: str = f"{artifact_prefix}/manifest.json"
        pkey: str = f"{artifact_prefix}/chunks.jsonl"
        ekey: str = f"{artifact_prefix}/error.json"
        manifest_fields: dict[str, Any] = self._manifest_fields(
            object_key, doc_version, settings
        )

        old_manifest: dict[str, Any] | None = self._get_json_or_none(mkey)
        if old_manifest and self._should_skip(old_manifest, object_key, doc_version):
            return

        start_ts: str = _now_iso()
        tmp_pdf: str | None = None
        chunk_count: int = 0
        inserted_rows: int = 0
        parsed_written: bool = False
        try:
            tmp_pdf = self._download_to_tempfile(object_key)
            chunks: list[RawChunk] = _parse_pdf(
                tmp_pdf, doc_id, object_key, doc_version
            )
            chunk_count = len(chunks)

            if not chunks:
                empty_manifest: dict[str, Any] = {
                    "doc_id": doc_id,
                    **manifest_fields,
                    "chunk_count": 0,
                    "inserted_rows": 0,
                    "status": "success",
                    "start_time": start_ts,
                    "end_time": _now_iso(),
                    "message": "No text chunks extracted",
                }
                self._put_json(mkey, empty_manifest)
                return

            self._put_jsonl(pkey, [c.model_dump() for c in chunks])
            parsed_written = True

            texts: list[str] = [c.content for c in chunks]
            vectors: list[list[float]] = [
                await self._embeddings.aquery(t) for t in texts
            ]

            inserted_rows = await self._upsert_chunks(
                chunks,
                vectors,
                stock_id=stock_id,
                fiscal_year=fiscal_year,
                report_type=report_type,
                content_type=content_type,
                doc_version=doc_version,
            )

            success_manifest: dict[str, Any] = {
                "doc_id": doc_id,
                **manifest_fields,
                "chunk_count": len(chunks),
                "inserted_rows": inserted_rows,
                "status": "success",
                "start_time": start_ts,
                "end_time": _now_iso(),
                "artifacts": {"parsed_jsonl": pkey},
            }
            self._put_json(mkey, success_manifest)

        except Exception as e:
            err: dict[str, Any] = {
                "doc_id": doc_id,
                **manifest_fields,
                "status": "failed",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "time": _now_iso(),
            }
            self._put_json(ekey, err)

            failed_manifest: dict[str, Any] = {
                "doc_id": doc_id,
                **manifest_fields,
                "chunk_count": chunk_count,
                "inserted_rows": inserted_rows,
                "status": "failed",
                "start_time": start_ts,
                "end_time": _now_iso(),
            }
            if parsed_written:
                failed_manifest["artifacts"] = {"parsed_jsonl": pkey}
            self._put_json(mkey, failed_manifest)
            raise

        finally:
            if tmp_pdf:
                tmp_pdf_path: Path = Path(tmp_pdf)
                if tmp_pdf_path.exists():
                    tmp_pdf_path.unlink()

    async def ingest(
        self,
        stock_id: int,
        fiscal_year: int,
        report_type: str,
        content_type: str = "application/pdf",
        prefix: str | None = None,
    ) -> int:
        """Ingest all PDF reports from the raw bucket.

        Args:
            stock_id: Stock ID for the reports.
            fiscal_year: Fiscal year of the reports.
            report_type: Report type label.
            content_type: MIME type of the source documents.
            prefix: Optional MinIO key prefix to filter objects.

        Returns:
            Number of PDFs processed (including skipped).
        """
        objects: list[MinioObject] = self._list_raw_pdfs(prefix=prefix)
        count: int = 0
        for obj in objects:
            if obj.object_name is None or obj.version_id is None:
                continue
            object_key: str = obj.object_name
            await self._process_one(
                object_key,
                obj.version_id,
                stock_id,
                fiscal_year,
                report_type,
                content_type,
            )
            count += 1
        return count
