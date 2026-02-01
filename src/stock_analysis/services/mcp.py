"""MCP client for agent interactions."""

from http import HTTPStatus

from fastapi import (
    HTTPException,
    Request,  # noqa: TC002
)
from langchain_mcp_adapters.client import MultiServerMCPClient  # noqa: TC002


async def get_mcp(request: Request) -> MultiServerMCPClient:
    """Get MCP client.

    Args:
        request: FastAPI request object for accessing app state.

    Returns:
        Configured MCP client instance.

    Raises:
        HTTPException: If MCP service is unavailable.
    """
    client: MultiServerMCPClient | None = getattr(request.app.state, "mcp", None)
    if client is None:
        raise HTTPException(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            detail="MCP service unavailable",
        )

    return client
