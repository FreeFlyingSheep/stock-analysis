#!/bin/bash
# Dump the current state of the database to data/data.sql file
#
# Requirements:
#   - Valid .env file with data store credentials
set -euo pipefail

pg_dump \
    -U "$DATABASE_USER" \
    -h "$DATABASE_HOST" \
    -p "$DATABASE_PORT" \
    -d "$DATABASE_DB" \
    -f data/data.sql
