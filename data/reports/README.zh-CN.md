# 年报目录

[English](README.md) | [中文](README.zh-CN.md)

该目录包含 A 股公司的年报 PDF 及其元数据。当前仅提供有限样本用于测试与演示。

## 文件

- `reports.csv`：年报元数据索引
- `*.pdf`：公司年报 PDF

## CSV 格式

`reports.csv` 包含如下字段：

| 字段 | 描述 | 示例 |
| --- | --- | --- |
| `year` | 年报年份 | `2020` |
| `stock_code` | 股票代码（6 位） | `000002` |
| `type` | 报告类型 | `annual_report` |
| `file_name` | 原始文件名 | `万科A：2020年年度报告.pdf` |
| `content_type` | MIME 类型 | `application/pdf` |

## 使用方法

使用 `import_reports.py` 上传到 MinIO：

```bash
python scripts/import_reports.py
```

存储路径结构：

```text
reports/{year}/{type}/{stock_code}.pdf
```

示例：`reports/2020/annual_report/000002.pdf`
