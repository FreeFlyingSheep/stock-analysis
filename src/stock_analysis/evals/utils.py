"""Shared runner utilities for evaluation suites."""

from typing import TYPE_CHECKING
from uuid import uuid4

from deepeval.dataset import EvaluationDataset, Golden
from deepeval.evaluate import AsyncConfig, evaluate
from deepeval.test_case import LLMTestCase

if TYPE_CHECKING:
    from pathlib import Path

    from deepeval.metrics import BaseMetric
    from langchain.tools import BaseTool

    from stock_analysis.agent.graph import ChatAgent


def load_dataset(path: Path) -> EvaluationDataset:
    """Load evaluation dataset from a JSON file.

    Args:
        path: Path to the JSON file containing the evaluation dataset.

    Returns:
        An EvaluationDataset instance populated with goldens.
    """
    dataset = EvaluationDataset()
    dataset.add_goldens_from_json_file(path.as_posix())
    return dataset


async def run_eval_suite(
    *,
    agent: ChatAgent,
    dataset: EvaluationDataset,
    metrics: list[BaseMetric],
    tools: list[BaseTool] | None = None,
    locale: str = "zh-CN",
) -> None:
    """Run standard deepeval evaluation for a suite."""
    config = AsyncConfig(run_async=False)
    test_cases: list[LLMTestCase] = []

    for golden in dataset.goldens:
        if not isinstance(golden, Golden):
            continue

        golden.actual_output = await agent.ainvoke(
            thread_id=str(uuid4()),
            message=golden.input,
            locale=locale,
            tools=tools,
        )

        test_cases.append(
            LLMTestCase(
                input=golden.input,
                actual_output=golden.actual_output,
                expected_output=golden.expected_output,
                context=golden.context,
                retrieval_context=golden.retrieval_context,
                tools_called=golden.tools_called,
                expected_tools=golden.expected_tools,
                name=golden.name,
            )
        )

    evaluate(test_cases=test_cases, metrics=metrics, async_config=config)
