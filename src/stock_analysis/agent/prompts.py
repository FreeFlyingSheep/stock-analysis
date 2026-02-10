"""Prompt management for the stock analysis agent."""

from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from stock_analysis.logger import get_logger

if TYPE_CHECKING:
    import logging
    import os


logger: logging.Logger = get_logger(__name__)


class PromptManager:
    """Manager for loading and caching prompt templates from YAML files."""

    def __init__(self, prompts_dir: str | os.PathLike[str]) -> None:
        """Initialize the prompt manager.

        Args:
            prompts_dir: Directory containing prompt YAML files.
        """
        self._prompts_dir = Path(prompts_dir)
        self._cache: dict[str, dict[str, Any]] = {}
        self._load_prompts()

    def _load_prompts(self) -> None:
        """Load all YAML prompt files from the prompts directory."""
        yaml_files: list[str] = [
            "agent.yaml",
            "retrieval.yaml",
            "errors.yaml",
        ]

        for yaml_file in yaml_files:
            file_path: Path = self._prompts_dir / yaml_file
            if not file_path.exists():
                logger.warning("Prompt file not found: %s", file_path)
                continue

            try:
                with file_path.open(encoding="utf-8") as f:
                    data: dict[str, Any] = yaml.safe_load(f)
                    if "prompts" in data:
                        self._cache.update(data["prompts"])
                        logger.info(
                            "Loaded %d prompts from %s",
                            len(data["prompts"]),
                            yaml_file,
                        )
            except Exception:
                logger.exception("Failed to load prompts from %s", yaml_file)

    def get_prompt(self, prompt: str, locale: str = "en") -> str:
        """Get a prompt template by name and locale.

        Args:
            prompt: Name of the prompt template.
            locale: Language locale ("en" or "zh-CN").

        Returns:
            The prompt template content as a string.

        Raises:
            KeyError: If the prompt or locale is not found.
        """
        if prompt not in self._cache:
            msg: str = f"Prompt '{prompt}' not found in loaded prompts"
            raise KeyError(msg)

        prompt_data: dict[str, Any] = self._cache[prompt]

        if locale in prompt_data:
            content: str = prompt_data[locale]
        else:
            msg = f"Locale '{locale}' not found for prompt '{prompt}'"
            raise KeyError(msg)

        return content.strip()

    def get_available_prompts(self) -> list[str]:
        """Get a list of all available prompt names.

        Returns:
            List of prompt names.
        """
        return list(self._cache.keys())

    def get_available_locales(self, prompt: str) -> list[str]:
        """Get a list of available locales for a specific prompt.

        Args:
            prompt: Name of the prompt template.

        Returns:
            List of locale codes.

        Raises:
            KeyError: If the prompt is not found.
        """
        if prompt not in self._cache:
            msg: str = f"Prompt '{prompt}' not found in loaded prompts"
            raise KeyError(msg)

        return [
            key for key in self._cache[prompt] if key not in ("description", "metadata")
        ]
