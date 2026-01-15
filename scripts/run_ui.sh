#!/bin/bash
# Run the frontend UI for the stock analysis application.
#
# Requirements:
#   - Backend services are running
set -euo pipefail

cd ui
pnpm run build
HOST=${UI_HOST:-localhost} PORT=${UI_PORT:-3000} node build
