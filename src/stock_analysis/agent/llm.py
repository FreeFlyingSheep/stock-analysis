"""LLM wrappers for stock analysis agent."""

from typing import TYPE_CHECKING

from aiolimiter import AsyncLimiter
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from stock_analysis.settings import get_settings

if TYPE_CHECKING:
    from langchain.messages import AIMessage
    from langchain.tools import BaseTool
    from langchain_core.embeddings import Embeddings as BaseEmbeddings
    from langchain_core.language_models import BaseChatModel, LanguageModelInput
    from langgraph.graph.state import Runnable
    from pydantic import BaseModel

    from stock_analysis.settings import Settings


class ChatModel:
    """Wrapper around the OpenAI language model."""

    _chat: BaseChatModel
    """Instance of the OpenAI language model."""
    _rpm_limiter: AsyncLimiter
    """Rate limiter for RPM (requests per minute) - 1000 RPM for chat."""
    _tpm_limiter: AsyncLimiter
    """Rate limiter for TPM (tokens per minute) - 50000 TPM for chat."""

    def __init__(self, chat: BaseChatModel | None = None) -> None:
        """Initialize the LLM wrapper.

        Args:
            chat: Optional instance of ChatOpenAI to use.
        """
        self._rpm_limiter = AsyncLimiter(max_rate=1000, time_period=60)
        self._tpm_limiter = AsyncLimiter(max_rate=50000, time_period=60)

        if chat is not None:
            self._chat = chat
            return

        settings: Settings = get_settings()
        self._chat = ChatOpenAI(
            model=settings.llm_chat_model,
            api_key=settings.llm_api_key,
            base_url=settings.llm_server_base_url,
        )

    def bind_tools(
        self, tools: list[BaseTool]
    ) -> Runnable[LanguageModelInput, AIMessage]:
        """Bind tools to the LLM for tool use.

        Args:
            tools: List of tools to bind.

        Returns:
            A Runnable that can use the tools with the LLM.

        Raises:
            LLMError: If the LLM is not configured.
        """
        return self._chat.bind_tools(tools)

    def with_structured_output(
        self, schema: dict | type[BaseModel]
    ) -> Runnable[LanguageModelInput, dict | BaseModel]:
        """Bind a structured output schema to the LLM.

        Args:
            schema: The schema to bind, either as a dict or a Pydantic model.

        Returns:
            A Runnable that will return output conforming to the schema.
        """
        return self._chat.with_structured_output(schema)

    def invoke(self, prompt: LanguageModelInput) -> AIMessage:
        """Invoke the language model with the given prompt.

        Args:
            prompt: The prompt to send to the language model.

        Returns:
            The response from the language model.

        Raises:
            LLMError: If the LLM is not configured.
        """
        return self._chat.invoke(prompt)

    async def ainvoke(self, prompt: LanguageModelInput) -> AIMessage:
        """Asynchronously invoke the language model with the given prompt.

        Args:
            prompt: The prompt to send to the language model.

        Returns:
            The response from the language model.

        Raises:
            LLMError: If the LLM is not configured.
        """
        async with self._rpm_limiter, self._tpm_limiter:
            return await self._chat.ainvoke(prompt)


class Embeddings:
    """Wrapper around the OpenAI embeddings model."""

    _embeddings: BaseEmbeddings
    """Instance of the OpenAI embeddings model."""
    _rpm_limiter: AsyncLimiter
    """Rate limiter for RPM (requests per minute) - 2000 RPM for embeddings."""
    _tpm_limiter: AsyncLimiter
    """Rate limiter for TPM (tokens per minute) - 500000 TPM for embeddings."""

    def __init__(self, embeddings: BaseEmbeddings | None = None) -> None:
        """Initialize the LLM embeddings wrapper.

        Args:
            embeddings: Optional instance of OpenAIEmbeddings to use.
        """
        self._rpm_limiter = AsyncLimiter(max_rate=2000, time_period=60)
        self._tpm_limiter = AsyncLimiter(max_rate=500000, time_period=60)

        if embeddings is not None:
            self._embeddings = embeddings
            return

        settings: Settings = get_settings()
        self._embeddings = OpenAIEmbeddings(
            model=settings.llm_embedding_model,
            dimensions=settings.llm_embedding_dimension,
            api_key=settings.llm_api_key,
            base_url=settings.llm_server_base_url,
        )

    def query(self, text: str) -> list[float]:
        """Get the embedding vector for the given text.

        Args:
            text: The text to embed.

        Returns:
            The embedding vector.

        Raises:
            LLMError: If the embeddings model is not configured.
        """
        return self._embeddings.embed_query(text)

    async def aquery(self, text: str) -> list[float]:
        """Asynchronously get the embedding vector for the given text.

        Args:
            text: The text to embed.

        Returns:
            The embedding vector.

        Raises:
            LLMError: If the embeddings model is not configured.
        """
        async with self._rpm_limiter, self._tpm_limiter:
            return await self._embeddings.aembed_query(text)
