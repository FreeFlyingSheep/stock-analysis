"""MCP server and tool definitions for stock analysis agent."""

from typing import TYPE_CHECKING

from fastmcp import FastMCP

from stock_analysis.routers.app import app

if TYPE_CHECKING:
    from fastmcp.server.openapi import FastMCPOpenAPI

mcp: FastMCPOpenAPI = FastMCP.from_fastapi(app=app)
