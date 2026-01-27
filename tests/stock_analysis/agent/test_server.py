from typing import TYPE_CHECKING

import pytest

from stock_analysis.schemas.stock import StockApiResponse

if TYPE_CHECKING:
    from fastmcp.client import Client, FastMCPTransport
    from fastmcp.client.client import CallToolResult
    from mcp.types import Tool

    from stock_analysis.models.stock import Stock


@pytest.mark.asyncio
async def test_mcp_server_tools(mcp_client: Client[FastMCPTransport]) -> None:
    tools: list[Tool] = await mcp_client.list_tools()
    assert len(tools) > 0


@pytest.mark.asyncio
async def test_mcp_server_get_stock(
    mcp_client: Client, seed_stocks: list[Stock]
) -> None:
    result: CallToolResult = await mcp_client.call_tool(
        "get_stocks",
        {
            "search": seed_stocks[0].company_name[:1],
        },
    )
    data: StockApiResponse = StockApiResponse.model_validate(result.data)
    assert len(data.data.stock_page.data) == 1
    assert data.data.stock_page.data[0].company_name == seed_stocks[0].company_name
