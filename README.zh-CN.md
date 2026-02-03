# 股票分析（Stock Analysis）

[English](README.md) | [中文](README.zh-CN.md)

股票分析（Stock Analysis）是一个面向 A 股的基础面评分代理，支持从巨潮资讯与雅虎财经拉取数据，使用声明式规则进行评分和筛选，并通过 FastAPI 后端与 SvelteKit UI 提供查询与可视化。

## 免责声明

**本工具仅供参考与学习，所有数据与分析结果不构成任何投资建议。**

本人**不提供**任何金融、投资或交易建议。用户应自行研究并在做出任何投资决定前咨询专业财务顾问。

**投资有风险，可能损失本金。** 历史表现不代表未来结果。请自行承担使用本工具的风险。

爬虫/下载器会自动从巨潮资讯和雅虎财经等第三方网站抓取数据；分析器会根据抓取的数据和用户定义的规则计算评分。有限的更新频率旨在减少对目标网站的流量压力并避免被封禁，仅供测试用途。

`data` 中仅预置 10 份年报，用于测试 RAG（检索增强生成）功能。出于伦理与安全考虑，项目不提供年报爬虫，因为可能会对目标网站造成巨大流量压力。

本项目在开发过程中使用了 AI 工具辅助：

- GitHub Copilot 用于代码与文档生成/建议
- ChatGPT 用于方案讨论与问题排查

## 技术与工具

### 后端与 API

- **Python 3.14** 后端开发
- **FastAPI** 异步 REST API 与自动文档
- **Uvicorn** ASGI 运行时
- **FastMCP** MCP 服务实现
- **Pydantic** 数据校验与配置管理
- **SQLAlchemy** 异步 ORM

### 数据与存储

- **PostgreSQL 18** 关系型存储
- **pgvector** 向量检索
- **Alembic** 数据库迁移
- **MinIO** S3 兼容对象存储
- **PgQueuer** 异步任务队列
- **Redis** 缓存与快速数据检索

### 前端（AI 辅助生成）

- **Svelte/SvelteKit** 交互式 UI
- **TypeScript** 类型安全
- **Vite** 构建与开发服务
- **pnpm** 或 **npm** 包管理

### DevOps 与基础设施

- **Docker Compose** 本地多容器编排
- **Kubernetes** + Kustomize 生产部署
- **Nginx** 反向代理
- **Minikube** 本地 Kubernetes 开发/测试
- **GitHub Workflows** CI/CD 流水线

### 开发与质量

- **uv** Python 依赖管理
- **pytest** 测试
- **testcontainers** 依赖容器测试
- **ruff** 代码格式与静态检查
- **mypy** 类型检查
- **Git** 版本控制

### AI & LLM

- **LangChain + LangGraph**（OpenAI 兼容接口）用于聊天分析

### 配置与数据

- **YAML** API 规范与评分规则
- **CSV** 批量导入/导出

## 功能特性

### 数据与分析

- **股票数据管理**：存储与查询 A 股公司信息、板块与行业
- **多数据源抓取**：从 CNInfo 与 Yahoo Finance 拉取数据，并带限流与重试
- **规则化评分**：基于 YAML 规则计算指标与总分
- **股票筛选**：按评分规则过滤
- **CSV 导入/导出**：批量导入与导出
- **任务队列**：PgQueuer 处理抓取与分析任务

### API 与服务

- **REST API**：FastAPI 异步 API，含 Swagger/ReDoc 文档
- **异步数据库**：SQLAlchemy + PostgreSQL
- **MCP 服务**：FastMCP 接入 Model Context Protocol
- **聊天代理**：LLM 驱动的解释与问答
- **缓存响应**：Redis 缓存频繁访问的数据

### 前端与界面

- **交互式仪表盘**：股票浏览与可视化
- **高级筛选**：按板块/行业/分页筛选
- **国际化支持**：提供中英文切换
- **浮动聊天窗口**：随时调用聊天助手

### 基础设施与部署

- **Docker Compose & Kubernetes**：开发与生产部署
- **数据库迁移**：Alembic 版本管理
- **向量存储**：pgvector 支持语义检索与 RAG

### 代码质量与体验

- **类型标注**：全量类型提示
- **文档规范**：Google 风格 docstring
- **质量标准**：ruff + mypy
- **自动化测试**：pytest + testcontainers 隔离测试

## 功能规划

已计划的功能：

- 增加 RAG（检索增强生成）功能
- 增加使用 Prometheus 和 Grafana 的可观测性和监控

正在考虑的功能：

- 在 PgQueuer 中去除重复任务
- 完善前端 UI/UX 设计

## 安装与运行

**警告：以下所有安装方法都会删除并重建数据库，擦除任何现有数据。**

如果要保留现有数据，请先导出数据库（`./scripts/dump_db.sh`），或通过手动运行 Alembic 迁移来确保数据库架构最新。

