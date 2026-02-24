#!/bin/bash
# Dump the current state of the database to data/data.sql file
#
# Requirements:
#   - Valid .env file with data store credentials
set -euo pipefail

export PGPASSWORD="$DATABASE_PASSWORD"

pg_dump \
    -U "$DATABASE_USER" \
    -h "$DATABASE_HOST" \
    -p "$DATABASE_PORT" \
    -d "$DATABASE_DB" \
    -t "analysis" \
    -t "cninfo_api_responses" \
    -t "report_chunks" \
    -t "stocks" \
    -t "yahoo_finance_api_responses" \
    -f data/data.sql
