#!/bin/bash
# Check code quality, type correctness, and run tests
#
# This script performs comprehensive code quality checks including:
# - Code formatting verification (ruff format)
# - Linting and style checks (ruff check)
# - Static type checking (mypy)
# - Unit and integration tests (pytest)
# - Frontend code checks (npm run check in the ui directory)
#
# Requirements:
#   - uv package manager installed
#   - All dependencies installed via uv
set -euo pipefail

uv run ruff format --check .
uv run ruff check .
uv run mypy .
uv run pytest
pnpm --prefix ui run check
