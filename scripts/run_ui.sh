#!/bin/bash
# Run the frontend UI for the stock analysis application.
#
# Requirements:
#   - Backend services are running
set -euo pipefail

source .env

npm --prefix ui run build
npm --prefix ui run preview
