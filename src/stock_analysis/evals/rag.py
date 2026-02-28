"""Evaluation RAG for stock analysis agent."""

from pathlib import Path
from typing import TYPE_CHECKING

from deepeval.metrics import (
    AnswerRelevancyMetric,
    FaithfulnessMetric,
)

from stock_analysis.evals.model import get_eval_llm
from stock_analysis.evals.utils import load_dataset, run_eval_suite
from stock_analysis.settings import get_settings

if TYPE_CHECKING:
    from deepeval.dataset import EvaluationDataset
    from deepeval.metrics import BaseMetric
    from langchain.tools import BaseTool

    from stock_analysis.agent.graph import ChatAgent
    from stock_analysis.evals.model import EvalLLM
    from stock_analysis.settings import Settings


async def eval_rag(agent: ChatAgent, tools: list[BaseTool] | None = None) -> None:
    """Evaluate RAG performance of the stock analysis agent.

    Args:
        agent: The stock analysis agent to evaluate.
        tools: Optional MCP tools available to the agent during evaluation.
    """
    settings: Settings = get_settings()
    dataset_dir = Path(settings.dataset_dir)
    dataset: EvaluationDataset = load_dataset(dataset_dir / "rag.json")

    eval_model: EvalLLM = get_eval_llm()

    answer_relevancy: AnswerRelevancyMetric = AnswerRelevancyMetric(
        threshold=0.7,
        model=eval_model,
    )
    faithfulness: FaithfulnessMetric = FaithfulnessMetric(
        threshold=0.7,
        model=eval_model,
    )
    metrics: list[BaseMetric] = [
        answer_relevancy,
        faithfulness,
    ]
    await run_eval_suite(
        agent=agent,
        dataset=dataset,
        metrics=metrics,
        tools=tools,
    )
