import json
from pathlib import Path
from typing import Any

import pytest

from stock_analysis.adaptors.rule import RuleAdaptor


@pytest.fixture
def data() -> dict[str, Any]:
    data: dict[str, Any] = {}
    data_dir: Path = Path(__file__).parents[3] / "data" / "api" / "cninfo"
    for file in data_dir.iterdir():
        with file.open("r", encoding="utf-8") as f:
            content: dict[str, Any] = json.load(f)
            content = content["data"]
            data[file.name.removesuffix(".json")] = content
    return data


@pytest.fixture
def rule_adaptor(data: dict[str, Any]) -> RuleAdaptor:
    rule_file_path: Path = (
        Path(__file__).parents[3] / "configs" / "rules" / "scoring_rules_sample.yaml"
    )
    return RuleAdaptor(rule_file_path=rule_file_path, data=data)


def test_rule_adaptor_compute_scores(
    rule_adaptor: RuleAdaptor,
) -> None:
    assert rule_adaptor.score() != 0.0
