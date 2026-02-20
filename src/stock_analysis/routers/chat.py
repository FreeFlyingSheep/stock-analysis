"""Chat router definitions."""

import asyncio
from http import HTTPStatus
from time import time
from typing import TYPE_CHECKING, Annotated
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,  # noqa: TC002
)
from langchain_mcp_adapters.client import MultiServerMCPClient  # noqa: TC002
from opentelemetry import trace
from pydantic import ValidationError
from redis.asyncio import Redis  # noqa: TC002
from redis.exceptions import LockError, LockNotOwnedError
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: TC002
from sse_starlette import EventSourceResponse

from stock_analysis.agent.graph import ChatAgent  # noqa: TC001
from stock_analysis.logger import get_logger
from stock_analysis.models.chat import ChatThread
from stock_analysis.schemas.chat import (
    ChatStartIn,  # noqa: TC001
    ChatStartOut,
    ChatThreadCreateIn,  # noqa: TC001
    ChatThreadDetailResponse,
    ChatThreadOut,
    ChatThreadsResponse,
    ChatThreadUpdateIn,  # noqa: TC001
    StreamEvent,
)
from stock_analysis.services.agent import get_agent
from stock_analysis.services.cache import CacheService, get_redis
from stock_analysis.services.chat import ChatService
from stock_analysis.services.database import get_db
from stock_analysis.services.mcp import get_mcp

if TYPE_CHECKING:
    import logging
    from collections.abc import AsyncGenerator

    from langchain_core.tools.base import BaseTool
    from redis.asyncio.client import PubSub
    from redis.asyncio.lock import Lock

    from stock_analysis.models.chat import ChatThread


RUN_TTL_SEC = 60 * 20
BUF_TTL_SEC = 60 * 60 * 6
LOCK_TTL_SEC = 60 * 10
PING_INTERVAL_SEC = 15

logger: logging.Logger = get_logger(__name__)
tracer: trace.Tracer = trace.get_tracer(__name__)

router = APIRouter()

_running_tasks: dict[str, asyncio.Task] = {}


async def _update_cache(
    thread_id: str,
    message_id: str,
    payload: str,
    event_type: str,
    cache_service: CacheService,
) -> None:
    buf_key: str = f"buf:{thread_id}:{message_id}"
    run_key: str = f"run:{thread_id}:{message_id}"
    status_key: str = f"status:{thread_id}:{message_id}"
    channel: str = f"channel:{thread_id}:{message_id}"
    await cache_service.push_to_list(buf_key, payload)
    await cache_service.publish(channel, payload)
    await cache_service.set_data(status_key, event_type, RUN_TTL_SEC)
    await cache_service.expire(buf_key, BUF_TTL_SEC)
    await cache_service.expire(run_key, RUN_TTL_SEC)


def _set_run_generation_span_attrs(  # noqa: PLR0913
    span: trace.Span,
    *,
    thread_id: str,
    message_id: str,
    locale: str,
    stock_code: str | None,
    message: str,
) -> None:
    span.set_attribute("thread_id", thread_id)
    span.set_attribute("message_id", message_id)
    span.set_attribute("locale", locale)
    span.set_attribute("has_stock_code", stock_code is not None)
    span.set_attribute("message_length", len(message))


def _start_lock_renew_task(lock: Lock, stop: asyncio.Event) -> asyncio.Task[None]:
    async def renew() -> None:
        try:
            while not stop.is_set():
                await asyncio.sleep(LOCK_TTL_SEC / 3)
                await lock.extend(LOCK_TTL_SEC)
        except Exception:
            logger.exception("Failed to extend lock TTL")

    return asyncio.create_task(renew())


async def _stream_generation_tokens(  # noqa: PLR0913
    *,
    agent: ChatAgent,
    cache_service: CacheService,
    thread_id: str,
    message: str,
    locale: str,
    stock_code: str | None,
    tools: list[BaseTool],
    buf_key: str,
    channel: str,
) -> int:
    seq: int = 0
    async for token in agent.astream_events(
        thread_id,
        message,
        locale,
        stock_code,
        tools,
    ):
        event = StreamEvent(id=str(seq), event="token", data=token)
        payload = event.model_dump_json()
        await cache_service.push_to_list(buf_key, payload)
        await cache_service.publish(channel, payload)
        seq += 1
    return seq


async def _finalize_generation(
    *,
    thread_id: str,
    message_id: str,
    cache_service: CacheService,
    status: str,
    seq: int = 0,
) -> None:
    if status == "done":
        event = StreamEvent(id=str(seq), event="done", data="")
    else:
        event = StreamEvent(id="0", event="error", data="Error during chat streaming")
    payload = event.model_dump_json()
    await _update_cache(
        thread_id,
        message_id,
        payload,
        status,
        cache_service,
    )


