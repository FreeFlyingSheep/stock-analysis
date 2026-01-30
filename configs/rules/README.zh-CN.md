# 规则目录

[English](README.md) | [中文](README.zh-CN.md)

该目录包含基础面评分引擎使用的规则定义。

所有规则使用 YAML 描述，作为一个 DSL，用于定义：

- 计算哪些指标
- 如何评分
- 如何筛选
- 如何合成总分

引擎执行规则，不硬编码逻辑。

## 目的

`rules/` 目录用于：

- 以声明式方式定义评分逻辑
- 无需修改代码即可迭代规则
- 作为评估标准的唯一真源

规则应当具备：

- 可机器读取
- 可复现
- 可解释
- 版本可控

## 内容结构

```text
rules/
├── scoring_rules_sample.yaml       # 简化示例规则集
└── README.md
```

### `scoring_rules_sample.yaml`

用于测试与参考的简化规则集：

- 引擎测试
- 规则示例
- 开发调试

## YAML 结构

每个规则集在 `ruleset` 下包含：

```yaml
ruleset:
  id: <rule_id>
  version: "x.y.z"
  name: "<human_readable_name>"
  total_score_scale: 100

  dimensions:
    - id: <dimension_id>
      name: "<dimension_name>"
      weight: <0-100>
      enabled: true|false

  metrics:
    - id: <metric_id>
      name: "<metric_name>"
      dimension: <dimension_id>
      metric: <metric_type>
      description: "<description>"
      params: { ... }
      max_score: <float>
      weight: <0-100>
      enabled: true|false

  filters:
    - id: <filter_id>
      name: "<filter_name>"
      metric: <metric_id>
      filter: <filter_type>
      description: "<description>"
      params: { ... }
      enabled: true|false
```

### 字段说明

- `dimension`：指标分组，权重影响总分
- `metric`：由原始数据计算
  - `metric` 指定计算类型（如 `roe_weighted_average`）
  - `params` 为计算参数
  - `max_score` 为最大分
  - `weight` 为维度内权重
- `filter`：筛除规则
  - `filter` 指定类型（如 `threshold`）
  - `params` 为阈值或条件

## 执行流程

1. 读取规则 YAML
2. 验证结构与引用
3. 从数据库拉取原始数据
4. 计算指标
5. 应用筛选
6. 计算指标得分
7. 按维度聚合
8. 计算总分
9. 写入分析表

## 设计原则

- 配置优先
- 依赖显式
- 无隐式假设
- 数据/逻辑/执行解耦

## 新增规则

1. 在本目录新增 `scoring_rules_<name>.yaml`
2. 填写 `ruleset` 的 `id`、`version`、`name`、`total_score_scale`
3. 添加 `dimensions`（名称与权重）
4. 添加 `metrics`（`id`、`name`、`dimension`、`metric`、`max_score`、`weight` 等）
5. 按需添加 `filters`
6. 在 `.env` 中更新 `RULE_FILE_PATH` 指向新规则文件

## 可用指标类型（示例）

- `roe_weighted_average`：ROE 多年加权
- `gross_margin`：毛利率
- `net_margin`：净利率
- `profit_growth`：利润同比
- `ocf_ratio`：经营现金流/净利润
- `debt_ratio`：资产负债率

## 版本管理建议

- 更新规则时递增 version
- 记录主要变更
- 用历史数据验证
- 若需对比，可并存多版本规则集

## 备注

- 规则仅定义评分逻辑，不负责数据抓取
- 不提供任何投资建议
