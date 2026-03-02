# 技术文档

[English](README.md) | [中文](README.zh-CN.md)

本文档集用于系统整理项目的技术方案与实现细节。
本文档由 GPT-5.3-Codex 辅助生成。

## 项目简介

- 基于 FastAPI、SQLAlchemy Async 和 PgQueuer 构建 A 股分析平台，抓取与分析任务异步化。
- 实现 YAML 规则引擎与 CNInfo/Yahoo 数据管道，具备重试、限流和缓存能力。
- 落地 LangGraph + RAG + SSE 聊天链路，并提供 Docker/K8s 部署与 OTel/Prometheus/Grafana 可观测性。

## 目录

1. [01 架构设计](./01-architecture.zh-CN.md)
2. [02 数据存储（Alembic + PostgreSQL + MinIO）](./02-data-storage.zh-CN.md)
3. [03 后端（FastAPI）](./03-backend-fastapi.zh-CN.md)
4. [04 中间件（PgQueuer + Redis）](./04-middleware-pgqueuer-redis.zh-CN.md)
5. [05 前端（SvelteKit）](./05-frontend-sveltekit.zh-CN.md)
6. [06 Agent 设计 + MCP](./06-agent-and-mcp.zh-CN.md)
7. [07 RAG + pgvector + 混合检索](./07-rag-pgvector-hybrid.zh-CN.md)
8. [08 监测平台（含 Langfuse）](./08-observability-and-langfuse.zh-CN.md)
9. [09 测试 + 部署](./09-testing-and-deployment.zh-CN.md)

## 架构图

Docker Compose 本地开发架构图（由 `./scripts/create_compose_graph.sh` 生成）：

![架构图](./images/compose.svg)
