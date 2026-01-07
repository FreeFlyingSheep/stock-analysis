"""Yahoo Finance adaptor for fetching historical stock price data."""

from typing import TYPE_CHECKING

import yfinance as yf  # type: ignore[import-untyped]
from aiolimiter import AsyncLimiter
from pydantic import ValidationError

from stock_analysis.schemas.api import YahooFinanceAPI

if TYPE_CHECKING:
    import pandas as pd


class YahooFinanceError(RuntimeError):
    """Error raised for Yahoo Finance adaptor issues."""


class YahooFinanceAdaptor:
    """Adaptor for fetching stock data from Yahoo Finance.

    Uses the yfinance library to retrieve historical stock price and volume data
    for specified symbols and time periods.

    Attributes:
        limiter: AsyncLimiter for controlling request rate.
        retry_attempts: Number of retry attempts for failed requests.
        period: Historical data period (e.g., '5y', '1mo').
        interval: Data point interval (e.g., '1d', '1mo').
    """

    limiter: AsyncLimiter
    retry_attempts: int
    period: str
    interval: str

    def __init__(
        self,
        limiter: AsyncLimiter | None = None,
        retry_attempts: int = 5,
        period: str = "5y",
        interval: str = "1mo",
    ) -> None:
        """Initialize the Yahoo Finance adaptor.

        Args:
            limiter: Optional AsyncLimiter to control request rate.
            retry_attempts: Number of retry attempts for failed requests.
            period: Data retrieval period.
            interval: Data retrieval interval.
        """
        self.limiter = limiter or AsyncLimiter(max_rate=5, time_period=1.0)
        self.retry_attempts = retry_attempts
        self.period = period
        self.interval = interval

    async def get_stock_history(self, symbol: str) -> str:
        """Fetch historical stock price and volume data for a given stock symbol.

        Args:
            symbol: The stock symbol to fetch data for (e.g., '600000.SH').

        Returns:
            JSON string containing historical stock data as list of records.

        Raises:
            YahooFinanceError: If data validation fails or fetch operation fails.
        """
        try:
            api: YahooFinanceAPI = YahooFinanceAPI.model_validate(
                {
                    "symbol": symbol,
                    "period": self.period,
                    "interval": self.interval,
                }
            )
        except ValidationError as e:
            msg: str = f"Validation error for Yahoo Finance API with symbol {symbol}"
            raise YahooFinanceError(msg) from e

        try:
            yf.config.network.retries = self.retry_attempts
            async with self.limiter:
                ticker: yf.Ticker = yf.Ticker(api.symbol)
                history_df: pd.DataFrame = ticker.history(
                    period=api.period, interval=api.interval
                )
                history: str = history_df.to_json(orient="records")
                return history
        except Exception as e:
            msg = f"Error fetching data from Yahoo Finance for symbol {symbol}"
            raise YahooFinanceError(msg) from e
