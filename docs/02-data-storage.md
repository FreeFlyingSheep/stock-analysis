# Data Storage (Alembic + PostgreSQL + MinIO)

[English](02-data-storage.md) | [中文](02-data-storage.zh-CN.md)

## Technology Overview

- **PostgreSQL 18**: Primary relational database for stocks, analysis, chat, and report chunks.
- **Alembic**: Schema migration and versioning.
- **pgvector**: Vector field support for report chunks and semantic retrieval.
- **pg_textsearch + zhparser**: Chinese BM25 indexing.
- **MinIO**: S3-compatible object storage for raw reports and processed artifacts.

## Implementation Details

### Initialization and Migrations

- `scripts/init_db.sh` workflow:
  - Drop/create database
  - Run Alembic `upgrade head`
  - Import initial stock CSV
  - Install PgQueuer metadata
- `scripts/create_db.py` creates extensions:
  - `vector`
  - `pg_textsearch`
  - `zhparser`
  - and creates `chinese` text search configuration.

### Report Vector and Full-Text Table

- `report_chunks` table is defined in `models/report.py`.
- `embedding` column type: `VECTOR(dim=<configured dimension>)`.
- BM25 index `idx_report_chunks_bm25` uses `postgresql_using="bm25"`.

### MinIO Buckets and Data Flow

- Raw report bucket: `<prefix>raw`
- Processed result bucket: `<prefix>processed`
- `scripts/import_reports.py`: uploads PDFs from `data/reports/reports.csv` to `reports/<year>/<type>/<stock_code>.pdf`.
- `scripts/ingest_reports.py` + `agent/ingest.py`:
  - pull MinIO objects
  - parse and chunk PDFs
  - generate embeddings
  - upsert into `report_chunks`

### Langfuse-Related Storage

- `scripts/init_langfuse.py` creates the PostgreSQL database and MinIO bucket required by Langfuse.

## Current Potential Issues

- `init_db.sh` / `migrate.sh` include destructive default behavior (drop and recreate DB), which is error-prone.
- As chunk data grows, index bloat and query degradation risks increase.
- MinIO lifecycle tiering and archive strategy are not yet documented.
- Database backup/recovery drill workflow is not documented.

## Improvement Directions

- Separate "development reset scripts" from "production incremental migration scripts".
- Add partition/archive strategy for `report_chunks` (by year, stock, document version).
- Define backup strategy (RPO/RTO) and operational drill scripts.
- Add MinIO lifecycle policies and cleanup jobs (historical versions, expired artifacts).
- Enable HA deployment for PostgreSQL and MinIO (primary-replica, distributed MinIO).
