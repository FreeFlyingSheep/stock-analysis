# Reports Directory

[English](README.md) | [中文](README.zh-CN.md)

This directory contains annual report PDF files for A-share companies and their metadata. The PDFs included here are a limited sample set for testing and demo purposes.

## Files

- `reports.csv`: Metadata index for all report files
- `*.pdf`: Annual report PDF files from companies

## CSV Format

The `reports.csv` file contains the following columns:

| Column | Description | Example |
| ------ | ----------- | ------- |
| `year` | Report publication year | `2020` |
| `stock_code` | Stock code (6 digits) | `000002` |
| `type` | Report type | `annual_report` |
| `file_name` | Original PDF filename | `万科A：2020年年度报告.pdf` |
| `content_type` | MIME type for the file | `application/pdf` |

## Usage

Use the `import_reports.py` script to upload all reports to MinIO storage:

```bash
python scripts/import_reports.py
```

Files are stored in MinIO with the following path structure:

```text
reports/{year}/{type}/{stock_code}.pdf
```

Example: `reports/2020/annual_report/000002.pdf`
