from datetime import UTC, datetime

from stock_analysis.schemas.chat import (
    ChatMessageOut,
    ChatStartIn,
    ChatStartOut,
    ChatThreadDetailResponse,
    ChatThreadIn,
    ChatThreadOut,
    ChatThreadsResponse,
    StreamEvent,
)


def test_chat_thread_in_validation() -> None:
    payload: dict[str, str] = {
        "thread_id": "thread_001",
        "title": "Test Thread",
        "status": "active",
    }
    chat_thread: ChatThreadIn = ChatThreadIn.model_validate(payload)

    assert chat_thread.thread_id == "thread_001"
    assert chat_thread.title == "Test Thread"
    assert chat_thread.status == "active"


def test_chat_thread_out() -> None:
    now: datetime = datetime.now(UTC)
    chat_thread_out = ChatThreadOut(
        thread_id="thread_001",
        title="Test Thread",
        status="active",
        created_at=now,
        updated_at=now,
    )

    assert chat_thread_out.thread_id == "thread_001"
    assert chat_thread_out.created_at == now
    assert chat_thread_out.updated_at == now


def test_chat_start_in_validation() -> None:
    payload: dict[str, str] = {
        "thread_id": "thread_001",
        "message_id": "msg_001",
        "message": "你好",
        "locale": "zh_CN",
        "stock_code": "000001",
    }
    chat_start: ChatStartIn = ChatStartIn.model_validate(payload)

    assert chat_start.thread_id == "thread_001"
    assert chat_start.message_id == "msg_001"
    assert chat_start.message == "你好"
    assert chat_start.stock_code == "000001"


def test_chat_start_in_without_stock_code() -> None:
    payload: dict[str, str] = {
        "thread_id": "thread_001",
        "message_id": "msg_001",
        "message": "你好",
        "locale": "zh_CN",
    }
    chat_start: ChatStartIn = ChatStartIn.model_validate(payload)

    assert chat_start.thread_id == "thread_001"
    assert chat_start.stock_code is None


def test_chat_start_out() -> None:
    chat_start_out = ChatStartOut(stream_url="http://localhost:8000/stream")

    assert chat_start_out.stream_url == "http://localhost:8000/stream"


def test_stream_event() -> None:
    event: StreamEvent = StreamEvent(id="1", event="token", data="hello")

    assert event.id == "1"
    assert event.event == "token"
    assert event.data == "hello"


def test_stream_event_done() -> None:
    event: StreamEvent = StreamEvent(id="2", event="done", data="")

    assert event.event == "done"


def test_stream_event_error() -> None:
    event: StreamEvent = StreamEvent(id="3", event="error", data="Error message")

    assert event.event == "error"
    assert event.data == "Error message"


def test_chat_threads_response() -> None:
    now: datetime = datetime.now(UTC)
    data: list[ChatThreadOut] = [
        ChatThreadOut(
            thread_id="thread_001",
            title="Thread 1",
            status="active",
            created_at=now,
            updated_at=now,
        ),
        ChatThreadOut(
            thread_id="thread_002",
            title="Thread 2",
            status="active",
            created_at=now,
            updated_at=now,
        ),
        ChatThreadOut(
            thread_id="thread_003",
            title="Thread 3",
            status="active",
            created_at=now,
            updated_at=now,
        ),
    ]
    response: ChatThreadsResponse = ChatThreadsResponse(data=data)

    assert len(response.data) == len(data)
    assert response.data[0].thread_id == "thread_001"


def test_chat_message_out() -> None:
    message: ChatMessageOut = ChatMessageOut(role="human", content="这是一条测试消息")

    assert message.role == "human"
    assert message.content == "这是一条测试消息"


def test_chat_message_out_ai_response() -> None:
    message: ChatMessageOut = ChatMessageOut(role="ai", content="这是AI的回应")

    assert message.role == "ai"
    assert message.content == "这是AI的回应"


def test_chat_thread_detail_response() -> None:
    messages: list[ChatMessageOut] = [
        ChatMessageOut(role="human", content="Hello"),
        ChatMessageOut(role="ai", content="Hello, how can I assist you?"),
        ChatMessageOut(role="human", content="Please analyze 000001"),
    ]
    response: ChatThreadDetailResponse = ChatThreadDetailResponse(data=messages)

    assert len(response.data) == len(messages)
    assert response.data[0].role == "human"
    assert response.data[1].role == "ai"
