#!/bin/bash
# Run the frontend UI for the stock analysis application.
#
# Requirements:
#   - Valid .env file with data store credentials
set -euo pipefail

pnpm --prefix ui run dev
