import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
VOICE_DIR = DATA_DIR / "voice"
TTS_DIR = DATA_DIR / "tts"

MEMORY_FILE = DATA_DIR / "memory.json"
VOICE_MODE_FILE = DATA_DIR / "voice_mode.json"
PENDING_ACTION_FILE = DATA_DIR / "pending_action.json"

BOT_TOKEN = os.getenv("BOT_TOKEN")
ALLOWED_USER_ID = os.getenv("ALLOWED_USER_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")
OPENAI_TRANSCRIBE_MODEL = os.getenv("OPENAI_TRANSCRIBE_MODEL", "gpt-4o-mini-transcribe")
OPENAI_TTS_MODEL = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
OPENAI_TTS_VOICE = os.getenv("OPENAI_TTS_VOICE", "marin")
OPENAI_ROUTER_MODEL = os.getenv("OPENAI_ROUTER_MODEL", OPENAI_MODEL)

WIN_AGENT_URL = os.getenv("WIN_AGENT_URL")
WIN_AGENT_TOKEN = os.getenv("WIN_AGENT_TOKEN")

MAX_HISTORY_MESSAGES = 12
MAX_TEXT_REPLY_CHARS = 4000
MAX_TTS_CHARS = 1200

SYSTEM_PROMPT = """
Ты — умный Telegram-бот Артёма.

Отвечай по-русски, понятно, по делу.
Если вопрос технический — объясняй простыми шагами.
Если можно ответить кратко — отвечай кратко.
Если нужен план или инструкция — структурируй.
Учитывай предыдущие сообщения в переписке.
Не выдумывай факты.
Если не уверена — так и скажи.
""".strip()

INTENT_ROUTER_PROMPT = """
Ты анализируешь одно пользовательское сообщение для Telegram-бота.
Твоя задача — определить, это обычный чат или действие для выполнения.

Верни СТРОГО JSON без markdown и без пояснений.

Формат:
{
  "kind": "chat" | "action",
  "action": "chat" | "ping" | "ip" | "search" | "server" | "uptime" | "disk" | "ram" | "top" | "services" | "docker" | "nginx" | "logs" | "net" | "whoami" | "clear" | "voice_on" | "voice_off" | "reboot" | "win_status" | "win_screenshot" | "win_camera" | "win_lock" | "win_logout" | "win_shutdown" | "win_reboot" | "win_unlock_screen" | "win_open_url",
  "args": {
    "query": "",
    "url": ""
  },
  "confidence": 0.0
}

Правила:
1. Если это обычный вопрос, просьба объяснить, поговорить, обсудить или помочь — kind="chat", action="chat".
2. Если пользователь хочет выполнить действие на сервере или Windows ПК — kind="action".
3. Для search клади текст запроса в args.query.
4. Для win_open_url клади ссылку в args.url.
5. Не придумывай url, если его нет.
6. Если не уверена — выбирай chat.
7. Никакого текста кроме JSON.
""".strip()


def validate_config() -> None:
    missing = []

    if not BOT_TOKEN:
        missing.append("BOT_TOKEN")
    if not ALLOWED_USER_ID:
        missing.append("ALLOWED_USER_ID")
    if not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")

    if missing:
        raise RuntimeError(f"Missing required env vars: {', '.join(missing)}")


def validate_windows_agent_config() -> None:
    missing = []

    if not WIN_AGENT_URL:
        missing.append("WIN_AGENT_URL")
    if not WIN_AGENT_TOKEN:
        missing.append("WIN_AGENT_TOKEN")

    if missing:
        raise RuntimeError(f"Missing Windows agent env vars: {', '.join(missing)}")


def get_allowed_user_id() -> int:
    return int(ALLOWED_USER_ID)