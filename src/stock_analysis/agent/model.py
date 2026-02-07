"""LLM wrappers for stock analysis agent."""

from typing import TYPE_CHECKING

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from stock_analysis.settings import get_settings

if TYPE_CHECKING:
    from langchain.messages import AIMessage
    from langchain.tools import BaseTool
    from langchain_core.embeddings import Embeddings as BaseEmbeddings
    from langchain_core.language_models import BaseChatModel, LanguageModelInput
    from langgraph.graph.state import Runnable

    from stock_analysis.settings import Settings


class LLMError(Exception):
    """Custom exception for LLM-related errors."""


class LLM:
    """Wrapper around the OpenAI language model."""

    _llm: BaseChatModel | None
    """Instance of the OpenAI language model."""

    def __init__(self, llm: BaseChatModel | None = None) -> None:
        """Initialize the LLM wrapper.

        Args:
            llm: Optional instance of ChatOpenAI to use.
        """
        if llm is not None:
            self._llm = llm
            return

        settings: Settings = get_settings()
        if (
            settings.use_llm
            and settings.llm_model is not None
            and settings.llm_api_key is not None
            and settings.llm_server_base_url is not None
        ):
            self._llm = ChatOpenAI(
                model=settings.llm_model,
                api_key=settings.llm_api_key,
                base_url=settings.llm_server_base_url,
            )
        else:
            self._llm = None

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
        if self._llm is None:
            msg: str = "LLM is not configured."
            raise LLMError(msg)

        return self._llm.bind_tools(tools)

    def invoke(self, prompt: LanguageModelInput) -> AIMessage:
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

    async def ainvoke(self, prompt: LanguageModelInput) -> AIMessage:
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

    _embeddings: BaseEmbeddings | None
    """Instance of the OpenAI embeddings model."""

    def __init__(self, embeddings: BaseEmbeddings | None = None) -> None:
        """Initialize the LLM embeddings wrapper.

        Args:
            embeddings: Optional instance of OpenAIEmbeddings to use.
        """
        if embeddings is not None:
            self._embeddings = embeddings
            return

        settings: Settings = get_settings()
        if (
            settings.use_llm
            and settings.llm_embedding_model is not None
            and settings.llm_api_key is not None
            and settings.llm_server_base_url is not None
            and settings.llm_embedding_dimension is not None
        ):
            self._embeddings = OpenAIEmbeddings(
                model=settings.llm_embedding_model,
                dimensions=settings.llm_embedding_dimension,
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
