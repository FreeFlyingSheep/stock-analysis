"""MCP client for agent interactions."""

from asyncio import Lock
from http import HTTPStatus
from typing import TYPE_CHECKING

from fastapi import (
    HTTPException,
    Request,  # noqa: TC002
)
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import StreamableHttpConnection

from stock_analysis.agent.graph import ChatAgent
from stock_analysis.settings import get_settings

if TYPE_CHECKING:
    from langchain_core.tools.base import BaseTool

    from stock_analysis.settings import Settings


_mcp_lock = Lock()


async def get_mcp(request: Request) -> ChatAgent:
    """Get MCP client. Initializes if not already present.

    Returns:
        MultiServerMCPClient: Configured MCP client instance.
    """
    if getattr(request.app.state, "mcp", None) is not None:
        return request.app.state.mcp

    async with _mcp_lock:
        if getattr(request.app.state, "mcp", None) is not None:
            return request.app.state.mcp

        try:
            settings: Settings = get_settings()
            client = MultiServerMCPClient(
                {
                    "stock-analysis": StreamableHttpConnection(
                        {"transport": "streamable_http", "url": settings.mcp_url}
                    )
                }
            )
            tools: list[BaseTool] = await client.get_tools()
            agent = ChatAgent(tools)
            request.app.state.mcp = agent
        except Exception as e:
            request.app.state.mcp = None
            raise HTTPException(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                detail="MCP service unavailable",
            ) from e
        else:
            return agent
