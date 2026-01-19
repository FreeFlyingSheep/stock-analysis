"""Stock auxiliary functions."""

from typing import Any


def _classify_market(stock_code: str) -> str:
    """Get the market classification based on stock code prefix.

    Args:
        stock_code: The stock code as a string.

    Returns:
        The market classification as a string.
    """
    if stock_code.startswith(("0", "3")):
        return "SZ"
    if stock_code.startswith("6"):
        return "SH"
    if stock_code.startswith("43"):
        return "NEEQ"
    if stock_code.startswith(("83", "87", "88")):
        return "BSE"
    return "UNKNOWN"


def is_valid_stock_code(stock_code: str) -> bool:
    """Check if the stock code is valid based on its market classification.

    Args:
        stock_code: The stock code as a string.

    Returns:
        True if the stock code is valid, False otherwise.
    """
    market: str = _classify_market(stock_code)
    return market != "UNKNOWN"


def get_stock_code_with_market(stock_code: str) -> str:
    """Get the stock code appended with its market classification.

    Args:
        stock_code: The stock code as a string.

    Returns:
        The stock code with market classification appended.
    """
    market: str = _classify_market(stock_code)
    return f"{stock_code.zfill(6)}.{market}"


def convert_stock_data(
    cninfo_data: dict[str, Any], yfinance_data: dict[str, Any]
) -> dict[str, Any]:
    """Convert and merge stock data from different sources.

    Args:
        cninfo_data: Stock data from CNInfo as a dictionary.
        yfinance_data: Stock data from Yahoo Finance as a dictionary.

    Returns:
        Merged stock data as a dictionary.
    """
    yfinance_data = {"history": {"records": yfinance_data}}
    merged_data: dict[str, Any] = {**cninfo_data, **yfinance_data}
    return merged_data
