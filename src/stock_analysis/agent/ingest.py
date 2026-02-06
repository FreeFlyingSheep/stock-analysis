"""Ingestion module for stock analysis agent."""


class Ingestor:
    """Base ingestor class for stock analysis agent."""

    async def ingest(self, data: str) -> None:
        """Ingest data into the system.

        Args:
            data: The input data to be ingested.

        Returns:
            None
        """
        raise NotImplementedError
