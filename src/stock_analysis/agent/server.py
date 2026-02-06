"""MCP server and tool definitions for stock analysis agent."""

from typing import TYPE_CHECKING

import httpx
from fastapi import Request  # noqa: TC002
from fastapi.responses import JSONResponse
from fastmcp import FastMCP
from fastmcp.server.openapi import MCPType, RouteMap
from fastmcp.server.openapi.server import FastMCPOpenAPI
from httpx import AsyncClient

from stock_analysis.settings import get_settings

if TYPE_CHECKING:
    from typing import Any

    from fastmcp.server.openapi import FastMCPOpenAPI

    from stock_analysis.settings import Settings


settings: Settings = get_settings()
client = AsyncClient(base_url=settings.api_url)
openapi_spec: dict[str, Any] = httpx.get(f"{settings.api_url}/openapi.json").json()
mcp: FastMCPOpenAPI = FastMCP.from_openapi(
    openapi_spec=openapi_spec,
    client=client,
    name="Stock Analysis MCP Server",
    route_maps=[
        RouteMap(tags={"chat"}, mcp_type=MCPType.EXCLUDE),
        RouteMap(tags={"reports"}, mcp_type=MCPType.EXCLUDE),
    ],
)


@mcp.custom_route("/health", methods=["GET"])
async def health_check(_request: Request) -> JSONResponse:
    """Health check endpoint for MCP server.

    Args:
        _request: FastAPI request object (unused).

    Returns:
        JSON response with service health status.
    """
    return JSONResponse({"status": "healthy", "service": "mcp-server"})


@mcp.tool(
    name="get_financial_report",
    description="Fetch financial report for a given stock code.",
)
async def get_financial_report(stock_code: str) -> str:
    """Tool to fetch financial report for a given stock code.

    Args:
        stock_code: Stock code to retrieve the report for.

    Returns:
        Financial report content for the specified stock code.

    Raises:
        NotImplementedError: Always raised until implemented.
    """
    raise NotImplementedError
