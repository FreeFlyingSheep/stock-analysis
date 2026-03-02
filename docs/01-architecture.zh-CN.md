# 架构设计

[English](01-architecture.md) | [中文](01-architecture.zh-CN.md)

## 目标与边界

本项目聚焦 A 股基础面分析，核心能力包括：

- 多源数据采集（CNInfo + Yahoo）
- 规则驱动打分
- 报告 RAG 检索与问答
- API + Web + MCP 对外服务
- 全链路可观测与离线评测

非目标（当前仓库未覆盖）：

- 实盘交易执行
- 投顾建议与风险兜底
- 多租户隔离与权限体系

## 分层与模块划分

从代码结构看，当前采用了“按职责分层 + 按域拆分”的组织方式：

- 接口层：`routers/*`（HTTP API）
- 业务层：`services/*`（业务编排）
- 集成层：`adapters/*`（第三方接口适配）
- 数据层：`models/*` + `schemas/*` + Alembic
- 异步任务层：`jobs/*` + PgQueuer
- 智能体层：`agent/*`（LangGraph、RAG、MCP 调用）

这套结构在 `src/stock_analysis/` 下已经较清晰，便于新增接口和新增数据源。

## 运行时架构

在 Docker Compose 场景下，主要服务链路如下：

- `web`（SvelteKit）
- `api`（FastAPI）
- `worker`（PgQueuer 执行器）
- `mcp`（FastMCP OpenAPI 转 MCP）
- `postgres`（含 pgvector + pg_textsearch + zhparser）
- `redis`（缓存、锁、PubSub）
- `minio`（报告对象存储）
- 观测栈：`alloy + prometheus + grafana + loki + tempo + langfuse`

对应文件：`compose.yaml`、`configs/docker/*`。

## 关键设计思想

### 异步优先

- API、数据库、缓存、任务执行均为异步路径。
- FastAPI 生命周期中集中初始化连接池与依赖（DB Session、Redis Pool、MCP Client、Agent）。

价值：提升并发吞吐，减少 I/O 阻塞。

### 解耦外部依赖

- CNInfo/Yahoo 通过 Adapter 层封装。
- Agent 与工具调用通过 MCP 协议抽象。

价值：替换数据源或工具协议时影响面更小。

### 数据与任务分离

- 在线查询由 API 承接。
- 抓取/分析通过 PgQueuer 异步执行。

价值：避免慢任务拖垮在线接口。

### 观测先行

- OTel 自动埋点（FastAPI/HTTPX/SQLAlchemy/Redis/LangChain）。
- Alloy 统一汇聚，输出到 Tempo/Loki/Prometheus，并可转发到 Langfuse。

价值：可定位 Agent 链路、接口时延、任务故障。

## 技术选型与优缺点

### FastAPI + SQLAlchemy Async

优点：

- 异步生态成熟，API 定义与校验效率高。
- OpenAPI 自动生成，适合再对接 MCP。

缺点：

- 异步调用链调试复杂度高于同步。
- 对数据库连接池、会话边界管理要求更高。

### PostgreSQL + pgvector + pg_textsearch

优点：

- 结构化数据与向量检索统一在一库。
- BM25 + 向量 + RRF 混合检索实现简单、工程成本低。

缺点：

- 报告规模继续增长时，单库读写与索引维护压力会增加。
- 向量索引策略与分片策略仍需持续优化。

### PgQueuer + Redis

优点：

- PgQueuer 复用 PostgreSQL，部署成本低。
- Redis 同时支持缓存、分布式锁、SSE 缓冲和 PubSub。

缺点：

- 队列状态、重试策略、死信治理能力目前文档与平台化程度有限。
- Redis 使用场景较多，容量与过期策略需要精细化治理。

### LangGraph + MCP + RAG

优点：

- 图编排适合多节点决策流（路由、检索、重写、工具调用）。
- MCP 使工具能力可标准化暴露与复用。

缺点：

- 链路较长，调参与稳定性治理成本高。
- 高并发下 token 成本与时延控制更敏感。

### SvelteKit 前端

优点：

- 组件与状态开销低，首屏和交互较轻量。
- 对流式 SSE 聊天支持实现直观。

缺点：

- 复杂业务场景下全局状态治理需进一步规范化。
- 与后端契约演进需更强的自动化校验。

## 当前架构问题

- 缺少正式架构决策记录（ADR）与模块边界约束文档。
- 安全域（鉴权、鉴别、细粒度权限）未形成系统方案。
- 在线 API、离线任务、Agent 评测的容量规划指标未沉淀。

## 改进思路

- 建立 ADR 机制（每个核心技术决策独立文档）。
- 增加统一鉴权与租户/用户维度权限模型。
- 建立容量模型与 SLO：API P95、队列积压、Agent 成功率、检索召回质量。
- 为关键链路增加压测基线与回归门禁（CI）。
