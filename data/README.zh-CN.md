# 数据目录说明

[English](README.md) | [中文](README.zh-CN.md)

该目录用于存放项目初始化、测试与 RAG 演示所需的数据文件，包括股票基础数据、可选 SQL 种子数据、API 响应样本以及少量年报 PDF 示例。

## 目录用途

`data/` 目录主要用于：

- 初始化数据库时导入股票基础信息
- 在本地初始化阶段导入可选 SQL 数据
- 为解析器/测试提供 API 原始响应样本
- 为 RAG 功能提供少量年报 PDF 演示数据

## 目录结构

- `stocks.csv`：A 股股票基础信息与行业分类数据（CSV 种子文件）
- `data.sql`：可选 SQL 种子脚本（`scripts/init_db.sh` 存在时会自动导入）
- `api/`：CNInfo 与 Yahoo Finance 的 API 响应样本
- `reports/`：年报 PDF 示例及 `reports.csv` 元数据
- `README.md` / `README.zh-CN.md`：本目录说明文档

## 使用方式

### 数据库初始化

`scripts/init_db.sh` 会使用本目录的数据完成本地初始化：

1. 重建数据库与表结构
2. 从 `data/stocks.csv` 导入股票基础数据
3. 安装 PgQueuer 队列
4. 如果存在 `data/data.sql`，则自动执行导入

### 完整迁移/初始化流程

`scripts/migrate.sh` 会执行完整初始化流程，并继续导入报告文件：

```bash
./scripts/migrate.sh
```

该脚本会清空现有数据库数据，请谨慎使用。

### 年报导入（RAG）

`data/reports/` 中的示例 PDF 可用于对象存储上传与向量化/检索流程（详见 `data/reports/README.zh-CN.md`）。

常用命令：

```bash
uv run scripts/import_reports.py
uv run scripts/ingest_reports.py
```

## 文件说明

### `stocks.csv`

包含 A 股上市公司主数据与行业分类字段（中文表头），例如：

- 上市公司代码、简称
- 门类/次类/大类代码与名称

该文件是 `scripts/import_csv.py` 在数据库初始化时使用的主要 CSV 种子数据。

### `data.sql`

可选的大型 SQL 数据文件，用于补充本地测试数据或快速恢复固定数据集。

- `scripts/init_db.sh` 检测到文件存在时会自动导入
- 适合本地开发/测试快速恢复数据
- 文件体积可能较大，不需要时可不保留在仓库中

## 子目录

### `api/`

保存上游接口的 JSON 响应样本，供适配器开发、解析校验与测试使用。

- 文档：`data/api/README.zh-CN.md`
- 包含 `cninfo/`、`yahoo/` 等数据源子目录

### `reports/`

保存少量年报 PDF 示例与 `reports.csv` 元数据。

- 文档：`data/reports/README.zh-CN.md`
- 用于测试/演示，不是完整年报库
