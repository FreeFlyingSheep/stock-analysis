# 后端（FastAPI）

[English](03-backend-fastapi.md) | [中文](03-backend-fastapi.zh-CN.md)

## 技术介绍

- FastAPI 作为 REST API 框架。
- Uvicorn 作为 ASGI 运行时（`src/stock_analysis/main.py`）。
- Pydantic + pydantic-settings 统一输入校验与配置管理。
- SQLAlchemy Async 提供数据库访问能力。

## 具体实现细节

### 应用启动与依赖装配

`routers/app.py` 的 `lifespan` 负责初始化：

- OTel telemetry 与 metrics server
- Async SQLAlchemy engine/session
- PgQueuer 连接池
- Redis 连接池
- MCP 客户端
- ChatAgent（含 Postgres checkpointer）

### 路由划分

当前按领域拆分路由：

- `routers/stock.py`
- `routers/analysis.py`
- `routers/chat.py`
- `routers/report.py`

路由层通过依赖注入拿到 service（数据库、缓存、agent、mcp）。

### 聊天流式接口

`/chat/start` + `/chat/stream` 组合实现 SSE：

- 启动阶段写入 Redis 运行状态
- 后台任务调用 Agent，按 token 推送
- Redis list 做缓冲，PubSub 做实时分发
- 错误与完成态以事件形式回传

### 配置体系

`settings.py` 定义数据库、MinIO、Redis、MCP、LLM、监控等全量配置，并通过 `cached_property` 生成派生地址。

## 当前可能存在的问题

- 目前接口鉴权/授权能力未在后端主链路中体现。
- 生命周期装配项较多，启动逻辑耦合度偏高。
- 聊天链路依赖 Redis 状态机，异常恢复路径复杂。

## 后续改进思路

- 引入统一认证机制（例如 API Key / OAuth2 / JWT），并增加权限分级。
- 将 `lifespan` 初始化拆分为更细粒度模块，提升可维护性与可测试性。
- 对聊天流程增加幂等键与更细化的错误码，便于前端恢复与重试。
- 增加关键接口的负载与稳定性基准测试。
