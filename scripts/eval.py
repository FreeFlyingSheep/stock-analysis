"""Run evaluation suites with app-like component initialization."""

import asyncio
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Final

from langchain.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import StreamableHttpConnection
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from stock_analysis.agent.graph import ChatAgent
from stock_analysis.agent.llm import ChatModel, Embeddings
from stock_analysis.evals.agent import eval_agent
from stock_analysis.evals.chatbot import eval_chatbot
from stock_analysis.evals.llm import eval_llm
from stock_analysis.evals.mcp import eval_mcp
from stock_analysis.evals.rag import eval_rag
from stock_analysis.logger import get_logger
from stock_analysis.settings import get_settings
from stock_analysis.telemetry import setup_telemetry, shutdown_telemetry

if TYPE_CHECKING:
    import logging

    from stock_analysis.settings import Settings


EvalRunner = Callable[[ChatAgent, list[BaseTool] | None], Awaitable[None]]

logger: logging.Logger = get_logger(__name__)

DEFAULT_EVALS: Final[list[str]] = ["chatbot", "llm", "agent", "mcp", "rag"]
EVAL_RUNNERS: Final[dict[str, EvalRunner]] = {
    "chatbot": eval_chatbot,
    "llm": eval_llm,
    "agent": eval_agent,
    "mcp": eval_mcp,
    "rag": eval_rag,
}


async def main() -> None:
    """Initialize components and run selected evaluation suites."""
    settings: Settings = get_settings()
    setup_telemetry("stock-analysis-eval")

    try:
        mcp = MultiServerMCPClient(
            {
                "stock-analysis": StreamableHttpConnection(
                    {"transport": "streamable_http", "url": settings.mcp_url}
                )
            }
        )
        tools: list[BaseTool] = await mcp.get_tools()
        async with AsyncPostgresSaver.from_conn_string(
            settings.database_url
        ) as checkpointer:
            await checkpointer.setup()
            agent = ChatAgent(
                checkpointer,
                settings.prompts_dir,
                ChatModel(),
                Embeddings(),
            )

            for eval_name in DEFAULT_EVALS:
                logger.info("Running eval suite: %s", eval_name)
                try:
                    await EVAL_RUNNERS[eval_name](agent, tools)
                    logger.info("Completed eval suite: %s", eval_name)
                except Exception:
                    logger.exception("Eval suite failed: %s", eval_name)
    finally:
        shutdown_telemetry()


if __name__ == "__main__":
    asyncio.run(main())
