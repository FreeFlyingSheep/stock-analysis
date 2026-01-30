# API 规范配置

[English](README.md) | [中文](README.zh-CN.md)

## 目的

- 定义各数据源的上游 API 适配
- 作为适配器解析与调用的唯一参考

## 目录结构

- 数据源目录：
  - `cninfo/`：CNInfo REST 端点
  - `yahoo/`：Yahoo Finance 响应结构
- 每个端点一个 YAML，文件名使用 `snake_case`（例如 `get_balance_sheets.yaml`）
- 每个 YAML 都有对应的真实响应样本，存放在 `data/api` 中，并使用端点 `id` 命名

## 命名规范

- 端点的唯一标识为 YAML 中的 `api.id`
- 样本数据文件名使用该 id

示例：

- 配置：`configs/api/cninfo/get_balance_sheets.yaml`
- 端点标识：`balance_sheets`
- 样本：`data/api/cninfo/balance_sheets.json`

## YAML 结构（CNInfo）

- `api`：端点标识与请求方式
  - `id`, `name`：稳定的端点标识与名称
  - `request`：`method`、`url` 与 `params`（类型、必填与固定值）
- `response`：返回结构定义
  - 静态字段（如 `path.value`、`code.value`）用于记录固定值
  - `data` 与子节点描述结构（`object`/`array`/`string`/`number`）及动态字段（如 `dynamic: true`、`label: <YYYY>`）
  - 用于解析与上游变更检测
- `params`（可选）：API 期望的包裹结构

## YAML 结构（Yahoo）

- Yahoo 规范仅描述响应结构，请求细节由 `yfinance` 适配器处理

## 新增或更新端点

1. 复制相近 YAML 作为模板
2. 设置 `api.id`、`api.name`、`request.method` 与 `request.url`（仅 CNInfo）
3. 为每个参数标注类型、必填与固定值
4. 按约定描述返回结构并保留固定值字段
5. 抓取真实响应并保存到 `data/api/<provider>/<id>.json`，确认结构匹配

## 相关文件

- CNInfo 适配器：`src/stock_analysis/adapters/cninfo.py`
- Yahoo 适配器：`src/stock_analysis/adapters/yahoo.py`
- 示例数据：`data/api/README.md`

## 备注

- 配置与样本需保持同步
- 优先使用结构化模式（如 `items` + `dynamic` 标签），避免重复枚举叶子节点
