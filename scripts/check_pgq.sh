#!/bin/bash
# Check PgQueuer status
#
# Requirements:
#   - uv package manager installed
#   - Database server running and accessible
#   - Valid .env file with database credentials
set -euo pipefail

pgq \
    --pg-host ${DATABASE_HOST} \
    --pg-port ${DATABASE_PORT} \
    --pg-user ${DATABASE_USER} \
    --pg-password ${DATABASE_PASSWORD} \
    --pg-database ${DATABASE_DB} \
    verify --expect present
