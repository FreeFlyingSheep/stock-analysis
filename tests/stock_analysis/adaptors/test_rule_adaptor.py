from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stock_analysis.adaptors.rule import RuleAdaptor


def test_rule_adaptor_compute_scores(
    rule_adaptor: RuleAdaptor,
) -> None:
    assert rule_adaptor.score() != 0.0
