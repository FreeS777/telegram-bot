import json
import logging
import time
from pathlib import Path
from typing import Any

from app.config import (
    DATA_DIR,
    MEMORY_FILE,
    VOICE_DIR,
    TTS_DIR,
    VOICE_MODE_FILE,
    PENDING_ACTION_FILE,
    MAX_HISTORY_MESSAGES,
)

logger = logging.getLogger(__name__)


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    VOICE_DIR.mkdir(parents=True, exist_ok=True)
    TTS_DIR.mkdir(parents=True, exist_ok=True)

    _ensure_json_file(MEMORY_FILE, {"messages": []})
    _ensure_json_file(VOICE_MODE_FILE, {"enabled": False})
    _ensure_json_file(PENDING_ACTION_FILE, {"pending": None})


def _ensure_json_file(path: Path, default_data: dict[str, Any]) -> None:
    if not path.exists():
        path.write_text(
            json.dumps(default_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def _read_json(path: Path, default_data: dict[str, Any]) -> dict[str, Any]:
    ensure_dirs()
    try:
        raw = path.read_text(encoding="utf-8").strip()
        if not raw:
            return default_data
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
        return default_data
    except Exception:
        logger.exception("Failed to read json from %s", path)
        return default_data


def _write_json(path: Path, data: dict[str, Any]) -> None:
    ensure_dirs()
    try:
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        logger.exception("Failed to write json to %s", path)


def load_memory() -> list[dict]:
    data = _read_json(MEMORY_FILE, {"messages": []})
    messages = data.get("messages", [])
    if isinstance(messages, list):
        return messages
    return []


def save_memory(messages: list[dict]) -> None:
    _write_json(MEMORY_FILE, {"messages": messages})


def add_to_memory(role: str, text: str) -> None:
    messages = load_memory()
    messages.append({"role": role, "text": text})
    messages = messages[-MAX_HISTORY_MESSAGES:]
    save_memory(messages)


def clear_memory() -> None:
    save_memory([])


def get_voice_mode() -> bool:
    data = _read_json(VOICE_MODE_FILE, {"enabled": False})
    return bool(data.get("enabled", False))


def set_voice_mode(enabled: bool) -> None:
    _write_json(VOICE_MODE_FILE, {"enabled": enabled})


def get_pending_action() -> dict | None:
    data = _read_json(PENDING_ACTION_FILE, {"pending": None})
    pending = data.get("pending")
    if isinstance(pending, dict):
        return pending
    return None


def set_pending_action(action_name: str, args: dict | None, code: str) -> None:
    payload = {
        "pending": {
            "action_name": action_name,
            "args": args or {},
            "code": code,
            "created_at": int(time.time()),
        }
    }
    _write_json(PENDING_ACTION_FILE, payload)


def clear_pending_action() -> None:
    _write_json(PENDING_ACTION_FILE, {"pending": None})