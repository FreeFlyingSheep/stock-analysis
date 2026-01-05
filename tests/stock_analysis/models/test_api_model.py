from datetime import UTC, datetime
from http import HTTPStatus
from typing import Any

from stock_analysis.models.cninfo import CNInfoAPIResponse


def test_cninfo_api_response_attributes() -> None:
    test_params: dict[str, Any] = {"param1": "value1", "param2": 123}
    test_json: dict[str, Any] = {"resultcode": HTTPStatus.OK, "records": []}
    now: datetime = datetime.now(UTC)

    response = CNInfoAPIResponse(
        endpoint="income_statement",
        params=test_params,
        response_code=HTTPStatus.OK,
        raw_json=test_json,
        created_at=now,
        updated_at=now,
    )

    assert response.endpoint == "income_statement"
    assert response.params == test_params
    assert response.response_code == HTTPStatus.OK
    assert response.raw_json == test_json
    assert response.created_at == now
    assert response.updated_at == now
