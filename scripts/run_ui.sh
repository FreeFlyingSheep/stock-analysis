#!/bin/bash
# Run the frontend UI for the stock analysis application.
#
# Requirements:
#   - Backend services are running
set -euo pipefail

cd ui
pnpm run build
HOST=${FRONTEND_HOST:-localhost} PORT=${FRONTEND_PORT:-3000} node build
