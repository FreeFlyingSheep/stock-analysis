# Data Directory

[English](README.md) | [中文](README.zh-CN.md)

This directory stores seed data, sample API responses, and demo report files used by the project for local initialization, testing, and RAG-related workflows.

## Purpose

The `data/` directory is used for:

- Bootstrapping the database with base stock metadata
- Loading optional local SQL seed data during initialization
- Providing sample API payloads for parser/testing work
- Providing a small set of annual report PDFs for demo/RAG ingestion

## Layout

- `stocks.csv`: Base A-share stock list and industry classification data (CSV seed file)
- `data.sql`: Optional SQL seed script (automatically imported by `scripts/init_db.sh` if present)
- `api/`: Sample raw API responses from CNInfo and Yahoo Finance
- `reports/`: Demo annual report PDFs and report metadata CSV
- `README.md` / `README.zh-CN.md`: This directory documentation

## How It Is Used

### Database initialization

`scripts/init_db.sh` uses files in this directory to initialize local data:

1. Recreates the database schema
2. Imports stock data from `data/stocks.csv`
3. Installs PgQueuer jobs
4. Imports `data/data.sql` (if the file exists)

### Full migration/bootstrap flow

`scripts/migrate.sh` runs a full bootstrap sequence and then imports report files:

```bash
./scripts/migrate.sh
```

This script is destructive and will drop existing database data.

### Report ingestion for RAG

The sample PDFs in `data/reports/` can be uploaded and ingested for retrieval/embedding workflows (see `data/reports/README.md`).

Common commands:

```bash
uv run scripts/import_reports.py
uv run scripts/ingest_reports.py
```

## File Details

### `stocks.csv`

Contains A-share company master data and industry classification columns (Chinese headers), for example:

- Company code and short name
- Industry category codes/names (category/subcategory/major category)

This file is the primary CSV seed used by `scripts/import_csv.py` during database initialization.

### `data.sql`

Optional large SQL dump/seed file for additional local data.

- Loaded automatically by `scripts/init_db.sh` when present
- Useful for restoring a known local dataset quickly
- May be large; keep only when needed for local development/testing

## Subdirectories

### `api/`

Contains sample JSON responses for upstream APIs used by adapters and parsers.

- Documentation: `data/api/README.md`
- Includes provider folders like `cninfo/` and `yahoo/`

### `reports/`

Contains a small demo set of annual report PDFs plus `reports.csv` metadata.

- Documentation: `data/reports/README.md`
- Intended for testing/demo (not a full report archive)
