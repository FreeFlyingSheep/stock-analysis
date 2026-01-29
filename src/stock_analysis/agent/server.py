"""MCP server and tool definitions for stock analysis agent."""

from typing import TYPE_CHECKING

from fastapi import Request  # noqa: TC002
from fastapi.responses import JSONResponse
from fastmcp import FastMCP
from fastmcp.server.openapi import MCPType, RouteMap

from stock_analysis.routers.app import app

if TYPE_CHECKING:
    from fastmcp.server.openapi import FastMCPOpenAPI


mcp: FastMCPOpenAPI = FastMCP.from_fastapi(
    app=app,
    route_maps=[
        RouteMap(tags={"chat"}, mcp_type=MCPType.EXCLUDE),
    ],
)


@mcp.custom_route("/health", methods=["GET"])
async def health_check(_request: Request) -> JSONResponse:
    """Health check endpoint for MCP server."""
    return JSONResponse({"status": "healthy", "service": "mcp-server"})
