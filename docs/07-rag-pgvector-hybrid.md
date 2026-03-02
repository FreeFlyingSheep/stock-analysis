# RAG + pgvector + Hybrid Retrieval

[English](07-rag-pgvector-hybrid.md) | [中文](07-rag-pgvector-hybrid.zh-CN.md)

## Technology Overview

- **RAG**: provides traceable evidence from annual reports for LLM answers.
- **pgvector**: vector storage and similarity retrieval.
- **pg_textsearch (BM25)**: keyword matching.
- **Hybrid + RRF**: fusion ranking between semantic and keyword results.

## Implementation Details

### Report Ingestion Pipeline

`agent/ingest.py` main steps:

- download PDFs from MinIO `raw` bucket
- extract text via PyMuPDF
- heading/paragraph split + overlap chunking
- compute embeddings
- write to `report_chunks` (`doc_id/doc_version/chunk_no` included)

Key chunking parameters:

- `CHUNK_MAX_CHARS = 300`
- `CHUNK_OVERLAP = 50`
- `PIPELINE_VERSION = v1.1.0`

### Retrieval Implementation

`services/report.py` provides three retrieval methods:

- `search_semantic`: cosine distance over vectors
- `search_bm25`: BM25 ranking
- `search_hybrid`: recalls from both and fuses with `RRF`

`agent/retriever.py` returns unified formatted chunk text.

### API and Agent Integration

- `POST /reports/retrieve` defaults to `retrieve_hybrid`
- Agent calls this capability through tools when needed

## Current Potential Issues

- Current chunking strategy is heuristic and may lose semantic integrity on complex report layouts.
- RRF parameters are fixed and not dynamically tuned by query type.
- Retrieval output is mostly text concatenation; structured evidence (page/paragraph confidence) is underused.

## Improvement Directions

- Introduce configurable chunking policies (section-aware, table-aware, layout-aware).
- Auto-tune `semantic_top_n/bm25_top_n/rrf_k` with offline eval datasets.
- Add a reranker (cross-encoder) to improve final relevance.
- Attach clearer citations in answers (source page, chunk id, document version).
- Introduce a dedicated vector database (e.g., Milvus) and benchmark feature/performance trade-offs.
