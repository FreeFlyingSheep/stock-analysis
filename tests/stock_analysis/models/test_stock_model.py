from stock_analysis.models.stock import Stock


def test_stock_repr() -> None:
    stock = Stock(
        stock_code="000001",
        company_name="测试公司",
        classification="金融业",
        industry="银行业",
    )

    result: str = repr(stock)
    assert "Stock(" in result
    assert "000001" in result
    assert "测试公司" in result
    assert "金融业" in result
    assert "银行业" in result
