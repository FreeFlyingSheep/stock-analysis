#!/bin/bash
# Initialize the database with fresh data
#
# WARNING: This script will DROP all existing data in the database!
#
# Usage:
#   ./scripts/init_db.sh
#
# Requirements:
#   - uv package manager installed
#   - Database server running and accessible
#   - Valid .env file with database credentials
#   - CSV file at data/stocks.csv
set -euo pipefail

python scripts/drop_db.py
python scripts/create_db.py

if [ -f data/data.sql ]; then
    psql -h ${DATABASE_HOST} -p ${DATABASE_PORT} -U ${DATABASE_USER} -d ${DATABASE_DB} -f data/data.sql
else
    alembic -c pyproject.toml upgrade head
    python scripts/import_csv.py
    pgq \
        --pg-host ${DATABASE_HOST} \
        --pg-port ${DATABASE_PORT} \
        --pg-user ${DATABASE_USER} \
        --pg-password ${DATABASE_PASSWORD} \
        --pg-database ${DATABASE_DB} \
        install
fi
