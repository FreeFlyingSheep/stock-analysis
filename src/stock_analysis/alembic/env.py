"""Alembic environment configuration."""

import logging
from logging.config import fileConfig
from pathlib import Path
from typing import TYPE_CHECKING

from alembic import context
from sqlalchemy import engine_from_config, pool

from stock_analysis.models.base import Base
from stock_analysis.models.stock import Stock  # noqa: F401
from stock_analysis.settings import get_settings

if TYPE_CHECKING:
    from alembic.config import Config
    from sqlalchemy import Engine, MetaData

    from stock_analysis.settings import Settings

config: Config = context.config
settings: Settings = get_settings()

if config.config_file_name is not None:
    root: Path = Path(__file__).parent.parent.parent.parent
    fileConfig(root / "configs" / Path(config.config_file_name))
else:
    logging.basicConfig(level=settings.log_level)

config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata: MetaData = Base.metadata


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
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
