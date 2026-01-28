#!/bin/bash
# Run the MinIO data store for the stock analysis application.
#
# Requirements:
#   - Valid .env file with data store credentials
set -euo pipefail

minio \
    server ${MINIO_DATA_DIR} \
    --address "${MINIO_HOST}:${MINIO_PORT}" \
    --console-address "${MINIO_HOST}:${MINIO_CONSOLE_PORT}"
