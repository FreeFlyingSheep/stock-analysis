from datetime import UTC, datetime
from typing import Any

from stock_analysis.schemas.stock import (
    StockApiResponse,
    StockIn,
    StockListData,
    StockOut,
    StockPage,
)


def test_stock_in_validation_and_aliases() -> None:
    payload: dict[str, str] = {
        "stock_code": "000001",
        "company_name": "测试公司",
        "classification": "金融业",
        "industry": "银行业",
    }
    stock: StockIn = StockIn.model_validate(payload)

    dumped: dict[str, Any] = stock.model_dump(by_alias=True)
    assert dumped["stockCode"] == "000001"
    assert dumped["companyName"] == "测试公司"
    assert dumped["classification"] == "金融业"
    assert dumped["industry"] == "银行业"


def test_stock_out_response() -> None:
    stock_out = StockOut(
        stock_code="000001",
        company_name="测试公司",
        classification="金融业",
        industry="银行业",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    page = StockPage(total=1, page_num=1, page_size=50, data=[stock_out])
    data = StockListData(
        industries=["银行业"],
        classifications=["金融业"],
        stock_page=page,
    )
    response = StockApiResponse(data=data)

    dumped: dict[str, Any] = response.model_dump(by_alias=True)
    assert dumped["data"]["stockPage"]["data"][0]["stockCode"] == "000001"
    assert dumped["data"]["industries"] == ["银行业"]
    assert dumped["data"]["classifications"] == ["金融业"]
    assert dumped["data"]["stockPage"]["total"] == 1
