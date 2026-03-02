# Middleware (PgQueuer + Redis)

[English](04-middleware-pgqueuer-redis.md) | [中文](04-middleware-pgqueuer-redis.zh-CN.md)

## Technology Overview

- **PgQueuer**: PostgreSQL-based task queue for async crawling and analysis jobs.
- **Redis**: cache, distributed locks, PubSub messaging, and streaming session buffering.

## Implementation Details

### PgQueuer Job Orchestration

`jobs/pgqueuer.py` registers key entrypoints:

- `crawl_stock_data`
- `analyze_stock_data`
- `update_stock_data`
- `analyze_all_stock_data`

`update_stock_data` creates crawl child jobs in batch and staggers execution via `execute_after`.

### Worker Runtime Shape

- Worker startup initializes DB sessions, adapters, rule engine, and telemetry.
- Shared dependencies are injected into jobs via `resources`.

### Redis Responsibilities in Chat Flow

- `run:*` keys control concurrent starts for the same message.
- `lock:*` distributed locks prevent concurrent stream writes.
- `buf:*` lists buffer historical token events.
- `channel:*` PubSub pushes tokens to SSE consumers in real time.

## Current Potential Issues

- Dead-letter queue and job-priority governance for PgQueuer are not documented.
- Redis keyspace has prefixes but lacks unified capacity governance and key observability dashboards.
- Lock-renewal flow may leave dirty keys in extreme failure scenarios.

## Improvement Directions

- Add retry strategy matrix by error type.
- Add task-level metrics: queue latency, failure rate, retry count, final success rate.
- Build Redis key lifecycle governance (TTL standards, periodic scans, alert thresholds).
- Add stronger chat recovery mechanisms (e.g., incremental replay validation after reconnect).
- Enable Redis HA (Sentinel or cluster) and validate failover behavior.