async def _cleanup_generation(
    lock: Lock, stop: asyncio.Event, task: asyncio.Task
) -> None:
    stop.set()
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        logger.debug("Failed to cancel renew task")
    try:
        await lock.release()
    except LockError, LockNotOwnedError:
        logger.exception("Failed to release lock")


async def _run_generation(
    start_in: ChatStartIn,
    cache_service: CacheService,
    client: MultiServerMCPClient,
    agent: ChatAgent,
) -> None:
    thread_id: str = start_in.thread_id
    message_id: str = start_in.message_id
    message: str = start_in.message
    locale: str = start_in.locale
    stock_code: str | None = start_in.stock_code
    buf_key: str = f"buf:{thread_id}:{message_id}"
    channel: str = f"channel:{thread_id}:{message_id}"

    with tracer.start_as_current_span("chat.run_generation") as span:
        _set_run_generation_span_attrs(
            span,
            thread_id=thread_id,
            message_id=message_id,
            locale=locale,
            stock_code=stock_code,
            message=message,
        )

        lock: Lock = cache_service.acquire_lock(thread_id, timeout=LOCK_TTL_SEC)
        if not await lock.acquire():
            span.set_attribute("lock_acquired", value=False)
            await _finalize_generation(
                thread_id=thread_id,
                message_id=message_id,
                cache_service=cache_service,
                status="error",
            )
            return
        span.set_attribute("lock_acquired", value=True)

        stop = asyncio.Event()
        renew_task: asyncio.Task[None] = _start_lock_renew_task(lock, stop)

        try:
            tools: list[BaseTool] = await client.get_tools()
            span.set_attribute("tool_count", len(tools))
            seq: int = await _stream_generation_tokens(
                agent=agent,
                cache_service=cache_service,
                thread_id=thread_id,
                message=message,
                locale=locale,
                stock_code=stock_code,
                tools=tools,
                buf_key=buf_key,
                channel=channel,
            )

            span.set_attribute("token_events", seq)
            await _finalize_generation(
                thread_id=thread_id,
                message_id=message_id,
                cache_service=cache_service,
                status="done",
                seq=seq,
            )
            span.set_attribute("final_status", "done")
        except Exception as err:
            span.set_attribute("final_status", "error")
            span.set_attribute("error_type", err.__class__.__name__)
            logger.exception("Error during generation")
            await _finalize_generation(
                thread_id=thread_id,
                message_id=message_id,
                cache_service=cache_service,
                status="error",
            )
        finally:
            await _cleanup_generation(lock, stop, renew_task)


@router.post("/chat/start")
async def start_chat(
    start_in: ChatStartIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
    client: Annotated[MultiServerMCPClient, Depends(get_mcp)],
    agent: Annotated[ChatAgent, Depends(get_agent)],
) -> ChatStartOut:
    """Start a new chat thread.

    Args:
        start_in: Input data for starting the chat.
        db: Database session dependency.
        redis: Redis dependency.
        client: MCP client dependency.
        agent: Chat agent dependency.

    Returns:
        Response from starting the chat thread.

    Raises:
        HTTPException: If the input message is empty or the thread cannot be started.
    """
    thread_id: str = start_in.thread_id
    message_id: str = start_in.message_id
    message: str = start_in.message.strip()
    if len(message) == 0:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Message cannot be empty.",
        )

    run_key: str = f"run:{thread_id}:{message_id}"
    status_key: str = f"status:{thread_id}:{message_id}"
    stream_url: str = f"/chat/stream?thread_id={thread_id}&message_id={message_id}"

    with tracer.start_as_current_span("chat.start") as span:
        span.set_attribute("thread_id", thread_id)
        span.set_attribute("message_id", message_id)
        span.set_attribute("locale", start_in.locale)
        span.set_attribute("has_stock_code", start_in.stock_code is not None)
        span.set_attribute("message_length", len(message))
        span.set_attribute("run_key", run_key)

        cache_service = CacheService(redis)
        created: bool = await cache_service.set_data_if_not_exists(
            run_key,
            "running",
            ttl=RUN_TTL_SEC,
        )
        span.set_attribute("run_created", created)

        status: str | None = await cache_service.get_data(status_key)
        span.set_attribute("cached_status", status or "missing")

        task_started: bool = False
        task_running: bool = False
        if created:
            task_key: str = run_key
            if task_key not in _running_tasks or _running_tasks[task_key].done():
                created_task: asyncio.Task[None] = asyncio.create_task(
                    _run_generation(start_in, cache_service, client, agent)
                )
                _running_tasks[task_key] = created_task
                task_started = True

                def _cleanup_task(_: asyncio.Task, key: str = task_key) -> None:
                    if _running_tasks.get(key) is created_task:
                        _running_tasks.pop(key, None)

                created_task.add_done_callback(_cleanup_task)

                chat_service = ChatService(db)
                await chat_service.get_or_create_thread(
                    thread_id=thread_id,
                    title="New Chat",
                    status="active",
                )
                await chat_service.touch_thread(thread_id)
            task_running = (
                task_key in _running_tasks and not _running_tasks[task_key].done()
            )
        else:
            existing_task: asyncio.Task | None = _running_tasks.get(run_key)
            task_running = existing_task is not None and not existing_task.done()
        span.set_attribute("task_started", task_started)
        span.set_attribute("task_running", task_running)
        if not created:
            span.add_event(
                "duplicate_start_request",
                {
                    "thread_id": thread_id,
                    "message_id": message_id,
                    "cached_status": status or "missing",
                    "task_running": task_running,
                },
            )

        span.set_attribute("stream_url", stream_url)
        return ChatStartOut(stream_url=stream_url)


