# Backend (FastAPI)

[English](03-backend-fastapi.md) | [中文](03-backend-fastapi.zh-CN.md)

## Technology Overview

- FastAPI as the REST API framework.
- Uvicorn as the ASGI runtime (`src/stock_analysis/main.py`).
- Pydantic + pydantic-settings for validation and centralized configuration.
- SQLAlchemy Async for database access.

## Implementation Details

### App Startup and Dependency Wiring

`lifespan` in `routers/app.py` initializes:

- OTel telemetry and metrics server
- Async SQLAlchemy engine/session
- PgQueuer connection pool
- Redis connection pool
- MCP client
- ChatAgent (with Postgres checkpointer)

### Router Structure

Routers are split by domain:

- `routers/stock.py`
- `routers/analysis.py`
- `routers/chat.py`
- `routers/report.py`

Router layer obtains services via dependency injection (database, cache, agent, MCP).

### Streaming Chat API

SSE is implemented via `/chat/start` + `/chat/stream`:

- Write runtime state to Redis at start
- Run background task invoking Agent and streaming tokens
- Use Redis list as buffer and PubSub for real-time delivery
- Return completion/error as SSE events

### Configuration System

`settings.py` defines database, MinIO, Redis, MCP, LLM, and observability settings, and derives computed endpoints via `cached_property`.

## Current Potential Issues

- Authentication/authorization is not present in the primary backend path.
- Many startup wiring items increase lifecycle coupling.
- Chat flow depends on Redis state machine with complex recovery paths.

## Improvement Directions

- Introduce unified auth (API Key / OAuth2 / JWT) with permission levels.
- Split `lifespan` initialization into smaller modules for maintainability/testability.
- Add idempotency keys and finer-grained error codes to chat flow.
- Add load/stability baselines for critical APIs.
