from pathlib import Path

import pytest

from stock_analysis.agent.prompt import PromptManager


@pytest.fixture
def prompt_manager() -> PromptManager:
    prompts_dir: Path = Path(__file__).parents[3] / "configs" / "prompts"
    return PromptManager(prompts_dir)


def test_load_prompts(prompt_manager: PromptManager) -> None:
    available_prompts: list[str] = prompt_manager.get_available_prompts()
    assert len(available_prompts) > 0

    assert "chat" in available_prompts
    assert "user" in available_prompts
    assert "grade" in available_prompts
    assert "rewrite" in available_prompts


def test_get_prompt(prompt_manager: PromptManager) -> None:
    prompt: str = prompt_manager.get_prompt("chat", "en-US")
    assert isinstance(prompt, str)
    assert len(prompt) > 0
    assert "Role" in prompt or "role" in prompt

    with pytest.raises(KeyError):
        prompt_manager.get_prompt("nonexistent", "en-US")

    with pytest.raises(KeyError):
        prompt_manager.get_prompt("chat", "en")


def test_get_locales(prompt_manager: PromptManager) -> None:
    """Test getting available locales for a prompt."""
    locales: list[str] = prompt_manager.get_available_locales("chat")
    assert "en-US" in locales
    assert "zh-CN" in locales

    with pytest.raises(KeyError):
        prompt_manager.get_available_locales("nonexistent")
