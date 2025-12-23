"""API data schemas for raw data."""

from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel


class RequestParam(BaseModel):
    """API request parameter specification from YAML.

    Attributes:
        key: The parameter key.
        label: The parameter label.
        param_type: The parameter type (e.g., 'string', 'integer').
        name: The parameter name (optional).
        value: The fixed value of the parameter (if any).
    """

    key: str
    label: str
    param_type: str
    name: str | None = None
    value: int | float | str | None = None


class RequestSpec(BaseModel):
    """HTTP request spec for an endpoint.

    Attributes:
        method: HTTP method (e.g., 'GET', 'POST').
        url: The full URL for the endpoint.
        params: Tuple of request parameters.
    """

    method: Literal["GET", "POST"]
    url: str
    params: tuple[RequestParam, ...] = ()

    @property
    def fixed_params(self) -> dict[str, int | float | str]:
        """Return a dict of fixed parameter labels and values."""
        return {p.label: p.value for p in self.params if p.value is not None}

    @property
    def required_params(self) -> frozenset[str]:
        """Return a set of labels for non-fixed parameters."""
        return frozenset(p.label for p in self.params if p.value is None)


class ApiSpec(BaseModel):
    """Complete endpoint specification parsed from YAML."""

    id: str
    name: str
    request: RequestSpec
    file_path: Path


class CNInfoFetchResult(BaseModel):
    """Result of a CNInfo API fetch operation.

    Attributes:
        request_params: Parameters used in the API request.
        response_code: HTTP response code from the API call.
        raw_json: Raw JSON response from the API call.
    """

    request_params: dict[str, int | float | str]
    response_code: int
    raw_json: dict[str, Any]


class CNInfoAPIResponseIn(BaseModel):
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
    """Schema for returning CNInfo API response records.

    Attributes:
        id: The id of the record.
        created_at: Timestamp when the record was created.
        updated_at: Timestamp when the data was fetched.
    """

    id: int
    created_at: datetime
    updated_at: datetime
