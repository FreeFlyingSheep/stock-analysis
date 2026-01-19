from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stock_analysis.adapters.rule import RuleAdapter


def test_rule_adapter_compute_scores(
    rule_adapter: RuleAdapter,
) -> None:
    assert rule_adapter.score() != 0.0
