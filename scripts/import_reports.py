"""Import report PDF files to MinIO based on the reports CSV."""

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd
from minio import Minio

from stock_analysis.settings import get_settings

if TYPE_CHECKING:
    from stock_analysis.settings import Settings

logger: logging.Logger = logging.getLogger(__name__)


def create_bucket_if_not_exists(client: Minio, bucket_name: str) -> None:
    """Create a MinIO bucket if it doesn't already exist.

    Args:
        client: MinIO client instance.
        bucket_name: Name of the bucket to create.
    """
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)
        logger.info("Created MinIO bucket: %s", bucket_name)
    else:
        logger.info("MinIO bucket already exists: %s", bucket_name)


def read_csv(csv_path: Path) -> pd.DataFrame:
    """Read CSV file into DataFrame.

    Args:
        csv_path: Path to the CSV file containing report data.

    Returns:
        pd.DataFrame: DataFrame containing parsed and validated CSV data.

    Raises:
        FileNotFoundError: If CSV file doesn't exist at the specified path.
        ValueError: If CSV format is invalid or headers don't match expected format.
    """
    if not csv_path.exists():
        msg: str = f"CSV file not found: {csv_path}"
        raise FileNotFoundError(msg)

    df: pd.DataFrame = pd.read_csv(csv_path, encoding="utf-8", dtype=str)

    expected_headers: list[str] = [
        "year",
        "stock_code",
        "type",
        "file_name",
        "content_type",
    ]
    if df.columns.tolist() != expected_headers:
        msg = (
            f"CSV headers {df.columns.tolist()} do not match"
            f" expected format {expected_headers}"
        )
        raise ValueError(msg)

    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()

    return df


def import_reports(
    client: Minio, reports_dir: Path, bucket_name: str, data: pd.DataFrame
) -> None:
    """Import report files to MinIO.

    Args:
        client: MinIO client instance.
        reports_dir: Directory containing report files.
        bucket_name: Name of the MinIO bucket to upload files to.
        data: DataFrame containing report metadata from CSV.
    """
    imported_count: int = 0

    for _, row in data.iterrows():
        file_path: Path = reports_dir / row["file_name"]
        file_suffix: str = file_path.suffix.lower()

        if not file_path.exists():
            logger.error("Report file not found: %s", file_path)
            continue

        object_name: str = (
            f"reports/{row['year']}/{row['type']}/{row['stock_code']}{file_suffix}"
        )
        client.fput_object(
            bucket_name,
            object_name,
            str(file_path),
            content_type=row["content_type"],
        )
        logger.info("Uploaded: %s", object_name)
        imported_count += 1

    logger.info("Import complete: %s succeeded", imported_count)


def main() -> None:
    """Import report files from data/reports to MinIO."""
    settings: Settings = get_settings()
    logging.basicConfig(level=settings.log_level)

    client = Minio(
        settings.minio_endpoint,
        access_key=settings.minio_user,
        secret_key=settings.minio_password.get_secret_value(),
        secure=settings.minio_secure,
    )

    reports_dir: Path = Path(__file__).parents[1] / "data" / "reports"
    csv_file: Path = reports_dir / "reports.csv"
    bucket_name: str = settings.minio_bucket_raw

    create_bucket_if_not_exists(client, bucket_name)
    df: pd.DataFrame = read_csv(csv_file)
    import_reports(client, reports_dir, bucket_name, df)


if __name__ == "__main__":
    main()