@router.post("/chats")
async def create_chat(
    payload: ChatThreadCreateIn,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ChatThreadOut:
    """Create a chat thread or return an existing one.

    Args:
        payload: Payload containing thread creation data.
        db: Database session dependency.

    Returns:
        Created or existing chat thread.
    """
    thread_id: str = payload.thread_id or f"chat_{uuid4().hex}"
    title: str = payload.title or "New Chat"
    status: str = payload.status or "active"
    chat_service = ChatService(db)
    thread: ChatThread = await chat_service.get_or_create_thread(
        thread_id=thread_id,
        title=title,
        status=status,
    )
    return ChatThreadOut.model_validate(thread)


@router.patch("/chats/{thread_id}")
async def update_chat(
    thread_id: str,
    payload: ChatThreadUpdateIn,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ChatThreadOut:
    """Update a chat thread.

    Args:
        thread_id: Thread identifier to update.
        payload: Payload containing updated thread fields.
        db: Database session dependency.

    Returns:
        Updated chat thread.

    Raises:
        HTTPException: If the chat thread does not exist.
    """
    chat_service = ChatService(db)
    thread: ChatThread | None = await chat_service.update_chat_thread(
        thread_id=thread_id,
        title=payload.title,
        status=payload.status,
    )
    if thread is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Chat thread not found.",
        )
    return ChatThreadOut.model_validate(thread)


@router.delete("/chats/{thread_id}")
async def delete_chat(
    thread_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ChatThreadOut:
    """Soft delete a chat thread.

    Args:
        thread_id: Thread identifier to delete.
        db: Database session dependency.

    Returns:
        Soft-deleted chat thread.

    Raises:
        HTTPException: If the chat thread does not exist.
    """
    chat_service = ChatService(db)
    thread: ChatThread | None = await chat_service.delete_chat_thread(thread_id)
    if thread is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Chat thread not found.",
        )
    return ChatThreadOut.model_validate(thread)


async def _stream_existing_data(
    request: Request,
    thread_id: str,
    message_id: str,
    start: int,
    cache_service: CacheService,
) -> AsyncGenerator[dict[str, str]]:
    buf_key: str = f"buf:{thread_id}:{message_id}"
    with tracer.start_as_current_span("chat.stream_existing_data") as span:
        span.set_attribute("thread_id", thread_id)
        span.set_attribute("message_id", message_id)
        span.set_attribute("start_index", start)
        span.set_attribute("buf_key", buf_key)

        existing: list[str] = await cache_service.get_from_list(buf_key, start, -1)
        span.set_attribute("existing_event_count", len(existing))

        replayed_events: int = 0
        replay_terminated_by: str = "none"
        for item in existing:
            if await request.is_disconnected():
                replay_terminated_by = "client_disconnected"
                span.set_attribute("replayed_event_count", replayed_events)
                span.set_attribute("replay_terminated_by", replay_terminated_by)
                return

            try:
                event: StreamEvent = StreamEvent.model_validate_json(item)
            except ValidationError:
                logger.warning("Invalid event in buffer: %s", item)
                continue

            replayed_events += 1
            yield event.model_dump()

            if event.event in ("done", "error"):
                replay_terminated_by = f"buffer_terminal_{event.event}"
                span.set_attribute("replayed_event_count", replayed_events)
                span.set_attribute("replay_terminated_by", replay_terminated_by)
                return

        span.set_attribute("replayed_event_count", replayed_events)
        span.set_attribute("replay_terminated_by", replay_terminated_by)


async def _stream_data(
    request: Request,
    thread_id: str,
    message_id: str,
    start: int,
    cache_service: CacheService,
) -> AsyncGenerator[dict[str, str]]:
    status_key: str = f"status:{thread_id}:{message_id}"
    channel: str = f"channel:{thread_id}:{message_id}"
    with tracer.start_as_current_span("chat.stream_data") as span:
        span.set_attribute("thread_id", thread_id)
        span.set_attribute("message_id", message_id)
        span.set_attribute("start_index", start)
        span.set_attribute("status_key", status_key)
        span.set_attribute("channel", channel)

        async for data in _stream_existing_data(
            request, thread_id, message_id, start, cache_service
        ):
            yield data

        status: str | None = await cache_service.get_data(status_key)
        span.set_attribute("status_after_replay", status or "missing")
        if status in ("done", "error"):
            span.set_attribute("stream_terminated_by", f"cached_terminal_{status}")
            return

        pubsub: PubSub = await cache_service.subscribe(channel)
        pubsub_events: int = 0
        ping_events: int = 0
        try:
            last_ping: float = time()
            while True:
                if await request.is_disconnected():
                    span.set_attribute("pubsub_event_count", pubsub_events)
                    span.set_attribute("ping_event_count", ping_events)
                    span.set_attribute("stream_terminated_by", "client_disconnected")
                    return

                now: float = time()
                if now - last_ping >= PING_INTERVAL_SEC:
                    last_ping = now
                    event: StreamEvent = StreamEvent(id="0", event="ping", data="")
                    ping_events += 1
                    yield event.model_dump()

                msg: dict[str, str] | None = await pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=1.0
                )
                if msg is None:
                    continue

                try:
                    event = StreamEvent.model_validate_json(msg["data"])
                except ValidationError:
                    logger.warning("Invalid event from pubsub: %s", msg["data"])
                    continue

                pubsub_events += 1
                yield event.model_dump()

                if event.event in ("done", "error"):
                    span.set_attribute("pubsub_event_count", pubsub_events)
                    span.set_attribute("ping_event_count", ping_events)
                    span.set_attribute(
                        "stream_terminated_by", f"pubsub_terminal_{event.event}"
                    )
                    return
        finally:
            try:
                await cache_service.unsubscribe(pubsub, channel)
            finally:
                await pubsub.close()


