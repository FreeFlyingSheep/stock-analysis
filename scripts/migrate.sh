#!/bin/bash
# Migrate the database to the latest schema and import fresh data
#
# WARNING: This script will DROP all existing data in the database!
#
# Usage:
#   ./scripts/migrate.sh
#
# Requirements:
#   - uv package manager installed
#   - Database server running and accessible
#   - Valid .env file with database credentials
#   - CSV file at data/stocks.csv
#   - MinIO server running and accessible
#   - Files to import located in data/reports/
set -euo pipefail

bash ./scripts/init_db.sh
python scripts/import_reports.py
