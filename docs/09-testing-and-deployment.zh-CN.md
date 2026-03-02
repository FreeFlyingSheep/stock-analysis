# 测试 + 部署

[English](09-testing-and-deployment.md) | [中文](09-testing-and-deployment.zh-CN.md)

## 技术介绍

- 测试：`pytest`、`testcontainers`、`deepeval`
- 质量门禁：`ruff`、`mypy`
- 部署：Docker Compose（本地/集成）、Kubernetes + Kustomize（集群）

## 具体实现细节

### 测试与检查

- `scripts/check.sh`：
  - `ruff format --check`
  - `ruff check`
  - `mypy`
  - `pytest`
  - `pnpm --prefix ui run check`
- `tests/` 覆盖 adapters/services/models/routers/agent/jobs。

### LLM/Agent 离线评测

- `scripts/eval.py` 会按顺序执行：
  - `chatbot`
  - `llm`
  - `agent`
  - `mcp`
  - `rag`
- 数据集位于 `data/evals/*.json`。
- 指标来自 DeepEval（相关性、任务完成度、工具正确性等）。

### Agent 评估

- Agent 相关评估集包含：
  - `chatbot`：通用聊天回答相关性
  - `llm`：基础 LLM 节点回答相关性
  - `agent`：端到端任务完成与回答相关性
  - `mcp`：工具调用正确性与参数正确性
  - `rag`：检索增强回答的相关性与忠实度
- 当前评估指标（基于 `src/stock_analysis/evals/*.py`）：
  - `chatbot`：`AnswerRelevancyMetric`（threshold=0.7）
  - `llm`：`AnswerRelevancyMetric`（threshold=0.7）
  - `agent`：`AnswerRelevancyMetric` + `TaskCompletionMetric`（threshold=0.7）
  - `mcp`：`AnswerRelevancyMetric` + `TaskCompletionMetric`（0.7）+ `ToolCorrectnessMetric` + `ArgumentCorrectnessMetric`（0.5）
  - `rag`：`AnswerRelevancyMetric` + `FaithfulnessMetric`（threshold=0.7）
- 评估实现位于 `src/stock_analysis/evals/`，可结合 `scripts/eval.py` 统一回归。
- 建议将 Agent 评估结果作为发布前质量门禁的一部分（与单测、类型检查并行）。

### 部署方式

- Docker Compose：`compose.yaml` 管理 API/Web/Worker/MCP/DB/缓存/观测组件。
- Kubernetes：`configs/k8s/base` + `configs/k8s/overlays/dev`。
  - API、Web、Worker、Postgres、Migrate 组件已拆分。

### 数据库迁移与初始化

- `scripts/migrate.sh`：init DB + 导入报告 + 初始化 Langfuse。
- Alembic 迁移脚本位于 `src/stock_analysis/alembic/versions`。

## 当前可能存在的问题

- `scripts/check.sh` 默认执行全量测试与前端检查，耗时较长，缺少分层门禁（快速/完整）。
- 评测结果阈值与准入标准尚未在文档中固化。
- K8s 部署目前以 dev overlay 为主，生产化参数与策略没有完整说明。

## 后续改进思路

- 建立分层 CI：PR 快速校验 + 主干完整回归 + 定时评测。
- 将 DeepEval 阈值纳入发布准入门槛。
- 完善 K8s 部署，引入 Helm 管理，明确生产环境配置与资源规划。
- 增加发布后验证（smoke test + 关键链路回放）。
