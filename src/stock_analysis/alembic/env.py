"""Alembic environment configuration."""

import logging
from logging.config import fileConfig
from pathlib import Path
from typing import TYPE_CHECKING

from alembic import context
from sqlalchemy import engine_from_config, pool

from stock_analysis.models.analysis import Analysis  # noqa: F401
from stock_analysis.models.base import Base
from stock_analysis.models.cninfo import CNInfoAPIResponse  # noqa: F401
from stock_analysis.models.stock import Stock  # noqa: F401
from stock_analysis.models.yahoo import YahooFinanceAPIResponse  # noqa: F401
from stock_analysis.settings import get_settings

if TYPE_CHECKING:
    from alembic.config import Config
    from sqlalchemy import Engine, MetaData
    from sqlalchemy.schema import SchemaItem

    from stock_analysis.settings import Settings


IGNORE_TABLES: list[str] = [
    "pgqueuer",
    "pgqueuer_log",
    "pgqueuer_schedules",
    "pgqueuer_statistics",
]


config: Config = context.config
settings: Settings = get_settings()

if config.config_file_name is not None:
    root: Path = Path(__file__).parents[3]
    fileConfig(root / "configs" / Path(config.config_file_name))
else:
    logging.basicConfig(level=settings.log_level)

config.set_main_option("sqlalchemy.url", settings.database_url_with_psycopg)

target_metadata: MetaData = Base.metadata


def include_object(
    object_: SchemaItem,
    name: str | None,
    type_: str,
    _reflected: bool,  # noqa: FBT001
    _compare_to: SchemaItem | None,
) -> bool:
    """Determine whether to include an object in autogeneration.

    Args:
        object_: The object being considered.
        name: The name of the object.
        type_: The type of the object (e.g., 'table', 'column').
        _reflected: Whether the object is reflected from the database.
        _compare_to: The object being compared to.

    Returns:
        True to include the object, False to exclude it.
    """
    return not (
        type_ == "table"
        and (name in IGNORE_TABLES or object_.info.get("skip_autogenerate", False))
    )


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url: str | None = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable: Engine = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
