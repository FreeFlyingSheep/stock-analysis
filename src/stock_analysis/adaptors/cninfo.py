"""CNInfo adaptor that reads endpoint specs from YAML and fetches data."""

from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, Self

import yaml
from aiolimiter import AsyncLimiter
from httpx import AsyncClient, HTTPStatusError, RequestError
from tenacity import (
    AsyncRetrying,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from stock_analysis.schemas.api import (
    ApiSpec,
    CNInfoFetchResult,
    RequestParam,
    RequestSpec,
)

if TYPE_CHECKING:
    from types import TracebackType

    from httpx import Response


class CNInfoError(RuntimeError):
    """Error raised when HTTP or validation issues occur in CNInfo adaptor."""


def _parse_request_params(params: dict[str, Any]) -> tuple[RequestParam, ...]:
    """Parse request parameters from configuration dictionary.

    Args:
        params: Dictionary of parameter configurations from YAML spec.

    Returns:
        Tuple of validated RequestParam objects.
    """
    parsed: list[RequestParam] = []

    for key, param in params.items():
        label: str | None = param.get("label")
        param_type: str | None = param.get("type")
        name: str | None = param.get("name")
        value: Any | None = param.get("value")
        if not key or not label or not param_type:
            continue

        parsed.append(
            RequestParam(
                key=key,
                label=label,
                param_type=param_type,
                name=name,
                value=value,
                fixed=value is not None,
            )
        )

    return tuple(parsed)


def _load_specs(config_dir: Path) -> dict[str, ApiSpec]:
    """Load and parse all CNInfo API endpoint specifications from YAML files.

    Reads all YAML files in the config directory and parses them into
    ApiSpec objects, indexed by endpoint id.

    Args:
        config_dir: Path to directory containing endpoint YAML specifications.

    Returns:
        Dictionary mapping endpoint IDs to their ApiSpec objects.

    Raises:
        CNInfoError: If no valid specifications are found in the directory.
    """
    specs: dict[str, ApiSpec] = {}

    for path in sorted(config_dir.glob("*.yaml")):
        raw: dict[str, Any] | None = yaml.safe_load(path.read_text())
        if not raw:
            continue

        api: Any | None = raw.get("api")
        if not api:
            continue

        spec_id: str | None = api.get("id")
        name: str | None = api.get("name")
        request: Any | None = api.get("request")
        if not spec_id or not name or not request:
            continue

        method: Literal["GET", "POST"] | None = request.get("method")
        url: str | None = request.get("url")
        if not method or not url:
            continue

        parameters: dict[str, Any] | None = request.get("params")
        if parameters is None or not isinstance(parameters, dict):
            parameters = {}
        params: tuple[RequestParam, ...] = _parse_request_params(parameters)

        spec = ApiSpec(
            id=spec_id,
            name=name,
            request=RequestSpec(
                method=method,
                url=url,
                params=params,
            ),
            file_path=path,
        )
        specs[spec.id] = spec

    if not specs:
        msg: str = f"No valid CNInfo specs found in {config_dir}"
        raise CNInfoError(msg)
    return specs


class CNInfoAdaptor:
    """Async adaptor for CNInfo endpoints defined in YAML specs."""

    client: AsyncClient | None
    timeout: float
    limiter: AsyncLimiter
    retry_attempts: int
    wait: wait_exponential
    _config_dir: Path
    _specs: dict[str, ApiSpec]
    _use_private_client: bool = False

    def __init__(  # noqa: PLR0913
        self,
        *,
        config_dir: Path | None = None,
        client: AsyncClient | None = None,
        timeout: float = 30.0,
        limiter: AsyncLimiter | None = None,
        retry_attempts: int = 5,
        wait: wait_exponential | None = None,
    ) -> None:
        """Initialize the CNInfo adaptor.

        If a client is provided, the caller is responsible for its lifecycle.

        Args:
            config_dir: Directory containing CNInfo YAML specs.
            client: Pre-initialized HTTPX AsyncClient.
            timeout: HTTP request timeout in seconds.
            limiter: Async rate limiter for requests.
            retry_attempts: Number of retry attempts for failed requests.
            wait: Tenacity wait strategy between retries.
        """
        self._config_dir: Path = (
            config_dir or Path(__file__).parents[3] / "configs" / "api" / "cninfo"
        )
        self._specs = _load_specs(self._config_dir)
        self.client = client
        self.timeout = timeout
        self.limiter = limiter or AsyncLimiter(max_rate=1, time_period=5.0)
        self.retry_attempts = retry_attempts
        self.wait: wait_exponential = wait or wait_exponential(min=5, max=10)
        if client is None:
            self._use_private_client = True

    @property
    def available_endpoints(self) -> frozenset[str]:
        """Get set of available endpoint IDs.

        Returns:
            Frozenset of endpoint IDs (e.g., 'balance_sheets', 'income_statement').
        """
        return frozenset(self._specs.keys())

    async def __aenter__(self) -> Self:
        """Enter async context manager and initialize HTTP client.

        Creates a new AsyncClient if one was not provided during initialization.

        Returns:
            Self: The CNInfoAdaptor instance for use in async with block.
        """
        self._use_private_client = self.client is None
        if self.client is None:
            self.client = AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc_val: BaseException | None,
        _exc_tb: TracebackType | None,
    ) -> None:
        """Exit async context manager and cleanup HTTP client.

        Closes the AsyncClient if it was created internally. Leaves external
        clients open for caller to manage.

        Args:
            _exc_type: Exception type if one was raised, None otherwise.
            _exc_val: Exception instance if one was raised, None otherwise.
            _exc_tb: Exception traceback if one was raised, None otherwise.
        """
        if self._use_private_client and self.client is not None:
            await self.client.aclose()
            self.client = None

    def set_unfixed_request_params(
        self, endpoint: str, **kwargs: float | str
    ) -> tuple[RequestParam, ...]:
        """Set unfixed request parameters for an endpoint.

        This method is used to validate and set values for parameters that do not
        have fixed values in the YAML spec. It will be called automatically before
        making a request.

        Args:
            endpoint: CNInfo endpoint ID.
            **kwargs: Parameter key-value pairs to set.

        Returns:
            Tuple of RequestParam with updated values.

        Raises:
            CNInfoError: If a parameter is unknown, fixed, or has a type mismatch.
        """
        if not kwargs:
            return ()

        spec: ApiSpec = self.get_spec(endpoint)
        for param in spec.request.params:
            if param.key in kwargs:
                if param.fixed:
                    msg: str = (
                        f"Cannot override fixed param '{param.key}' for {endpoint}"
                    )
                    raise CNInfoError(msg)

                type_str: str = type(kwargs[param.key]).__name__
                if type_str == "int":
                    type_str = "integer"
                elif type_str == "float":
                    type_str = "number"
                elif type_str == "str":
                    type_str = "string"
                if param.param_type != type_str:
                    msg = (
                        f"Param '{param.key}' for {endpoint} must be of type "
                        f"'{param.param_type}', got '{type_str}' instead."
                    )
                    raise CNInfoError(msg)

                param.value = kwargs[param.key]

        return tuple(spec.request.params)

    def get_spec(self, endpoint: str) -> ApiSpec:
        """Get the API specification for a given endpoint ID.

        Args:
            endpoint: CNInfo endpoint ID to retrieve spec for.

        Returns:
            ApiSpec object containing endpoint configuration.

        Raises:
            CNInfoError: If endpoint ID is not found in loaded specifications.
        """
        if endpoint not in self._specs:
            msg: str = f"Unknown CNInfo endpoint id: {endpoint}"
            raise CNInfoError(msg)

        return self._specs[endpoint]

    def _load_json(self, response: Response) -> dict[str, Any]:
        """Load and parse JSON from HTTPX response object.

        Args:
            response: HTTPX Response object from an API request.

        Returns:
            Dictionary containing parsed JSON data from response.

        Raises:
            CNInfoError: If response body is not valid JSON.
        """
        try:
            return response.json()
        except ValueError as e:
            msg: str = "Failed to parse CNInfo JSON response"
            raise CNInfoError(msg) from e

    async def fetch(self, endpoint: str, **kwargs: str) -> CNInfoFetchResult:
        """Fetch data from a CNInfo endpoint with validated parameters.

        Makes an HTTP request to the specified endpoint with validated and merged
        parameters (both fixed from spec and runtime values).

        Args:
            endpoint: CNInfo endpoint ID to fetch from.
            **kwargs: Runtime parameter key-value pairs to set for the request.

        Returns:
            CNInfoFetchResult containing merged params, response code, and raw JSON.

        Raises:
            CNInfoError: If client not initialized, required params missing, or
                request fails after all retries.
        """
        spec: ApiSpec = self.get_spec(endpoint)
        if not self.client:
            msg: str = "Client not initialized. Use 'async with' context manager."
            raise CNInfoError(msg)

        params: tuple[RequestParam, ...] = self.set_unfixed_request_params(
            endpoint, **kwargs
        )
        merged_params: dict[str, int | float | str] = {
            **spec.request.fixed_params,
            **{p.label: p.value for p in params if p.value is not None},
        }
        missing: frozenset[str] = spec.request.required_params - merged_params.keys()
        if missing:
            msg = f"Missing required params for {endpoint}: {sorted(missing)}"
            raise CNInfoError(msg)

        def should_retry(exception: BaseException) -> bool:
            if isinstance(exception, RequestError):
                return True
            return bool(
                isinstance(exception, HTTPStatusError)
                and exception.response is not None
                and exception.response.status_code
                in {
                    HTTPStatus.REQUEST_TIMEOUT,
                    HTTPStatus.TOO_MANY_REQUESTS,
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    HTTPStatus.BAD_GATEWAY,
                    HTTPStatus.SERVICE_UNAVAILABLE,
                    HTTPStatus.GATEWAY_TIMEOUT,
                }
            )

        retrying = AsyncRetrying(
            reraise=True,
            stop=stop_after_attempt(self.retry_attempts),
            wait=self.wait,
            retry=retry_if_exception(should_retry),
        )
        try:
            async for attempt in retrying:
                with attempt:
                    async with self.limiter:
                        response: Response = await self.client.request(
                            spec.request.method,
                            spec.request.url,
                            params=merged_params,
                        )
                    response.raise_for_status()
                    return CNInfoFetchResult(
                        request_params=merged_params,
                        response_code=response.status_code,
                        raw_json=self._load_json(response),
                    )
        except HTTPStatusError as e:
            msg = f"CNInfo HTTP {e.response.status_code} for {endpoint}"
            raise CNInfoError(msg) from e
        except RequestError as e:
            msg = f"Request to {spec.request.url} failed: {e}"
            raise CNInfoError(msg) from e
        msg = f"Failed to fetch data from {endpoint}"
        raise CNInfoError(msg)
