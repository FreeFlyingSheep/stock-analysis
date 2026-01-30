#!/bin/bash
# Run the frontend UI for the stock analysis application.
#
# Requirements:
#   - Valid .env file with data store credentials
set -euo pipefail

cd ui
pnpm run build
HOST=${FRONTEND_HOST:-localhost} PORT=${FRONTEND_PORT:-3000} node build
