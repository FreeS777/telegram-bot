import json
import logging
from app.config import (
    DATA_DIR,
    VOICE_DIR,
    TTS_DIR,
    MEMORY_FILE,
    VOICE_MODE_FILE,
    MAX_HISTORY_MESSAGES,
)

logger = logging.getLogger(__name__)


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    VOICE_DIR.mkdir(parents=True, exist_ok=True)
    TTS_DIR.mkdir(parents=True, exist_ok=True)

    if not MEMORY_FILE.exists():
        MEMORY_FILE.write_text(
            json.dumps({"messages": []}, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    if not VOICE_MODE_FILE.exists():
        VOICE_MODE_FILE.write_text(
            json.dumps({"enabled": False}, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )


def load_memory() -> list[dict]:
    ensure_dirs()
    try:
        data = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
        messages = data.get("messages", [])
        if isinstance(messages, list):
            return messages
        return []
    except Exception:
        logger.exception("Failed to load memory")
        return []


def save_memory(messages: list[dict]) -> None:
    ensure_dirs()
    try:
        MEMORY_FILE.write_text(
            json.dumps({"messages": messages}, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    except Exception:
        logger.exception("Failed to save memory")


def add_to_memory(role: str, text: str) -> None:
    messages = load_memory()
    messages.append({"role": role, "text": text})
    messages = messages[-MAX_HISTORY_MESSAGES:]
    save_memory(messages)


def clear_memory() -> None:
    save_memory([])


def get_voice_mode() -> bool:
    ensure_dirs()
    try:
        data = json.loads(VOICE_MODE_FILE.read_text(encoding="utf-8"))
        return bool(data.get("enabled", False))
    except Exception:
        logger.exception("Failed to read voice mode")
        return False


def set_voice_mode(enabled: bool) -> None:
    ensure_dirs()
    try:
        VOICE_MODE_FILE.write_text(
            json.dumps({"enabled": enabled}, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    except Exception:
        logger.exception("Failed to write voice mode")
