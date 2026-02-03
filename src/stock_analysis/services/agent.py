"""Agent instance for agent interactions."""

from http import HTTPStatus

from fastapi import (
    HTTPException,
    Request,  # noqa: TC002
)

from stock_analysis.agent.graph import ChatAgent  # noqa: TC001


async def get_agent(request: Request) -> ChatAgent:
    """Get agent instance.

    Args:
        request: FastAPI request object for accessing app state.

    Returns:
        Configured agent instance.

    Raises:
        HTTPException: If agent service is unavailable.
    """
    agent: ChatAgent | None = getattr(request.app.state, "agent", None)
    if agent is None:
        raise HTTPException(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            detail="Agent service unavailable",
        )

    return agent
