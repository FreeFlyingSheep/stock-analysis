from typing import TYPE_CHECKING

from stock_analysis.settings import get_settings

if TYPE_CHECKING:
    from stock_analysis.settings import Settings


def test_read_settings() -> None:
    settings: Settings = get_settings(".env.example")  # type: ignore[call-arg]
    assert (
        settings.database_url
        == "postgresql+psycopg://postgres:**********@127.0.0.1:5432/stock_analysis"
    )
    assert settings.debug is False
    assert settings.log_level == "INFO"
