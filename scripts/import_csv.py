"""Import stock data from a CSV file into the database."""

import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd
from pydantic import ValidationError
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)

from stock_analysis.models.stock import Stock
from stock_analysis.schemas.stock import StockIn
from stock_analysis.settings import get_settings

if TYPE_CHECKING:
    import os

    from sqlalchemy.dialects.postgresql import Insert
    from sqlalchemy.ext.asyncio import (
        AsyncEngine,
        AsyncSession,
    )

    from stock_analysis.settings import Settings

logger: logging.Logger = logging.getLogger(__name__)


def read_csv(csv_path: str | os.PathLike) -> pd.DataFrame:
    """Read CSV file into DataFrame.

    Args:
        csv_path: Path to the CSV file containing stock data.

    Returns:
        pd.DataFrame: DataFrame containing parsed and validated CSV data.

    Raises:
        FileNotFoundError: If CSV file doesn't exist at the specified path.
        ValueError: If CSV format is invalid or headers don't match expected format.
    """
    csv_file = Path(csv_path)
    if not csv_file.exists():
        msg: str = f"CSV file not found: {csv_path}"
        raise FileNotFoundError(msg)

    df: pd.DataFrame = pd.read_csv(csv_file, encoding="utf-8", dtype=str)

    expected_headers: list[str] = [
        "上市公司代码",
        "上市公司简称",
        "门类代码",
        "门类简称",
        "次类代码",
        "次类简称",
        "大类代码",
        "大类简称",
    ]
    if df.columns.tolist() != expected_headers:
        msg = (
            f"CSV headers {df.columns.tolist()} do not match"
            f" expected format {expected_headers}"
        )
        raise ValueError(msg)

    mapper: dict[str, str] = {
        "上市公司代码": "stock_code",
        "上市公司简称": "company_name",
        "门类简称": "classification",
        "大类简称": "industry",
    }
    df = df.rename(columns=mapper)[list(mapper.values())]
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()

    return df


async def import_stocks_from_csv(db: AsyncSession, csv_path: str | os.PathLike) -> int:
    """Import stocks from CSV file into database.

    Args:
        db: AsyncSession instance for database operations.
        csv_path: Path to the CSV file containing stock data.

    Returns:
        int: Number of valid stock records successfully imported.

    Raises:
        FileNotFoundError: If CSV file doesn't exist at the specified path.
        ValueError: If CSV format is invalid or headers don't match expected format.
    """
    csv_file = Path(csv_path)
    if not csv_file.exists():
        msg: str = f"CSV file not found: {csv_path}"
        raise FileNotFoundError(msg)

    df: pd.DataFrame = await asyncio.to_thread(read_csv, csv_file)
    valid_records: list[dict[str, str]] = []
    for r in df.to_dict(orient="records"):
        try:
            s: StockIn = StockIn.model_validate(r)
        except ValidationError as e:
            logger.warning(
                "Skipping invalid stock %s: %s",
                r.get("stock_code"),
                e.errors(),
            )
            continue
        valid_records.append(s.model_dump())

    if not valid_records:
        return 0

    stmt: Insert = insert(Stock).values(valid_records)
    stmt = stmt.on_conflict_do_update(
        index_elements=[Stock.stock_code],
        set_={
            "company_name": stmt.excluded.company_name,
            "classification": stmt.excluded.classification,
            "industry": stmt.excluded.industry,
            "updated_at": func.now(),
        },
    )

    await db.execute(stmt)
    await db.commit()
    return len(valid_records)


async def main() -> None:
    """Import stocks from CSV into the database.

    Entry point for the CSV import script. Initializes settings, creates
    database engine and session, then imports stock data from the default
    CSV file location.
    """
    settings: Settings = get_settings()
    logging.basicConfig(level=settings.log_level)
    engine: AsyncEngine = create_async_engine(
        settings.database_url,
        echo=settings.debug,
    )
    async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(
        engine,
        expire_on_commit=False,
    )
    async with async_session() as session:
        csv_file: Path = Path(__file__).parent.parent / "data" / "stocks.csv"
        count: int = await import_stocks_from_csv(session, csv_file)
        logger.info("Imported %d stocks from CSV.", count)


if __name__ == "__main__":
    asyncio.run(main())
