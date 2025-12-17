"""Tests for database services."""

from typing import TYPE_CHECKING, Any

import pytest
from sqlalchemy import text

if TYPE_CHECKING:
    from sqlalchemy import Result
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_database_connection(async_session: AsyncSession) -> None:
    result: Result[Any] = await async_session.execute(text("SELECT 1"))
    num: int = result.scalar_one()
    assert num == 1


@pytest.mark.asyncio
async def test_insert_and_select(async_session: AsyncSession) -> None:
    await async_session.execute(
        text(
            "CREATE TABLE IF NOT EXISTS test_table"
            "(id SERIAL PRIMARY KEY, name VARCHAR(255))",
        ),
    )
    await async_session.execute(
        text("INSERT INTO test_table (name) VALUES ('test name')"),
    )
    await async_session.flush()

    result: Result[Any] = await async_session.execute(
        text("SELECT name FROM test_table WHERE name = 'test name'"),
    )
    name: str = result.scalar_one()
    assert name == "test name"
