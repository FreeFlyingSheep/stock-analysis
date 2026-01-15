#!/bin/bash
# Check PgQueuer status
#
# Usage:
#   ./scripts/check_pgq.sh
#
# Exit codes:
#   0: PgQueuer is present and healthy
#   others: PgQueuer is not present or unhealthy
#
# Requirements:
#   - uv package manager installed
#   - Database server running and accessible
#   - Valid .env file with database credentials
set -euo pipefail

uv run pgq \
    --pg-host ${DATABASE_HOST} \
    --pg-port ${DATABASE_PORT} \
    --pg-user ${DATABASE_USER} \
    --pg-password ${DATABASE_PASSWORD} \
    --pg-database ${DATABASE_DB} \
    verify --expect present
