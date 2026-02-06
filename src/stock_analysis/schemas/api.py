"""API data schemas for HTTP requests and responses."""

from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from stock_analysis.schemas.base import BaseSchema


class RequestParam(BaseSchema):
    """API request parameter specification from YAML configuration.

    Attributes:
        key: The parameter key identifier.
        label: The parameter label for API requests.
        param_type: The parameter data type (e.g., 'string', 'integer').
        name: The parameter name (optional).
        value: The fixed parameter value (if any), overrides runtime values.
        fixed: Whether the parameter value is fixed (True) or variable (False).
    """

    key: str
    label: str
    param_type: str
    name: str | None = None
    value: int | float | str | None = None
    fixed: bool


class RequestSpec(BaseSchema):
    """HTTP request specification for an API endpoint.

    Attributes:
        method: HTTP method (GET or POST).
        url: The full URL for the endpoint.
        params: Tuple of request parameter specifications.
    """

    method: Literal["GET", "POST"]
    url: str
    params: tuple[RequestParam, ...] = ()

    @property
    def fixed_params(self) -> dict[str, int | float | str]:
        """Return dictionary mapping parameter labels to fixed values.

        Returns:
            Mapping of parameter labels to fixed values.
        """
        return {
            p.label: p.value for p in self.params if p.fixed and p.value is not None
        }

    @property
    def required_params(self) -> frozenset[str]:
        """Return set of parameter labels that require runtime values.

        Returns:
            Set of parameter labels requiring runtime values.
        """
        return frozenset(p.label for p in self.params if not p.fixed)


class ApiSpec(BaseSchema):
    """Complete API endpoint specification parsed from YAML.

    Contains all configuration needed to make requests to an API endpoint.

    Attributes:
        id: Unique endpoint identifier.
        name: Human-readable endpoint name.
        request: RequestSpec with URL, method, and parameters.
        file_path: Path to the source YAML configuration file.
    """

    id: str
    name: str
    request: RequestSpec
    file_path: Path


class CNInfoFetchResult(BaseSchema):
    """Result of a CNInfo API fetch operation.

    Attributes:
        request_params: Parameters used in the API request.
        response_code: HTTP response code from the API call.
        raw_json: Raw JSON response from the API call.
    """

    request_params: dict[str, int | float | str]
    response_code: int
    raw_json: dict[str, Any]


class JobPayload(BaseSchema):
    """Payload for data fetching jobs.

    Attributes:
        stock_code: The stock code to fetch data for.
    """

    stock_code: str


class CNInfoAPIResponseIn(BaseSchema):
    """Schema for creating CNInfo API response records.

    Attributes:
        endpoint: CNInfo endpoint name (e.g., 'balance_sheets', 'income_statement').
        stock_id: ID of the associated stock.
        params: Parameters used in the API request.
        response_code: HTTP response code from the API call.
        raw_json: Raw JSON response from the API call.
    """

    endpoint: str
    stock_id: int
    params: dict[str, int | float | str]
    response_code: int
    raw_json: dict[str, Any]


class CNInfoAPIResponseOut(CNInfoAPIResponseIn):
    """Schema for returning CNInfo API responses.

    Extends CNInfoAPIResponseIn with record ID and timestamps.

    Attributes:
        id: The unique identifier of the record.
        created_at: Timestamp when record was created.
        updated_at: Timestamp when data was fetched/updated.
    """

    id: int
    created_at: datetime
    updated_at: datetime


class YahooFinanceAPI(BaseSchema):
    """Yahoo Finance API request parameters schema.

    Attributes:
        symbol: Stock ticker symbol (e.g., '600000.SH').
        period: Historical data retrieval period.
        interval: Data point interval.
    """

    symbol: str
    period: Literal[
        "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"
    ]
    interval: Literal[
        "1m",
        "2m",
        "5m",
        "15m",
        "30m",
        "60m",
        "90m",
        "1h",
        "1d",
        "5d",
        "1wk",
        "1mo",
        "3mo",
    ]


class YahooFinanceAPIResponseIn(BaseSchema):
    """Schema for creating Yahoo Finance API response records.

    Attributes:
        stock_id: ID of the associated stock.
        params: Parameters used in the API request.
        raw_json: Raw JSON response from the API call.
    """

    stock_id: int
    params: dict[str, int | float | str]
    raw_json: str


class YahooFinanceAPIResponseOut(YahooFinanceAPIResponseIn):
    """Schema for returning Yahoo Finance API responses.

    Extends YahooFinanceAPIResponseIn with record ID and timestamps.

    Attributes:
        id: The unique identifier of the record.
        created_at: Timestamp when record was created.
        updated_at: Timestamp when data was fetched/updated.
    """

    id: int
    created_at: datetime
    updated_at: datetime
