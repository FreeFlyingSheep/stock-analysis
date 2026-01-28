"""MCP client for agent interactions."""

from typing import TYPE_CHECKING

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import StreamableHttpConnection

from stock_analysis.agent.graph import ChatAgent
from stock_analysis.settings import get_settings

if TYPE_CHECKING:
    from langchain_core.tools.base import BaseTool

    from stock_analysis.settings import Settings


async def init_agent() -> ChatAgent:
    """Initialize the MCP client for agent interactions.

    Returns:
        MultiServerMCPClient: Configured MCP client instance.
    """
    settings: Settings = get_settings()
    client = MultiServerMCPClient(
        {
            "stock-analysis": StreamableHttpConnection(
                {"transport": "streamable_http", "url": settings.mcp_url}
            )
        }
    )
    tools: list[BaseTool] = await client.get_tools()
    return ChatAgent(tools)
