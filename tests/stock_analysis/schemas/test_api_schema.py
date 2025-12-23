from datetime import UTC, datetime
from http import HTTPStatus
from pathlib import Path
from typing import Any

from stock_analysis.schemas.api import (
    ApiSpec,
    CNInfoAPIResponseIn,
    CNInfoAPIResponseOut,
    RequestParam,
    RequestSpec,
)


def test_request_param_with_name() -> None:
    param = RequestParam(
        key="stock_code",
        label="scode",
        param_type="string",
        name="Stock Code",
        value="000001",
    )

    assert param.label == "scode"
    assert param.param_type == "string"
    assert param.name == "Stock Code"
    assert param.value == "000001"


def test_request_spec_fixed_params() -> None:
    params: tuple[RequestParam, ...] = (
        RequestParam(
            key="api_key", label="apikey", param_type="string", value="secret"
        ),
        RequestParam(key="format", label="format", param_type="string", value="json"),
        RequestParam(key="stock_code", label="scode", param_type="string"),
    )
    spec = RequestSpec(method="POST", url="https://api.example.com", params=params)

    fixed_labels: dict[str, Any] = spec.fixed_params
    assert fixed_labels == {"apikey": "secret", "format": "json"}


def test_request_spec_required_params() -> None:
    params: tuple[RequestParam, ...] = (
        RequestParam(
            key="api_key", label="apikey", param_type="string", value="secret"
        ),
        RequestParam(key="stock_code", label="scode", param_type="string"),
        RequestParam(key="year", label="year", param_type="string"),
    )
    spec = RequestSpec(method="GET", url="https://api.example.com", params=params)

    required_labels: frozenset[str] = spec.required_params
    assert required_labels == frozenset({"scode", "year"})


def test_request_spec_empty_params() -> None:
    spec = RequestSpec(method="GET", url="https://api.example.com")

    assert spec.params == ()
    assert spec.fixed_params == {}
    assert spec.required_params == frozenset()


def test_api_spec_complete() -> None:
    params: tuple[RequestParam, ...] = (
        RequestParam(key="stock_code", label="scode", param_type="string"),
    )
    request = RequestSpec(method="POST", url="https://api.cninfo.com.cn", params=params)
    spec = ApiSpec(
        id="balance_sheets",
        name="Balance Sheets",
        request=request,
        file_path=Path("/configs/api/cninfo/get_balance_sheets.yaml"),
    )

    assert spec.id == "balance_sheets"
    assert spec.name == "Balance Sheets"
    assert spec.request.method == "POST"
    assert spec.request.url == "https://api.cninfo.com.cn"
    assert len(spec.request.params) == len(params)


def test_cninfo_api_response_in() -> None:
    params: dict[str, str] = {"scode": "000001"}
    payload: dict[str, Any] = {
        "endpoint": "balance_sheets",
        "stock_id": 1,
        "params": params,
        "response_code": HTTPStatus.OK,
        "raw_json": {"resultcode": HTTPStatus.OK, "records": []},
    }

    response: CNInfoAPIResponseIn = CNInfoAPIResponseIn.model_validate(payload)

    assert response.endpoint == "balance_sheets"
    assert response.params == params
    assert response.response_code == HTTPStatus.OK


def test_cninfo_api_response_out() -> None:
    params: dict[str, int | float | str] = {
        "scode": "000001",
        "format": "json",
    }
    now: datetime = datetime.now(UTC)
    response = CNInfoAPIResponseOut(
        id=1,
        endpoint="balance_sheets",
        stock_id=1,
        params=params,
        response_code=HTTPStatus.OK,
        raw_json={"resultcode": 200},
        created_at=now,
        updated_at=now,
    )

    dumped: dict[str, Any] = response.model_dump()
    assert dumped["id"] == 1
    assert dumped["endpoint"] == "balance_sheets"
    assert dumped["response_code"] == HTTPStatus.OK
    assert len(dumped["params"]) == len(params)
