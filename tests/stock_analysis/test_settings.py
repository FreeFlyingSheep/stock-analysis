import os
from typing import TYPE_CHECKING

from stock_analysis.settings import get_settings

if TYPE_CHECKING:
    from stock_analysis.settings import Settings


def test_read_settings() -> None:
    saved_vars: dict[str, str] = {}
    var_names: list[str] = [
        "DATABASE_USER",
        "DATABASE_PASSWORD",
        "DATABASE_HOST",
        "DATABASE_PORT",
        "DATABASE_DB",
        "DEBUG",
        "LOG_LEVEL",
    ]
    for var_name in var_names:
        if var_name in os.environ:
            saved_vars[var_name] = os.environ.pop(var_name)

    try:
        settings: Settings = get_settings(".env.example")  # type: ignore[call-arg]
        assert (
            settings.database_url_with_psycopg
            == "postgresql+psycopg://postgres:password@127.0.0.1:5432/stock_analysis"
        )
        assert settings.debug is False
        assert settings.log_level == "INFO"
    finally:
        os.environ.update(saved_vars)
