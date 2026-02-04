from stock_analysis.models.chat import ChatThread


def test_chat_thread_repr() -> None:
    chat_thread = ChatThread(
        thread_id="thread_001",
        title="Test Thread",
        status="active",
    )

    result: str = repr(chat_thread)
    assert "ChatThread(" in result
    assert "thread_001" in result
    assert "Test Thread" in result
    assert "active" in result
