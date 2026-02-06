"""Retriever definitions for stock analysis agent."""


class Retriever:
    """Base retriever class for stock analysis agent."""

    async def retrieve(self, query: str) -> str:
        """Retrieve relevant information based on the query.

        Args:
            query: The input query for which to retrieve information.

        Returns:
            A string containing the retrieved information.

        Raises:
            NotImplementedError: Always raised by the base class.
        """
        raise NotImplementedError
