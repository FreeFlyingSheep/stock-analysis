"""MCP server and tool definitions for stock analysis agent."""

from typing import TYPE_CHECKING

import httpx
from fastapi import Request  # noqa: TC002
from fastapi.responses import JSONResponse
from fastmcp import FastMCP
from fastmcp.server.openapi import MCPType, RouteMap
from fastmcp.server.openapi.server import FastMCPOpenAPI
from httpx import AsyncClient

from stock_analysis.schemas.report import ReportRetrieverBody, ReportRetrieverResponse
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
    tags={"retrieve"},
)
async def get_financial_report(query: str, stock_code: str) -> ReportRetrieverResponse:
    """Get financial report for a given stock code by calling the upstream API.

    Args:
        query: The query to use for retrieving the financial report.
        stock_code: The stock code to retrieve the financial report for.

    Returns:
        A ReportRetrieverResponse containing the retrieved financial report.
    """
    body = ReportRetrieverBody(query=query, stock_code=stock_code)
    response: httpx.Response = await client.post(
        "/reports/retrieve", json=body.model_dump()
    )
    response.raise_for_status()
    return ReportRetrieverResponse.model_validate(response.json())
