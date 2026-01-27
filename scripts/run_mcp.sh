#!/bin/bash
# Run the MCP server for the stock analysis application.
#
# Requirements:
#   - Valid .env file with database credentials
set -euo pipefail

fastmcp \
    run src/stock_analysis/agent/server.py:mcp \
    --transport http \
    --host ${MCP_HOST} \
    --port ${MCP_PORT}
