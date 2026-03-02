# 监测平台（含 Langfuse）

[English](08-observability-and-langfuse.md) | [中文](08-observability-and-langfuse.zh-CN.md)

## 技术介绍

- OpenTelemetry：应用埋点与遥测标准。
- Alloy：遥测汇聚与转发。
- Prometheus：指标采集与存储。
- Grafana：指标、日志、追踪统一可视化。
- Loki：日志聚合。
- Tempo：分布式追踪。
- Langfuse：Agent/LLM 调用链分析。

## 具体实现细节

### 应用侧埋点

`telemetry.py` 已接入：

- FastAPI
- HTTPX / requests
- SQLAlchemy / psycopg
- Redis
- LangChain

并启动独立 metrics HTTP server 暴露 `/metrics`。

### 采集与存储链路

`config.alloy` 中的核心流向：

- OTLP receiver 接收 app 遥测
- traces -> Tempo + Langfuse OTLP endpoint
- logs -> Loki
- metrics -> Prometheus remote write

### 运行时编排

`compose.yaml` 启动完整观测栈，并通过 healthcheck 依赖保证服务顺序。

### Langfuse 初始化

- `scripts/init_langfuse.py` 自动创建 Langfuse 数据库与 S3 bucket。
- `compose.yaml` 里 `langfuse-web` + `langfuse-worker` + `clickhouse` 共同组成运行环境。

## 当前可能存在的问题

- 指标体系尚缺“业务指标视角”说明（例如 Agent 成功率、检索命中率）。
- 日志与 trace 的关联字段规范（trace_id、thread_id）文档化不足。
- 告警规则虽有默认配置，但分级策略与响应流程未成体系。

## 后续改进思路

- 定义分层指标：系统指标、服务指标、业务指标、模型指标。
- 统一日志字段规范并打通 trace 关联查询。
- 建立告警分级与值班流程，补齐 runbook。
- 在 Langfuse 上建立 prompt 版本、实验分组与回归看板。
