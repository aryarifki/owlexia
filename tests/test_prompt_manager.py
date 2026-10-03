"""Unit tests for PromptManager and dynamic system prompt loading."""
import pytest
from pathlib import Path
from engine.prompt_manager import PromptManager


def test_prompt_manager_load():
    pm = PromptManager()
    prompt = pm.get_system_prompt()
    assert len(prompt) > 0
    assert "OWLEXIA" in prompt
    assert "<identity>" in prompt


def test_prompt_manager_metadata():
    pm = PromptManager()
    meta = pm.get_metadata()
    assert meta["file_exists"] is True
    assert meta["character_count"] > 100
    assert meta["estimated_tokens"] > 50


def test_prompt_manager_hot_reload(tmp_path):
    test_file = tmp_path / "test_prompt.md"
    test_file.write_text("<identity>Initial Test Prompt</identity>", encoding="utf-8")
    
    pm = PromptManager(prompt_file=test_file)
    assert "Initial Test Prompt" in pm.get_system_prompt()

    # Modify file directly on disk
    test_file.write_text("<identity>Updated Hot Reloaded Prompt</identity>", encoding="utf-8")
    # Touch mtime forward
    import os, time
    os.utime(test_file, (time.time() + 2, time.time() + 2))

    # Should hot reload automatically
    assert "Updated Hot Reloaded Prompt" in pm.get_system_prompt()
