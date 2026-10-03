"""Dynamic Prompt Manager with Hot-Reload for OWLEXIA Legal AI Agent.

Allows users to directly edit Markdown prompt files in the `prompts/` directory
without needing to restart the server. Changes take effect on the very next query.
"""
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger("owlexia.prompts")

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
SYSTEM_PROMPT_FILE = PROMPTS_DIR / "system_prompt.md"

DEFAULT_SYSTEM_PROMPT = """# OWLEXIA MASTER SYSTEM PROMPT
<identity>
Anda adalah OWLEXIA, sistem intelijen kecerdasan artifisial spesialis Hukum Positif Republik Indonesia.
</identity>
"""


class PromptManager:
    """Manages loading, hot-reloading, and updating system prompts."""

    _default_instance: Optional["PromptManager"] = None

    @classmethod
    def get_instance(cls) -> "PromptManager":
        if cls._default_instance is None:
            cls._default_instance = cls()
        return cls._default_instance

    def __init__(self, prompt_file: Optional[Path] = None):
        self.prompt_file = prompt_file or SYSTEM_PROMPT_FILE
        self._cached_content: str = ""
        self._last_mtime: float = 0.0
        self._load_if_modified()

    def _load_if_modified(self) -> str:
        """Checks file mtime and reloads if changed."""
        if not self.prompt_file.exists():
            # If prompt file does not exist, initialize it
            try:
                self.prompt_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.prompt_file, "w", encoding="utf-8") as f:
                    f.write(DEFAULT_SYSTEM_PROMPT)
                self._cached_content = DEFAULT_SYSTEM_PROMPT
                self._last_mtime = self.prompt_file.stat().st_mtime
            except Exception as e:
                logger.error(f"Failed to create default prompt file: {e}")
                return DEFAULT_SYSTEM_PROMPT
            return self._cached_content

        try:
            current_mtime = self.prompt_file.stat().st_mtime
            if current_mtime > self._last_mtime:
                with open(self.prompt_file, "r", encoding="utf-8") as f:
                    self._cached_content = f.read()
                self._last_mtime = current_mtime
                logger.info(f"Hot-reloaded system prompt from {self.prompt_file} (size: {len(self._cached_content)} chars)")
        except Exception as e:
            logger.error(f"Error reading prompt file: {e}")
            if not self._cached_content:
                self._cached_content = DEFAULT_SYSTEM_PROMPT

        return self._cached_content

    def get_system_prompt(self) -> str:
        """Returns the latest active system prompt."""
        return self._load_if_modified()

    def update_system_prompt(self, new_content: str) -> bool:
        """Overwrites the system prompt file on disk."""
        try:
            self.prompt_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.prompt_file, "w", encoding="utf-8") as f:
                f.write(new_content)
            self._cached_content = new_content
            self._last_mtime = self.prompt_file.stat().st_mtime
            return True
        except Exception as e:
            logger.error(f"Failed to update system prompt file: {e}")
            return False

    def get_metadata(self) -> Dict[str, Any]:
        """Returns metadata about the active prompt file."""
        self._load_if_modified()
        content = self._cached_content
        words = len(content.split())
        est_tokens = int(words * 1.3)
        return {
            "file_path": str(self.prompt_file),
            "file_exists": self.prompt_file.exists(),
            "character_count": len(content),
            "word_count": words,
            "estimated_tokens": est_tokens,
            "last_modified": self._last_mtime
        }
