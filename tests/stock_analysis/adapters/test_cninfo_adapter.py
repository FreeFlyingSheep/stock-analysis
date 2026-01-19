from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest
import pytest_asyncio
from httpx import HTTPStatusError
from httpx._client import AsyncClient

from stock_analysis.adapters.cninfo import CNInfoAdapter, CNInfoError
from stock_analysis.schemas.api import RequestParam

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Awaitable, Callable
    from pathlib import Path

    from aiolimiter import AsyncLimiter
    from httpx import AsyncClient

    from stock_analysis.schemas.api import ApiSpec, CNInfoFetchResult


@pytest_asyncio.fixture
async def client_ok(
    httpx_client_factory: Callable[
        [int, bytes], Awaitable[tuple[AsyncClient, dict[str, int]]]
    ],
) -> AsyncGenerator[tuple[AsyncClient, dict[str, int]]]:
    result: tuple[AsyncClient, dict[str, int]] = await httpx_client_factory(
        HTTPStatus.OK, b'{"code": 200, "records": []}'
    )
    client: AsyncClient = result[0]
    yield client, result[1]
    await client.aclose()


@pytest_asyncio.fixture
async def client_unauthorized(
    httpx_client_factory: Callable[
        [int, bytes], Awaitable[tuple[AsyncClient, dict[str, int]]]
    ],
) -> AsyncGenerator[tuple[AsyncClient, dict[str, int]]]:
    result: tuple[AsyncClient, dict[str, int]] = await httpx_client_factory(
        HTTPStatus.UNAUTHORIZED, b""
    )
    client: AsyncClient = result[0]
    yield client, result[1]
    await client.aclose()


@pytest_asyncio.fixture
async def client_too_many_requests(
    httpx_client_factory: Callable[
        [int, bytes], Awaitable[tuple[AsyncClient, dict[str, int]]]
    ],
) -> AsyncGenerator[tuple[AsyncClient, dict[str, int]]]:
    result: tuple[AsyncClient, dict[str, int]] = await httpx_client_factory(
        HTTPStatus.TOO_MANY_REQUESTS, b""
    )
    client: AsyncClient = result[0]
    yield client, result[1]
    await client.aclose()


def test_adapter_initialization(
    yaml_config_dir: Path, async_limiter: AsyncLimiter
) -> None:
    timeout: float = 2.0
    retry_attempts: int = 2
    adapter = CNInfoAdapter(
        config_dir=yaml_config_dir,
        timeout=timeout,
        limiter=async_limiter,
        retry_attempts=retry_attempts,
    )
    assert adapter.timeout == timeout
    assert adapter.limiter is async_limiter
    assert adapter.retry_attempts == retry_attempts
    assert adapter.available_endpoints == {"balance_sheets", "income_statement"}


def test_adapter_no_specs_error(tmp_path: Path) -> None:
    empty_dir: Path = tmp_path / "empty"
    empty_dir.mkdir()

    with pytest.raises(CNInfoError) as e:
        CNInfoAdapter(config_dir=empty_dir)
    assert "No valid CNInfo specs found" in str(e.value)


def test_get_spec(yaml_config_dir: Path) -> None:
    adapter = CNInfoAdapter(config_dir=yaml_config_dir)
    spec: ApiSpec = adapter.get_spec("balance_sheets")

    assert spec.id == "balance_sheets"
    assert spec.name == "资产负债表"
    assert spec.request.method == "GET"


def test_get_spec_unknown(yaml_config_dir: Path) -> None:
    endpoint: str = "unknown_endpoint"
    adapter = CNInfoAdapter(config_dir=yaml_config_dir)

    with pytest.raises(CNInfoError) as e:
        adapter.get_spec(endpoint)
    assert f"Unknown CNInfo endpoint id: {endpoint}" in str(e.value)


def test_set_unfixed_request_params(yaml_config_dir: Path) -> None:
    adapter = CNInfoAdapter(config_dir=yaml_config_dir)
    params: tuple[RequestParam, ...] = adapter.set_unfixed_request_params(
        "balance_sheets"
    )
    assert params == ()

    params = adapter.set_unfixed_request_params("income_statement", stock_code="000001")
    expected: tuple[RequestParam, ...] = (
        RequestParam(
            key="stock_code",
            label="scode",
            param_type="string",
            name="股票代码",
            value="000001",
            fixed=False,
        ),
        RequestParam(
            key="sign_flag", label="sign", param_type="integer", value=1, fixed=True
        ),
    )
    assert params == expected


def test_set_unfixed_request_params_invalid(yaml_config_dir: Path) -> None:
    adapter = CNInfoAdapter(config_dir=yaml_config_dir)

    with pytest.raises(CNInfoError) as e:
        adapter.set_unfixed_request_params("income_statement", stock_code=1)
    assert (
        "Param 'stock_code' for income_statement must be of type 'string',"
        " got 'integer' instead." in str(e.value)
    )

    with pytest.raises(CNInfoError) as e:
        adapter.set_unfixed_request_params(
            "income_statement", stock_code="000001", sign_flag=2
        )
    assert "Cannot override fixed param 'sign_flag'" in str(e.value)


@pytest.mark.asyncio
async def test_fetch_success(
    cninfo_adapter: CNInfoAdapter,
    client_ok: tuple[AsyncClient, dict[str, int]],
) -> None:
    cninfo_adapter.client = client_ok[0]
    result: CNInfoFetchResult = await cninfo_adapter.fetch("balance_sheets")
    assert result.request_params == {}
    assert result.response_code == HTTPStatus.OK
    assert result.raw_json == {"code": HTTPStatus.OK, "records": []}
    assert client_ok[1]["count"] == 1


@pytest.mark.asyncio
async def test_fetchclient_not_initialized(yaml_config_dir: Path) -> None:
    adapter = CNInfoAdapter(config_dir=yaml_config_dir)
    adapter.client = None

    with pytest.raises(CNInfoError) as e:
        await adapter.fetch("balance_sheets")
    assert "Client not initialized" in str(e.value)


@pytest.mark.asyncio
async def test_fetch_error(
    cninfo_adapter: CNInfoAdapter,
    client_unauthorized: tuple[AsyncClient, dict[str, int]],
) -> None:
    cninfo_adapter.client = client_unauthorized[0]
    with pytest.raises(CNInfoError) as e:
        await cninfo_adapter.fetch("income_statement")
    assert "Missing required params" in str(e.value)

    with pytest.raises(CNInfoError) as e:
        await cninfo_adapter.fetch("income_statement", stock_code="000001")
    assert "CNInfo HTTP" in str(e.value)
    assert client_unauthorized[1]["count"] == 1

    cause: BaseException | None = e.value.__cause__
    assert isinstance(cause, HTTPStatusError)
    assert cause.response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.asyncio
async def test_fetch_retry(
    cninfo_adapter: CNInfoAdapter,
    client_too_many_requests: tuple[AsyncClient, dict[str, int]],
) -> None:
    cninfo_adapter.client = client_too_many_requests[0]
    with pytest.raises(CNInfoError) as e:
        await cninfo_adapter.fetch("balance_sheets")
    assert "CNInfo HTTP" in str(e.value)
    assert client_too_many_requests[1]["count"] == cninfo_adapter.retry_attempts

    cause: BaseException | None = e.value.__cause__
    assert isinstance(cause, HTTPStatusError)
    assert cause.response.status_code == HTTPStatus.TOO_MANY_REQUESTS
