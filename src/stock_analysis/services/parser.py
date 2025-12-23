"""CNInfo data parser service."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class ParserError(RuntimeError):
    """Raised when parsing fails."""


class CNInfoParser:
    """Service for parsing raw CNInfo data into normalized tables."""

    _session: AsyncSession

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the parser.

        Args:
            session: Database session for reading/writing data.
        """
        self._session = session

    async def parse(self, record_id: int) -> None:
        """Parse a raw record by ID.

        Args:
            record_id: ID of the cninfo_raw record to parse.

        Raises:
            ParserError: If parsing fails.
        """
        msg: str = (
            f"CNInfoParser.parse is not yet implemented for record ID {record_id}"
        )
        raise NotImplementedError(msg)
