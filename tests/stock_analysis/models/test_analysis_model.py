from datetime import UTC, datetime

from stock_analysis.models.analysis import Analysis


def test_analysis_repr() -> None:
    analysis = Analysis(
        id=1,
        stock_id=1,
        metrics={"pe_ratio": 15.5, "pb_ratio": 2.3},
        score=85.5,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    result: str = repr(analysis)
    assert "Analysis(" in result
    assert "id=1" in result
    assert "stock_id=1" in result
    assert "score=85.5" in result
    assert "created_at=" in result
    assert "updated_at=" in result
