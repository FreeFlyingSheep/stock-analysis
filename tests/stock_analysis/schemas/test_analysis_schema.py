from datetime import UTC, datetime
from typing import Any

from stock_analysis.schemas.analysis import (
    AnalysisApiResponse,
    AnalysisDetailApiResponse,
    AnalysisIn,
    AnalysisOut,
    AnalysisPage,
)


def test_analysis_in() -> None:
    expected_score = 85.5
    payload: dict[str, Any] = {
        "stock_id": 1,
        "metrics": {"pe_ratio": 15.5, "pb_ratio": 2.3},
        "score": expected_score,
        "filtered": True,
    }
    analysis: AnalysisIn = AnalysisIn.model_validate(payload)

    assert analysis.stock_id == 1
    assert analysis.metrics == {"pe_ratio": 15.5, "pb_ratio": 2.3}
    assert analysis.score == expected_score
    assert analysis.filtered is True


def test_analysis_out() -> None:
    now: datetime = datetime.now(UTC)
    expected_score = 80.0
    analysis_out = AnalysisOut(
        stock_id=1,
        metrics={"pe_ratio": 15.5},
        score=expected_score,
        created_at=now,
        updated_at=now,
    )

    assert analysis_out.stock_id == 1
    assert analysis_out.metrics == {"pe_ratio": 15.5}
    assert analysis_out.score == expected_score
    assert analysis_out.created_at == now
    assert analysis_out.updated_at == now


def test_analysis_page() -> None:
    now: datetime = datetime.now(UTC)
    total_count = 5
    page_num = 1
    page_size = 50
    expected_list_len = 2
    analysis_list: list[AnalysisOut] = [
        AnalysisOut(
            stock_id=1,
            metrics={"pe_ratio": 15.5},
            score=85.0,
            created_at=now,
            updated_at=now,
        ),
        AnalysisOut(
            stock_id=2,
            metrics={"pe_ratio": 12.3},
            score=75.0,
            created_at=now,
            updated_at=now,
        ),
    ]

    page = AnalysisPage(
        total=total_count,
        page_num=page_num,
        page_size=page_size,
        data=analysis_list,
    )

    assert page.total == total_count
    assert page.page_num == page_num
    assert page.page_size == page_size
    assert len(page.data) == expected_list_len
    assert page.data[0].stock_id == 1
    second_stock_id = 2
    assert page.data[1].stock_id == second_stock_id


def test_analysis_api_response() -> None:
    now: datetime = datetime.now(UTC)
    analysis_list: list[AnalysisOut] = [
        AnalysisOut(
            stock_id=1,
            metrics={"pe_ratio": 15.5},
            score=85.0,
            created_at=now,
            updated_at=now,
        ),
    ]

    page = AnalysisPage(total=1, page_num=1, page_size=50, data=analysis_list)
    response = AnalysisApiResponse(data=page)

    assert response.data.total == 1
    assert response.data.page_num == 1
    assert len(response.data.data) == 1


def test_analysis_detail_api_response() -> None:
    now: datetime = datetime.now(UTC)
    expected_list_len = 2
    expected_score = 82.0
    analysis_list: list[AnalysisOut] = [
        AnalysisOut(
            stock_id=1,
            metrics={"pe_ratio": 15.5},
            score=85.0,
            created_at=now,
            updated_at=now,
        ),
        AnalysisOut(
            stock_id=1,
            metrics={"pe_ratio": 14.2},
            score=expected_score,
            created_at=now,
            updated_at=now,
        ),
    ]

    response = AnalysisDetailApiResponse(data=analysis_list)

    assert len(response.data) == expected_list_len
    assert response.data[0].stock_id == 1
    assert response.data[1].score == expected_score
