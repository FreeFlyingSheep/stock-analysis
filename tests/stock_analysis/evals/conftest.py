from typing import TYPE_CHECKING, Any

import pytest
from deepeval.models.base_model import DeepEvalBaseLLM
from langchain_openai import ChatOpenAI

from stock_analysis.agent.stream import convert_content_to_str
from stock_analysis.settings import get_settings

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel

    from stock_analysis.settings import Settings


settings: Settings = get_settings()
if "CHANGEME" in settings.llm_api_key.get_secret_value():
    pytest.skip(
        "LLM API key is not set. Skipping tests that require LLM.",
        allow_module_level=True,
    )


class EvalLLM(DeepEvalBaseLLM):
    model: DeepEvalBaseLLM

    def __init__(self, model: BaseChatModel) -> None:
        self.model = model  # type: ignore[assignment]

    def load_model(self) -> DeepEvalBaseLLM:
        return self.model  # type: ignore[return-value]

    def generate(self, prompt: str) -> str:
        chat_model: Any = self.load_model()
        return convert_content_to_str(chat_model.invoke(prompt).content)

    async def a_generate(self, prompt: str) -> str:
        chat_model: Any = self.load_model()
        return convert_content_to_str(await chat_model.ainvoke(prompt).content)

    def get_model_name(self) -> str:
        return "Custom Chat Model"


@pytest.fixture(scope="session")
def chat_model() -> BaseChatModel:
    return ChatOpenAI(
        model=settings.llm_chat_model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_server_base_url,
    )


@pytest.fixture(scope="session")
def eval_llm(chat_model: BaseChatModel) -> EvalLLM:
    return EvalLLM(model=chat_model)
