#!/bin/bash
# Initialize the database with fresh data
#
# WARNING: This script will DROP all existing data in the database!
#
# This script performs the following operations in sequence:
# 1. Drops the existing database (if it exists)
# 2. Creates a fresh database
# 3. Runs Alembic migrations to create tables
# 4. Imports initial stock data from CSV file
#
# Usage:
#   ./scripts/init.sh
#
# Exit codes:
#   0: Database initialized successfully
#   1: Initialization failed at any step
#
# Requirements:
#   - uv package manager installed
#   - Database server running and accessible
#   - Valid .env file with database credentials
#   - CSV file at data/stocks.csv
set -euo pipefail

uv run scripts/drop_db.py
uv run scripts/create_db.py
uv run alembic upgrade head
uv run scripts/import_csv.py
