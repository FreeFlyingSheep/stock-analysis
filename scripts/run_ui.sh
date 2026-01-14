#!/bin/bash
# Run the frontend UI for the stock analysis application.
#
# Requirements:
#   - Backend services are running
set -euo pipefail

source .env

pnpm --prefix ui run build
pnpm --prefix ui run preview
