# Observability Platform (Including Langfuse)

[English](08-observability-and-langfuse.md) | [中文](08-observability-and-langfuse.zh-CN.md)

## Technology Overview

- OpenTelemetry: app instrumentation and telemetry standard.
- Alloy: telemetry aggregation and forwarding.
- Prometheus: metrics collection and storage.
- Grafana: unified visualization for metrics/logs/traces.
- Loki: log aggregation.
- Tempo: distributed tracing.
- Langfuse: analysis for Agent/LLM call chains.

## Implementation Details

### Application-Side Instrumentation

`telemetry.py` currently instruments:

- FastAPI
- HTTPX / requests
- SQLAlchemy / psycopg
- Redis
- LangChain

It also starts a standalone metrics HTTP server exposing `/metrics`.

### Collection and Storage Pipeline

Core flow in `config.alloy`:

- OTLP receiver ingests app telemetry
- traces -> Tempo + Langfuse OTLP endpoint
- logs -> Loki
- metrics -> Prometheus remote write

### Runtime Orchestration

`compose.yaml` starts the full observability stack, with healthcheck dependencies controlling startup order.

### Langfuse Initialization

- `scripts/init_langfuse.py` automatically creates Langfuse database and S3 bucket.
- In `compose.yaml`, `langfuse-web` + `langfuse-worker` + `clickhouse` form the runtime.

## Current Potential Issues

- Metrics system still lacks business-level perspective (e.g., agent success rate, retrieval hit quality).
- Correlation-field standardization between logs and traces (`trace_id`, `thread_id`) is under-documented.
- Alert rules exist, but severity strategy and incident response process are not systematic.

## Improvement Directions

- Define layered metrics: system, service, business, and model metrics.
- Standardize logging fields and enable trace-linked queries.
- Establish alert severity model, on-call process, and runbooks.
- Build prompt-versioning, experiment grouping, and regression dashboards in Langfuse.