对于大多数用户，[Docker Compose](#docker-compose)是**推荐**的，因为它简单易用。
[本地开发](#本地开发)仅用于开发和测试。
[Kubernetes](#kubernetes)用于生产部署场景，但由于硬件限制，仅支持和测试部分模块。

### 本地开发

1. 克隆仓库：

    ```bash
    git clone https://github.com/FreeFlyingSheep/stock-analysis
    cd stock-analysis
    ```

2. 使用 [uv](https://docs.astral.sh/uv/) 安装依赖：

    ```bash
    uv sync --all-extras
    source .venv/bin/activate
    ```

3. 配置环境变量：

    ```bash
    cp .env.example .env
    # 使用您的数据库凭证和设置编辑 .env
    export $(grep -v '^#' .env | xargs)
    ```

4. 初始化数据库（先安装 [PostgreSQL 18+](https://www.postgresql.org/) 和 [pgvector](https://github.com/pgvector/pgvector)）：

    ```bash
    ./scripts/init_db.sh
    ```

    此脚本将：
    - 删除任何现有数据库
    - 创建新的数据库
    - 启用 pgvector 扩展
    - 运行 Alembic 迁移以创建表
    - 从 `data/stocks.csv` 导入初始股票数据
    - 初始化 PgQueuer 任务队列

5. 启动 MinIO 数据存储：

    在单独的终端中运行 MinIO 以进行对象存储：

    ```bash
    source .venv/bin/activate
    export $(grep -v '^#' .env | xargs)
    ./scripts/run_minio.sh
    ```

6. 运行任务队列：

    在单独的终端中运行 PgQueuer 以处理爬虫和分析任务：

    ```bash
    source .venv/bin/activate
    export $(grep -v '^#' .env | xargs)
    ./scripts/run_pgq.sh
    ```

    这将启动任务处理器，其中：
    - 从巨潮资讯和雅虎财经获取股票数据
    - 使用配置的规则计算评分和指标
    - 将结果存储在数据库中

7. 启动 MCP 服务器：

    在另一个终端中运行 FastMCP 服务器：

    ```bash
    source .venv/bin/activate
    export $(grep -v '^#' .env | xargs)
    ./scripts/run_mcp.sh
    ```

8. 启动 API 服务器：

    ```bash
    uv run app
    ```

    默认情况下，API 将在 `http://127.0.0.1:8000` 可用。
    API 文档由 FastAPI 自动生成，可在以下位置访问：
    - Swagger UI：`http://127.0.0.1:8000/docs`
    - ReDoc：`http://127.0.0.1:8000/redoc`

9. 启动前端 UI：

    在另一个终端中运行 SvelteKit 前端：

    ```bash
    export $(grep -v '^#' .env | xargs)
    pnpm --prefix ui run dev
    # 或 npm --prefix ui run dev
    ```

    UI 将在 `http://127.0.0.1:5173` 可用。

### Docker Compose

配置在 `.env` 中设置，并在 `compose.yaml` 中覆盖。如果需要更改，请在启动服务前编辑这些文件。

1. 确保已安装 Docker 和 Docker Compose。

2. 克隆仓库：

    ```bash
    git clone https://github.com/FreeFlyingSheep/stock-analysis
    cd stock-analysis
    ```

3. 配置环境变量：

    ```bash
    cp .env.example .env
    # 使用您的数据库凭证和设置编辑 .env
    ```

4. 运行 Docker Compose 设置：

    ```bash
    docker compose up -d
    ```

    这将启动所有必要的服务，包括 PostgreSQL、MinIO、MCP、API 服务器、worker 和前端 UI（通过 Nginx）。
    如果更新了代码或配置，请使用以下命令重建镜像：

    ```bash
    docker compose up -d --build --force-recreate
    ```

    您可以在 `http://127.0.0.1:8080` 访问服务。

5. 关闭后删除所有本地镜像：

    ```bash
    docker compose down --rmi local
    ```

    如果还想删除数据卷，请使用：

    ```bash
    docker compose down -v --rmi local
    ```

如果已导出数据库，可以通过运行 `docker exec -i stock-analysis-postgres-1 psql -U postgres -d stock_analysis < data/data.sql` 来恢复它，忽略关于现有对象的错误消息。

### Kubernetes

以 Minikube 为例进行本地 Kubernetes 部署（由于硬件限制，不支持 MCP）。
此设置中不使用 `.env` 文件；而是直接在 Kustomize 文件中配置环境变量。

1. 确保 Minikube 正在运行且 `kubectl` 已配置。

   如果尚未启用 Ingress 插件，请启用：

   ```bash
   minikube addons enable ingress
   ```

2. 克隆仓库：

    ```bash
    git clone https://github.com/FreeFlyingSheep/stock-analysis
    cd stock-analysis
    ```

3. 为 Minikube 构建 Docker 镜像：

    ```bash
    ./scripts/build.sh
    ```

4. 使用 Kustomize 设置 Kubernetes 资源：

    ```bash
    kubectl apply -k configs/k8s/overlays/dev
    ```

5. 获取服务 IP 和端口：

    ```bash
    minikube ip
    kubectl get svc -n ingress-nginx ingress-nginx-controller
    ```

    在 `http://<MINIKUBE_IP>:<NODE_PORT>` 访问应用。

    如果在 WSL2 中使用 Minikube（不是通过 Docker Desktop），可能需要设置端口转发：

    ```bash
    kubectl -n ingress-nginx port-forward svc/ingress-nginx-controller 8080:80
    ```

    然后在 `http://localhost:8080` 访问应用。

6. 完成后删除 Kubernetes 资源：

    ```bash
    kubectl delete -k configs/k8s/overlays/dev
    ```

## 配置文件与数据

### API 规范

详见 [configs/api/README.zh-CN.md](configs/api/README.zh-CN.md) 了解：

- 添加新的 API 端点
- YAML 结构和约定
- 维护端点规范

### 评分规则

详见 [configs/rules/README.zh-CN.md](configs/rules/README.zh-CN.md) 了解：

- 编写评分规则
- 指标定义
- 过滤规范
- 规则版本管理

### 提示模板

详见 [configs/prompts/README.zh-CN.md](configs/prompts/README.zh-CN.md) 了解：

- 为聊天机器人编写提示模板

### 数据样例

详见 [data/samples/README.zh-CN.md](data/samples/README.zh-CN.md) 了解：

- 样例数据格式

### 报告

详见 [data/reports/README.zh-CN.md](data/reports/README.zh-CN.md) 了解：

- 元数据格式

## 前端 UI

详见 [ui/README.zh-CN.md](ui/README.zh-CN.md) 了解：

- 前端开发

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。
