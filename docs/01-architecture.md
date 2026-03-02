# Architecture Design

[English](01-architecture.md) | [中文](01-architecture.zh-CN.md)

## Goals and Boundaries

This project focuses on fundamental analysis for A-share stocks. Core capabilities include:

- Multi-source data ingestion (CNInfo + Yahoo)
- Rule-based scoring
- Report RAG retrieval and Q&A
- External services through API + Web + MCP
- End-to-end observability and offline evaluation

Out of scope (not covered by the current repository):

- Live trading execution
- Investment advisory and risk guarantee
- Multi-tenant isolation and permission system

## Layering and Module Decomposition

From the code structure, the project currently follows a "layered by responsibility + split by domain" approach:

- Interface layer: `routers/*` (HTTP API)
- Business layer: `services/*` (business orchestration)
- Integration layer: `adapters/*` (third-party adapters)
- Data layer: `models/*` + `schemas/*` + Alembic
- Async task layer: `jobs/*` + PgQueuer
- Agent layer: `agent/*` (LangGraph, RAG, MCP calls)

This structure is already clear under `src/stock_analysis/`, making it easier to add new endpoints and data sources.

## Runtime Architecture

In the Docker Compose setup, the main service chain is:

- `web` (SvelteKit)
- `api` (FastAPI)
- `worker` (PgQueuer executor)
- `mcp` (FastMCP OpenAPI-to-MCP)
- `postgres` (with pgvector + pg_textsearch + zhparser)
- `redis` (cache, lock, PubSub)
- `minio` (report object storage)
- Observability stack: `alloy + prometheus + grafana + loki + tempo + langfuse`

Related files: `compose.yaml`, `configs/docker/*`.

## Key Design Principles

### Async-First

- API, database, cache, and task execution all use async paths.
- FastAPI lifecycle centralizes initialization of pools and dependencies (DB Session, Redis Pool, MCP Client, Agent).

Value: better concurrency throughput and reduced I/O blocking.

### Decoupling External Dependencies

- CNInfo/Yahoo are encapsulated in the Adapter layer.
- Agent and tool calling are abstracted through MCP.

Value: smaller impact when replacing data sources or tool protocols.

### Separation Between Online Queries and Tasks

- Online queries are served by API.
- Crawling/analysis runs asynchronously through PgQueuer.

Value: prevents slow jobs from affecting online APIs.

### Observability First

- OTel auto-instrumentation (FastAPI/HTTPX/SQLAlchemy/Redis/LangChain).
- Alloy aggregates telemetry and exports to Tempo/Loki/Prometheus, with optional forwarding to Langfuse.

Value: easier debugging of agent chains, API latency, and task failures.

## Technology Choices: Pros and Cons

### FastAPI + SQLAlchemy Async

Pros:

- Mature async ecosystem; high development efficiency for API definition and validation.
- Auto-generated OpenAPI, suitable for MCP integration.

Cons:

- Async call-chain debugging is more complex than sync.
- Higher requirements for connection pool and session-boundary management.

### PostgreSQL + pgvector + pg_textsearch

Pros:

- Structured data and vector retrieval live in a single database.
- BM25 + vector + RRF hybrid retrieval is straightforward and cost-effective.

Cons:

- As report scale grows, pressure on single-DB read/write and index maintenance will increase.
- Vector index and sharding strategy still require continuous optimization.

### PgQueuer + Redis

Pros:

- PgQueuer reuses PostgreSQL and keeps deployment cost low.
- Redis supports cache, distributed locks, SSE buffering, and PubSub.

Cons:

- Queue state, retry policy, and dead-letter governance are not yet well documented/platformized.
- Redis has many use cases; capacity and TTL governance need to be more refined.

### LangGraph + MCP + RAG

Pros:

- Graph orchestration fits multi-node decision flows (routing, retrieval, rewrite, tool use).
- MCP standardizes tool exposure and reuse.

Cons:

- Long chains increase tuning and stability costs.
- Under high concurrency, token cost and latency become more sensitive.

### SvelteKit Frontend

Pros:

- Lightweight component/state overhead, with efficient initial load and interaction.
- Straightforward implementation for streaming SSE chat.

Cons:

- Global state management needs more standardization in complex scenarios.
- API contract evolution needs stronger automated verification.

## Current Architecture Gaps

- No formal architecture decision records (ADR) or boundary constraint documents.
- Security domain (authentication, authorization, fine-grained permissions) is not yet systematic.
- Capacity planning metrics for API, offline tasks, and agent evaluation are not yet formalized.

## Improvement Directions

- Establish an ADR process (one document per key technical decision).
- Introduce unified authentication and tenant/user-level permission model.
- Define capacity model and SLOs: API P95, queue backlog, agent success rate, retrieval quality.
- Add performance baselines and CI regression gates for critical paths.
