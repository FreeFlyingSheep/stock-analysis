"""LLM wrappers for stock analysis agent."""

from typing import TYPE_CHECKING

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from stock_analysis.settings import get_settings

if TYPE_CHECKING:
    from langchain.messages import AIMessage
    from langchain.tools import BaseTool
    from langchain_core.language_models import LanguageModelInput
    from langgraph.graph.state import Runnable

    from stock_analysis.settings import Settings


class LLMError(Exception):
    """Custom exception for LLM-related errors."""


class LLM:
    """Wrapper around the OpenAI language model."""

    _llm: ChatOpenAI | Runnable[LanguageModelInput, AIMessage] | None
    """Instance of the OpenAI language model."""

    def __init__(self, tools: list[BaseTool] | None = None) -> None:
        """Initialize the LLM wrapper."""
        settings: Settings = get_settings()
        if (
            settings.use_llm
            and settings.llm_model is not None
            and settings.llm_api_key is not None
            and settings.llm_server_base_url is not None
        ):
            llm = ChatOpenAI(
                model=settings.llm_model,
                api_key=settings.llm_api_key,
                base_url=settings.llm_server_base_url,
            )
            self._llm = llm.bind_tools(tools) if tools is not None else llm
        else:
            self._llm = None

    def invoke(self, prompt: str | list[str | dict]) -> AIMessage:
        """Invoke the language model with the given prompt.

        Args:
            prompt: The prompt to send to the language model.

        Returns:
            The response from the language model.

        Raises:
            LLMError: If the LLM is not configured.
        """
        if self._llm is None:
            msg: str = "LLM is not configured."
            raise LLMError(msg)

        return self._llm.invoke(prompt)

    async def ainvoke(self, prompt: str | list[str | dict]) -> AIMessage:
        """Asynchronously invoke the language model with the given prompt.

        Args:
            prompt: The prompt to send to the language model.

        Returns:
            The response from the language model.

        Raises:
            LLMError: If the LLM is not configured.
        """
        if self._llm is None:
            msg: str = "LLM is not configured."
            raise LLMError(msg)

        return await self._llm.ainvoke(prompt)


class Embeddings:
    """Wrapper around the OpenAI embeddings model."""

    _embeddings: OpenAIEmbeddings | None
    """Instance of the OpenAI embeddings model."""

    def __init__(self) -> None:
        """Initialize the LLM embeddings wrapper."""
        settings: Settings = get_settings()
        if (
            settings.use_llm
            and settings.llm_embedding_model is not None
            and settings.llm_api_key is not None
            and settings.llm_server_base_url is not None
        ):
            self._embeddings = OpenAIEmbeddings(
                model=settings.llm_embedding_model,
                api_key=settings.llm_api_key,
                base_url=settings.llm_server_base_url,
            )
        else:
            self._embeddings = None

    def query(self, text: str) -> list[float]:
        """Get the embedding vector for the given text.

        Args:
            text: The text to embed.

        Returns:
            The embedding vector.

        Raises:
            LLMError: If the embeddings model is not configured.
        """
        if self._embeddings is None:
            msg: str = "LLM embeddings model is not configured."
            raise LLMError(msg)

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
        if self._embeddings is None:
            msg: str = "LLM embeddings model is not configured."
            raise LLMError(msg)

        return await self._embeddings.aembed_query(text)
