"""Grade nodes for relevance checking of retrieved documents."""

from langchain.messages import (
    AIMessage,
    AnyMessage,  # noqa: TC002
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from opentelemetry import trace
from pydantic import BaseModel, Field

from stock_analysis.agent.helper import find_last_human_content, load_prompt
from stock_analysis.agent.llm import ChatModel  # noqa: TC001
from stock_analysis.agent.prompt import PromptManager  # noqa: TC001
from stock_analysis.agent.state import State  # noqa: TC001

tracer: trace.Tracer = trace.get_tracer(__name__)


class GradeDocuments(BaseModel):
    """Grade documents using a binary score for relevance check.

    Attributes:
        binary_score: Relevance score indicating if the document is relevant or not.
    """

    binary_score: str = Field(
        description="Relevance score: 'yes' if relevant, or 'no' if not relevant"
    )


async def grade_documents(
    state: State, prompt_manager: PromptManager, chat: ChatModel
) -> dict:
    """Grade retrieved documents for relevance using a dedicated prompt.

    Extracts the user query and the retrieved ToolMessage contents,
    builds a grading prompt, and stores the binary result in state.

    Args:
        state: Current state containing messages.
        prompt_manager: The prompt manager to use for loading prompts.
        chat: The chat model to use for grading.

    Returns:
        Updated state with grade_result and incremented chat_calls.
    """
    with tracer.start_as_current_span("chat_agent.grade_documents") as span:
        locale: str = state.get("locale", "en-US")
        query: str = find_last_human_content(state["messages"])
        span.set_attribute("query_preview", query[:100])

        retrieved_parts: list[str] = []
        for msg in reversed(state["messages"]):
            if isinstance(msg, ToolMessage):
                content: str | list[str | dict] = msg.content
                retrieved_parts.append(
                    content if isinstance(content, str) else str(content)
                )
            elif isinstance(msg, AIMessage):
                break
        span.set_attribute("retrieved_document_count", len(retrieved_parts))

        retrieved: str = (
            "\n\n".join(reversed(retrieved_parts))
            or load_prompt(prompt_manager, "grade_no_documents", locale).strip()
        )
        grade_input: str = load_prompt(prompt_manager, "grade_input", locale).format(
            question=query, documents=retrieved
        )

        messages: list[AnyMessage] = [
            SystemMessage(content=load_prompt(prompt_manager, "grade", locale)),
            HumanMessage(content=grade_input),
        ]
        response: dict | BaseModel = await chat.with_structured_output(
            GradeDocuments
        ).ainvoke(messages)
        score: str = GradeDocuments.model_validate(response).binary_score
        span.set_attribute("grade_result", score)

        return {
            "grade_result": score,
            "chat_calls": state.get("chat_calls", 0) + 1,
        }
