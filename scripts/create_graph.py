"""Script to create and display the internal graph structure of the chat agent."""

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from stock_analysis.agent.graph import ChatAgent
from stock_analysis.settings import get_settings

if TYPE_CHECKING:
    from stock_analysis.settings import Settings


async def main() -> None:
    """Draw the agent's internal graph structure and display it as an image."""
    settings: Settings = get_settings()
    async with AsyncPostgresSaver.from_conn_string(
        settings.database_url
    ) as checkpointer:
        agent = ChatAgent(checkpointer=checkpointer, prompts_dir="configs/prompts")
        output_path = Path("data/agent.png")
        await asyncio.to_thread(
            output_path.write_bytes, agent.get_graph().draw_mermaid_png()
        )


if __name__ == "__main__":
    asyncio.run(main())
