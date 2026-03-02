# Testing + Deployment

[English](09-testing-and-deployment.md) | [中文](09-testing-and-deployment.zh-CN.md)

## Technology Overview

- Testing: `pytest`, `testcontainers`, `deepeval`
- Quality gates: `ruff`, `mypy`
- Deployment: Docker Compose (local/integration), Kubernetes + Kustomize (cluster)

## Implementation Details

### Tests and Checks

- `scripts/check.sh`:
  - `ruff format --check`
  - `ruff check`
  - `mypy`
  - `pytest`
  - `pnpm --prefix ui run check`
- `tests/` covers adapters/services/models/routers/agent/jobs.

### Offline LLM/Agent Evaluation

- `scripts/eval.py` runs suites in order:
  - `chatbot`
  - `llm`
  - `agent`
  - `mcp`
  - `rag`
- Datasets are under `data/evals/*.json`.
- Metrics come from DeepEval (relevancy, task completion, tool correctness, etc.).

### Agent Evaluation

- Agent-focused suites include:
  - `chatbot`: general chatbot answer relevancy
  - `llm`: base LLM-node answer relevancy
  - `agent`: end-to-end task completion and answer relevancy
  - `mcp`: tool correctness and argument correctness
  - `rag`: retrieval-augmented answer relevancy and faithfulness
- Current metrics (from `src/stock_analysis/evals/*.py`):
  - `chatbot`: `AnswerRelevancyMetric` (threshold=0.7)
  - `llm`: `AnswerRelevancyMetric` (threshold=0.7)
  - `agent`: `AnswerRelevancyMetric` + `TaskCompletionMetric` (threshold=0.7)
  - `mcp`: `AnswerRelevancyMetric` + `TaskCompletionMetric` (0.7) + `ToolCorrectnessMetric` + `ArgumentCorrectnessMetric` (0.5)
  - `rag`: `AnswerRelevancyMetric` + `FaithfulnessMetric` (threshold=0.7)
- Implementations are under `src/stock_analysis/evals/`, and can be run together via `scripts/eval.py`.
- Agent evaluation should be treated as a release quality gate alongside unit tests and type checks.

### Deployment Approaches

- Docker Compose: `compose.yaml` manages API/Web/Worker/MCP/DB/cache/observability components.
- Kubernetes: `configs/k8s/base` + `configs/k8s/overlays/dev`.
  - API, Web, Worker, Postgres, and Migrate components are split.

### Database Migration and Initialization

- `scripts/migrate.sh`: initialize DB + import reports + initialize Langfuse.
- Alembic migrations are under `src/stock_analysis/alembic/versions`.

## Current Potential Issues

- `scripts/check.sh` runs full backend/frontend checks by default; it is time-consuming and lacks tiered gates (fast/full).
- Eval thresholds and release entry criteria are not documented.
- K8s deployment is currently centered on dev overlay; production-grade parameters and policies are not fully documented.

## Improvement Directions

- Build tiered CI: fast PR checks + full main-branch regression + scheduled evals.
- Add DeepEval thresholds into release gates.
- Improve K8s deployment with Helm management, explicit production config, and resource planning.
- Add post-release verification (smoke tests + critical-path replay).
