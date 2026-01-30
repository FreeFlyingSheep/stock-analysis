# API 样本数据

[English](README.md) | [中文](README.zh-CN.md)

## 目的

保存 CNInfo 与 Yahoo Finance 的真实 API 响应用于：

- 离线开发与测试
- 解析器验证与结构校验
- 合约一致性检查
- 避免频繁请求上游

## 目录结构

按数据源划分：

- `cninfo/`：CNInfo 响应样本
- `yahoo/`：Yahoo Finance 响应样本

每个 JSON 文件：

- 使用对应 YAML 中的 `api.id` 命名
- 保存完整原始响应
- 结构保持完整用于校验

## 文件命名

配置文件使用蛇形命名法，端点 `id` 由 `api.id` 指定：

- 配置：`configs/api/cninfo/get_balance_sheets.yaml`
- 端点 `id`：`balance_sheets`
- 样本：`data/api/cninfo/balance_sheets.json`

## 响应结构

每个响应应符合 `configs/api` 中定义的结构，例如：

```json
{
  "path": "/financialData/getBalanceSheets",
  "code": 200,
  "data": {
    "total": 123,
    "count": 123,
    "resultMsg": "success",
    "result": []
  }
}
```

## 更新样本数据

1. 从真实端点拉取最新数据
2. 保存完整 JSON 到 `data/api/<provider>/<id>.json`
3. 必要时清理敏感信息
4. 对照配置结构验证
5. 配置与样本同步更新

## 现有端点

### CNInfo

- `balance_sheets.json`
- `cash_flow_statement.json`
- `income_statement.json`
- `company_introduction.json`
- `company_executives.json`
- `main_indicators.json`
- `stock_structure.json`
- `top_ten_stockholders.json`
- `top_ten_circulating_stockholders.json`
- `stockholder_num.json`
- `equity_pledge.json`
- `company_his_dividend.json`
- `lift_ban.json`
- `executives_inc_dec_detail.json`
- `stockholeder_inc_dec_detail.json`
- `margin_trading.json`
- `ints_detail.json`
- `fund_holdings.json`

### Yahoo Finance

- `history.json`

## 测试示例

```python
import json

with open('data/api/cninfo/balance_sheets.json') as f:
    sample_response = json.load(f)

result = parser.parse_balance_sheets(sample_response)
assert result.total == sample_response['data']['total']
```

## 最佳实践

- 避免手工修改，尽量重新抓取
- 结构尽量完整，必要时保留代表性样本
- 记录结构变更，方便排查
