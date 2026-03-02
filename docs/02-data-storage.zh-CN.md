# 数据存储（Alembic + PostgreSQL + MinIO）

[English](02-data-storage.md) | [中文](02-data-storage.zh-CN.md)

## 技术介绍

- **PostgreSQL 18**：主关系型数据库，承载股票、分析、聊天、报告分块等核心数据。
- **Alembic**：数据库 schema 迁移与版本管理。
- **pgvector**：报告分块向量字段，支持语义检索。
- **pg_textsearch + zhparser**：中文 BM25 索引能力。
- **MinIO**：S3 兼容对象存储，保存原始报告与处理产物。

## 具体实现细节

### 初始化与迁移

- `scripts/init_db.sh` 执行流程：
  - 删除/创建数据库
  - 执行 Alembic `upgrade head`
  - 导入基础股票 CSV
  - 安装 PgQueuer 元数据
- `scripts/create_db.py` 会创建扩展：
  - `vector`
  - `pg_textsearch`
  - `zhparser`
  - 并创建 `chinese` 文本搜索配置。

### 报告向量与全文检索表

- `report_chunks` 表定义见 `models/report.py`。
- `embedding` 字段类型为 `VECTOR(dim=<配置维度>)`。
- BM25 索引 `idx_report_chunks_bm25` 使用 `postgresql_using="bm25"`。

### MinIO 分桶与数据流

- 原始报告桶：`<prefix>raw`
- 处理结果桶：`<prefix>processed`
- `scripts/import_reports.py`：按 `data/reports/reports.csv` 上传 PDF 到 `reports/<year>/<type>/<stock_code>.pdf`。
- `scripts/ingest_reports.py` + `agent/ingest.py`：
  - 拉取 MinIO 对象
  - PDF 抽取与分块
  - 生成 embedding
  - upsert 到 `report_chunks`

### Langfuse 依赖存储

- `scripts/init_langfuse.py` 会创建 Langfuse 所需 PostgreSQL 数据库与 MinIO bucket。

## 当前可能存在的问题

- `init_db.sh` / `migrate.sh` 默认包含 destructive 行为（删库重建），对误操作不友好。
- 报告分块表随数据增长后，索引膨胀与查询退化风险上升。
- MinIO 生命周期策略、冷热分层、数据归档策略尚未文档化。
- 数据库备份/恢复演练流程未文档化。

## 后续改进思路

- 区分“开发重置脚本”和“生产增量迁移脚本”，避免误删。
- 为 `report_chunks` 增加分区/归档策略（按年份、股票、文档版本）。
- 明确备份策略（RPO/RTO）并固化演练脚本。
- 给 MinIO 增加生命周期规则与清理任务（历史版本、过期处理产物）。
- 给 PostgreSQL 和 MinIO 启用高可用部署（主从、分布式 MinIO）。
