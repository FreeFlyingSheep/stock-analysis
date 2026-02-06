"""Chat thread managing service."""

from typing import TYPE_CHECKING

from sqlalchemy import func, select, update

from stock_analysis.models.chat import ChatThread

if TYPE_CHECKING:
    from sqlalchemy import Result, Select
    from sqlalchemy.ext.asyncio import AsyncSession


class ChatService:
    """Service for database operations on chat threads.

    Provides methods for querying chat threads with filtering and pagination,
    creating, updating, and soft-deleting threads.

    Attributes:
        db: AsyncSession instance for database operations.
    """

    db: AsyncSession
    """Database session for all operations."""

    def __init__(self, db_session: AsyncSession) -> None:
        """Initialize the ChatService with a database session.

        Args:
            db_session: AsyncSession instance for database operations.
        """
        self.db: AsyncSession = db_session

    async def get_chat_threads(
        self,
        status: str | None = None,
    ) -> list[ChatThread]:
        """Get all chat threads with optional status filtering.

        Args:
            status: Optional filter by status (active or deleted).

        Returns:
            List of ChatThread objects matching the criteria.
        """
        query: Select[tuple[ChatThread]] = select(ChatThread)

        if status:
            query = query.where(ChatThread.status == status)

        query = query.order_by(ChatThread.updated_at.desc())

        result: Result[tuple[ChatThread]] = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_chat_thread_by_id(self, thread_id: str) -> ChatThread | None:
        """Get a single chat thread by its thread_id.

        Args:
            thread_id: The unique thread identifier to search for.

        Returns:
            ChatThread object if found, None otherwise.
        """
        result: Result[tuple[ChatThread]] = await self.db.execute(
            select(ChatThread).where(ChatThread.thread_id == thread_id)
        )
        return result.scalar_one_or_none()

    async def create_chat_thread(
        self, thread_id: str, title: str, status: str = "active"
    ) -> ChatThread:
        """Create a new chat thread.

        Args:
            thread_id: Unique identifier for the chat thread.
            title: Title of the chat thread.
            status: Status of the thread. Defaults to "active".

        Returns:
            The newly created ChatThread object.
        """
        chat_thread = ChatThread(
            thread_id=thread_id,
            title=title,
            status=status,
        )
        self.db.add(chat_thread)
        await self.db.flush()
        await self.db.refresh(chat_thread)
        return chat_thread

    async def get_or_create_thread(
        self, thread_id: str, title: str, status: str = "active"
    ) -> ChatThread:
        """Get a chat thread by thread_id or create it if missing.

        Args:
            thread_id: Unique identifier for the chat thread.
            title: Title of the chat thread.
            status: Status of the thread. Defaults to "active".

        Returns:
            Existing or newly created ChatThread object.
        """
        existing: ChatThread | None = await self.get_chat_thread_by_id(thread_id)
        if existing is not None:
            return existing
        return await self.create_chat_thread(
            thread_id=thread_id,
            title=title,
            status=status,
        )

    async def touch_thread(self, thread_id: str) -> None:
        """Update the thread's updated_at timestamp.

        Args:
            thread_id: The thread identifier to update.
        """
        await self.db.execute(
            update(ChatThread)
            .where(ChatThread.thread_id == thread_id)
            .values(updated_at=func.now())
        )
        await self.db.flush()

    async def update_chat_thread(
        self,
        thread_id: str,
        title: str | None = None,
        status: str | None = None,
    ) -> ChatThread | None:
        """Update an existing chat thread.

        Args:
            thread_id: The unique thread identifier.
            title: Optional new title for the thread.
            status: Optional new status for the thread.

        Returns:
            Updated ChatThread object if found, None otherwise.
        """
        chat_thread: ChatThread | None = await self.get_chat_thread_by_id(thread_id)
        if not chat_thread:
            return None

        if title is not None:
            chat_thread.title = title
        if status is not None:
            chat_thread.status = status

        await self.db.flush()
        await self.db.refresh(chat_thread)
        return chat_thread

    async def delete_chat_thread(self, thread_id: str) -> ChatThread | None:
        """Soft delete a chat thread by setting status to 'deleted'.

        Args:
            thread_id: The unique thread identifier.

        Returns:
            Deleted ChatThread object if found, None otherwise.
        """
        return await self.update_chat_thread(thread_id, status="deleted")