@router.get("/chat/stream")
async def chat(
    request: Request,
    thread_id: str,
    message_id: str,
    redis: Annotated[Redis, Depends(get_redis)],
) -> EventSourceResponse:
    """Stream chat messages using Server-Sent Events.

    Args:
        request: FastAPI request object.
        thread_id: ID of the chat thread.
        message_id: ID of the chat message.
        redis: Redis dependency.

    Returns:
        EventSourceResponse with SSE events.

    Raises:
        HTTPException: If the chat operation fails.
    """
    cache_service = CacheService(redis)

    last_event_id: str | None = request.headers.get("last-event-id")
    with tracer.start_as_current_span("chat.stream_endpoint") as span:
        span.set_attribute("thread_id", thread_id)
        span.set_attribute("message_id", message_id)
        span.set_attribute("last_event_id", last_event_id or "")
        try:
            last: int = int(last_event_id) if last_event_id is not None else -1
        except ValueError:
            logger.warning("Invalid last-event-id header: %s", last_event_id)
            span.set_attribute("last_event_id_invalid", value=True)
            last = -1
        start: int = last + 1
        span.set_attribute("start_index", start)

        return EventSourceResponse(
            _stream_data(request, thread_id, message_id, start, cache_service)
        )


@router.get("/chats")
async def get_chats(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ChatThreadsResponse:
    """Get available chat threads.

    Args:
        db: Database session dependency.

    Returns:
        A dictionary of available chat threads.
    """
    chat_service = ChatService(db)
    threads: list[ChatThread] = await chat_service.get_chat_threads(status="active")
    return ChatThreadsResponse(
        data=[ChatThreadOut.model_validate(thread) for thread in threads]
    )


@router.get("/chats/{thread_id}")
async def get_chat_details(
    thread_id: str,
    agent: Annotated[ChatAgent, Depends(get_agent)],
) -> ChatThreadDetailResponse:
    """Get details of a specific chat thread.

    Args:
        thread_id: ID of the chat thread.
        agent: Chat agent dependency.

    Returns:
        Details of the specified chat thread.
    """
    return ChatThreadDetailResponse.model_validate(
        {"data": await agent.aget_chat_history(thread_id)}
    )
