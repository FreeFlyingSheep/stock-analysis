"""Eval model wrappers for LLM-based evaluations."""

from typing import TYPE_CHECKING, Any

from deepeval.models.base_model import DeepEvalBaseLLM
from langchain_openai import ChatOpenAI

from stock_analysis.agent.stream import convert_content_to_str
from stock_analysis.settings import get_settings

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel

    from stock_analysis.settings import Settings


class EvalLLM(DeepEvalBaseLLM):
    """Eval model wrapper for LLM-based evaluations."""

    model: DeepEvalBaseLLM

    def __init__(self, model: BaseChatModel) -> None:
        """Initialize evaluator with a chat model."""
        self.model = model  # type: ignore[assignment]

    def load_model(self) -> DeepEvalBaseLLM:
        """Load and return the underlying chat model."""
        return self.model  # type: ignore[return-value]

    def generate(self, prompt: str) -> str:
        """Generate text output from the evaluator model."""
        chat_model: Any = self.load_model()
        return convert_content_to_str(chat_model.invoke(prompt).content)

    async def a_generate(self, prompt: str) -> str:
        """Asynchronously generate text output from the evaluator model."""
        chat_model: Any = self.load_model()
        return convert_content_to_str(await chat_model.ainvoke(prompt).content)

    def get_model_name(self) -> str:
        """Return a display name of evaluator model."""
        return "Custom Chat Model"


def get_eval_llm() -> EvalLLM:
    """Get an instance of EvalLLM."""
    settings: Settings = get_settings()
    model = ChatOpenAI(
        model=settings.deepeval_llm_chat_model,
        api_key=settings.deepeval_llm_api_key,
        base_url=settings.deepeval_llm_server_base_url,
    )
    return EvalLLM(model=model)
