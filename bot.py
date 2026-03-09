import os
import json
import html
import logging
import subprocess
from pathlib import Path
from urllib.parse import quote_plus

import requests
from dotenv import load_dotenv
from openai import OpenAI
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ALLOWED_USER_ID = os.getenv("ALLOWED_USER_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")
OPENAI_TRANSCRIBE_MODEL = os.getenv("OPENAI_TRANSCRIBE_MODEL", "gpt-4o-mini-transcribe")
OPENAI_TTS_MODEL = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
OPENAI_TTS_VOICE = os.getenv("OPENAI_TTS_VOICE", "marin")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN not found in .env")

if not ALLOWED_USER_ID:
    raise RuntimeError("ALLOWED_USER_ID not found in .env")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not found in .env")

ALLOWED_USER_ID = int(ALLOWED_USER_ID)

client = OpenAI(api_key=OPENAI_API_KEY)

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
Ты — умный Telegram-бот Артёма.
Отвечай по-русски, понятно, по делу.
Если вопрос технический — объясняй простыми шагами.
Если можно ответить кратко — отвечай кратко.
Если нужен plan или инструкция — структурируй.
Учитывай предыдущие сообщения в переписке.
Не выдумывай факты. Если не уверена — так и скажи.
"""

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MEMORY_FILE = DATA_DIR / "memory.json"
VOICE_DIR = DATA_DIR / "voice"
TTS_DIR = DATA_DIR / "tts"
MAX_HISTORY_MESSAGES = 12
MAX_TTS_CHARS = 1200  # чтобы не слать слишком длинный текст в TTS


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    VOICE_DIR.mkdir(parents=True, exist_ok=True)
    TTS_DIR.mkdir(parents=True, exist_ok=True)
    if not MEMORY_FILE.exists():
        MEMORY_FILE.write_text(
            json.dumps({"messages": []}, ensure_ascii=False, indent=2),
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


def build_openai_input(user_text: str) -> list[dict]:
    memory = load_memory()

    input_items = [
        {
            "role": "system",
            "content": [
                {"type": "input_text", "text": SYSTEM_PROMPT}
            ],
        }
    ]

    for item in memory:
        role = item.get("role")
        text = item.get("text", "")
        if role not in {"user", "assistant"} or not text:
            continue

        if role == "user":
            content = [{"type": "input_text", "text": text}]
        else:
            content = [{"type": "output_text", "text": text}]

        input_items.append(
            {
                "role": role,
                "content": content,
            }
        )

    input_items.append(
        {
            "role": "user",
            "content": [
                {"type": "input_text", "text": user_text}
            ],
        }
    )

    return input_items


def is_allowed(update: Update) -> bool:
    user = update.effective_user
    return bool(user and user.id == ALLOWED_USER_ID)


async def deny_access(update: Update) -> None:
    if update.message:
        await update.message.reply_text("Доступ запрещён.")


def safe_html(text: str) -> str:
    return html.escape(text)


def truncate(text: str, limit: int = 3500) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\n\n...обрезано..."


def truncate_for_tts(text: str, limit: int = MAX_TTS_CHARS) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text

    cut = text[:limit]
    last_dot = max(cut.rfind("."), cut.rfind("!"), cut.rfind("?"), cut.rfind("\n"))
    if last_dot > 300:
        cut = cut[: last_dot + 1]

    return cut.strip() + " ..."


def run_command(command: str, timeout: int = 15) -> str:
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        output = result.stdout.strip() or result.stderr.strip()
        return output if output else "Команда выполнена, но ничего не вернула."
    except subprocess.TimeoutExpired:
        return "Команда выполнялась слишком долго."
    except Exception as e:
        logger.exception("Command failed")
        return f"Ошибка выполнения команды: {e}"


def ask_openai(user_text: str) -> str:
    try:
        response = client.responses.create(
            model=OPENAI_MODEL,
            input=build_openai_input(user_text),
        )

        if hasattr(response, "output_text") and response.output_text:
            return response.output_text.strip()

        return str(response)

    except Exception as e:
        logger.exception("OpenAI request failed")
        return f"Ошибка OpenAI API: {e}"


def transcribe_audio_file(file_path: Path) -> str:
    try:
        with open(file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model=OPENAI_TRANSCRIBE_MODEL,
                file=audio_file,
            )

        text = getattr(transcript, "text", None)
        if text and text.strip():
            return text.strip()

        return ""
    except Exception as e:
        logger.exception("Audio transcription failed")
        return f"Ошибка распознавания аудио: {e}"


def synthesize_speech_to_file(text: str, output_path: Path) -> str | None:
    """
    Генерирует голосовой ответ в формате opus и сохраняет в файл.
    Возвращает None при успехе или строку ошибки.
    """
    try:
        text_for_tts = truncate_for_tts(text)

        response = client.audio.speech.create(
            model=OPENAI_TTS_MODEL,
            voice=OPENAI_TTS_VOICE,
            input=text_for_tts,
            response_format="opus",
        )

        audio_bytes = response.read()

        output_path.write_bytes(audio_bytes)
        return None
    except Exception as e:
        logger.exception("TTS generation failed")
        return f"Ошибка генерации голоса: {e}"


async def send_voice_reply(update: Update, text: str) -> None:
    """
    Генерирует и отправляет голосовой ответ.
    """
    ensure_dirs()

    if not update.message:
        return

    tts_file = TTS_DIR / f"reply_{update.message.message_id}.opus"

    error = synthesize_speech_to_file(text, tts_file)
    if error:
        await update.message.reply_text(error)
        return

    try:
        with open(tts_file, "rb") as f:
            await update.message.reply_voice(voice=f)
    except Exception as e:
        logger.exception("Failed to send voice reply")
        await update.message.reply_text(f"Не смогла отправить голосовой ответ: {e}")
    finally:
        try:
            tts_file.unlink(missing_ok=True)
        except Exception:
            logger.exception("Failed to delete temporary TTS file")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    text = (
        "Бот запущен и работает.\n\n"
        "Команды:\n"
        "/help — список команд\n"
        "/ping — проверка\n"
        "/ip — внешний IP сервера\n"
        "/search текст — поиск в Google\n"
        "/server — общая сводка\n"
        "/uptime — время работы\n"
        "/disk — место на диске\n"
        "/ram — память\n"
        "/top — топ процессов\n"
        "/services — важные сервисы\n"
        "/docker — контейнеры Docker\n"
        "/nginx — статус Nginx\n"
        "/logs — логи бота\n"
        "/net — сеть\n"
        "/whoami — пользователь и хост\n"
        "/reboot — перезагрузка через 1 минуту\n"
        "/cancel_reboot — отменить перезагрузку\n"
        "/clear — очистить память диалога\n"
        "/voice_on — включить голосовые ответы\n"
        "/voice_off — выключить голосовые ответы\n\n"
        "Можно писать обычные сообщения и присылать голосовухи."
    )
    await update.message.reply_text(text)


VOICE_MODE_FILE = DATA_DIR / "voice_mode.json"


def ensure_voice_mode_file() -> None:
    ensure_dirs()
    if not VOICE_MODE_FILE.exists():
        VOICE_MODE_FILE.write_text(
            json.dumps({"enabled": False}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def get_voice_mode() -> bool:
    ensure_voice_mode_file()
    try:
        data = json.loads(VOICE_MODE_FILE.read_text(encoding="utf-8"))
        return bool(data.get("enabled", False))
    except Exception:
        logger.exception("Failed to read voice mode")
        return False


def set_voice_mode(enabled: bool) -> None:
    ensure_voice_mode_file()
    try:
        VOICE_MODE_FILE.write_text(
            json.dumps({"enabled": enabled}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        logger.exception("Failed to write voice mode")


async def voice_on_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return
    set_voice_mode(True)
    await update.message.reply_text("Голосовые ответы включены.")


async def voice_off_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return
    set_voice_mode(False)
    await update.message.reply_text("Голосовые ответы выключены.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    text = (
        "Доступные команды:\n\n"
        "/ping — проверка бота\n"
        "/ip — внешний IP\n"
        "/search текст — поиск в Google\n"
        "/server — hostname / uptime / load / RAM / disk\n"
        "/uptime — сколько сервер работает\n"
        "/disk — место на диске\n"
        "/ram — память\n"
        "/top — топ процессов по CPU\n"
        "/services — systemd-статус важных сервисов\n"
        "/docker — docker ps\n"
        "/nginx — статус nginx\n"
        "/logs — последние логи бота\n"
        "/net — IP и сетевые интерфейсы\n"
        "/whoami — текущий пользователь\n"
        "/reboot — перезагрузка через 1 минуту\n"
        "/cancel_reboot — отмена перезагрузки\n"
        "/clear — очистить память диалога\n"
        "/voice_on — включить голосовые ответы\n"
        "/voice_off — выключить голосовые ответы\n\n"
        "Также можно писать обычный текст и присылать voice message."
    )
    await update.message.reply_text(text)


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    clear_memory()
    await update.message.reply_text("Память диалога очищена.")


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return
    await update.message.reply_text("Я живая. Сервер не уснул 😎")


async def ip_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    try:
        response = requests.get("https://api.ipify.org", timeout=10)
        response.raise_for_status()
        ip = response.text.strip()
        await update.message.reply_text(f"Внешний IP сервера: {ip}")
    except Exception as e:
        logger.exception("Failed to get IP")
        await update.message.reply_text(f"Не смогла получить IP: {e}")


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    if not context.args:
        await update.message.reply_text("Напиши так: /search react router dom")
        return

    query = " ".join(context.args).strip()
    url = f"https://www.google.com/search?q={quote_plus(query)}"
    await update.message.reply_text(url)


async def uptime_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return
    output = run_command("uptime -p")
    await update.message.reply_text(f"Uptime: {output}")


async def disk_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return
    output = truncate(run_command("df -h /"))
    text = f"<b>Диск /</b>\n<pre>{safe_html(output)}</pre>"
    await update.message.reply_text(text, parse_mode="HTML")


async def ram_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return
    output = truncate(run_command("free -h"))
    text = f"<b>Память</b>\n<pre>{safe_html(output)}</pre>"
    await update.message.reply_text(text, parse_mode="HTML")


async def server_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    hostname = run_command("hostname")
    uptime = run_command("uptime -p")
    loadavg = run_command("cat /proc/loadavg")
    mem = truncate(run_command("free -h"))
    disk = truncate(run_command("df -h /"))

    text = (
        f"<b>Сервер: {safe_html(hostname)}</b>\n\n"
        f"<b>Uptime</b>\n<pre>{safe_html(uptime)}</pre>\n"
        f"<b>Load Average</b>\n<pre>{safe_html(loadavg)}</pre>\n"
        f"<b>RAM</b>\n<pre>{safe_html(mem)}</pre>\n"
        f"<b>Disk /</b>\n<pre>{safe_html(disk)}</pre>"
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return
    cmd = "ps -eo pid,ppid,cmd,%mem,%cpu --sort=-%cpu | head -n 12"
    output = truncate(run_command(cmd))
    text = f"<b>Топ процессов по CPU</b>\n<pre>{safe_html(output)}</pre>"
    await update.message.reply_text(text, parse_mode="HTML")


async def services_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    bot_status = run_command("systemctl is-active telegram-bot")
    nginx_status = run_command("systemctl is-active nginx")
    docker_status = run_command("systemctl is-active docker")

    text = (
        "<b>Статус сервисов</b>\n\n"
        f"<b>telegram-bot</b>\n<pre>{safe_html(bot_status)}</pre>\n"
        f"<b>nginx</b>\n<pre>{safe_html(nginx_status)}</pre>\n"
        f"<b>docker</b>\n<pre>{safe_html(docker_status)}</pre>"
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def docker_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return
    output = truncate(run_command("docker ps --format 'table {{.Names}}\\t{{.Image}}\\t{{.Status}}'"))
    text = f"<b>Docker containers</b>\n<pre>{safe_html(output)}</pre>"
    await update.message.reply_text(text, parse_mode="HTML")


async def nginx_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return
    output = truncate(run_command("systemctl status nginx --no-pager -l", timeout=20))
    text = f"<b>Nginx status</b>\n<pre>{safe_html(output)}</pre>"
    await update.message.reply_text(text, parse_mode="HTML")


async def logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return
    output = truncate(run_command("journalctl -u telegram-bot -n 30 --no-pager", timeout=20))
    text = f"<b>Последние логи telegram-bot</b>\n<pre>{safe_html(output)}</pre>"
    await update.message.reply_text(text, parse_mode="HTML")


async def net_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    ip_brief = truncate(run_command("ip -br a"))
    routes = truncate(run_command("ip route"))
    external_ip = "не удалось получить"
    try:
        response = requests.get("https://api.ipify.org", timeout=10)
        response.raise_for_status()
        external_ip = response.text.strip()
    except Exception:
        pass

    text = (
        f"<b>Внешний IP</b>\n<pre>{safe_html(external_ip)}</pre>\n"
        f"<b>IP интерфейсы</b>\n<pre>{safe_html(ip_brief)}</pre>\n"
        f"<b>Маршруты</b>\n<pre>{safe_html(routes)}</pre>"
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def whoami_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    user = run_command("whoami")
    hostname = run_command("hostname")
    pwd = run_command("pwd")

    text = (
        f"<b>Пользователь</b>\n<pre>{safe_html(user)}</pre>\n"
        f"<b>Хост</b>\n<pre>{safe_html(hostname)}</pre>\n"
        f"<b>Текущая директория</b>\n<pre>{safe_html(pwd)}</pre>"
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def reboot_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    result = run_command("sudo shutdown -r +1 'Reboot requested from Telegram bot'")
    text = (
        "Перезагрузка сервера запланирована через 1 минуту.\n"
        "Если передумал — жми /cancel_reboot\n\n"
        f"<pre>{safe_html(result)}</pre>"
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def cancel_reboot_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    result = run_command("sudo shutdown -c")
    text = f"Попыталась отменить перезагрузку.\n\n<pre>{safe_html(result)}</pre>"
    await update.message.reply_text(text, parse_mode="HTML")


async def chat_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    if not update.message or not update.message.text:
        return

    user_text = update.message.text.strip()
    if not user_text:
        return

    await update.message.chat.send_action(action=ChatAction.TYPING)

    answer = ask_openai(user_text)
    answer = truncate(answer, 4000)

    add_to_memory("user", user_text)
    add_to_memory("assistant", answer)

    await update.message.reply_text(answer)

    if get_voice_mode():
        await update.message.chat.send_action(action=ChatAction.RECORD_VOICE)
        await send_voice_reply(update, answer)


async def voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    if not update.message or not update.message.voice:
        return

    ensure_dirs()
    voice = update.message.voice
    file_id = voice.file_unique_id or voice.file_id
    local_path = VOICE_DIR / f"{file_id}.ogg"

    await update.message.chat.send_action(action=ChatAction.TYPING)

    try:
        telegram_file = await voice.get_file()
        await telegram_file.download_to_drive(custom_path=str(local_path))
    except Exception as e:
        logger.exception("Failed to download voice file")
        await update.message.reply_text(f"Не смогла скачать голосовуху: {e}")
        return

    transcript_text = transcribe_audio_file(local_path)

    try:
        local_path.unlink(missing_ok=True)
    except Exception:
        logger.exception("Failed to delete temporary voice file")

    if not transcript_text:
        await update.message.reply_text("Не смогла распознать голосовуху.")
        return

    if transcript_text.startswith("Ошибка распознавания аудио:"):
        await update.message.reply_text(transcript_text)
        return

    await update.message.reply_text(f"Распознала так:\n\n{transcript_text}")

    answer = ask_openai(transcript_text)
    answer = truncate(answer, 4000)

    add_to_memory("user", transcript_text)
    add_to_memory("assistant", answer)

    await update.message.reply_text(answer)

    await update.message.chat.send_action(action=ChatAction.RECORD_VOICE)
    await send_voice_reply(update, answer)


def main() -> None:
    ensure_dirs()
    ensure_voice_mode_file()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("clear", clear_command))
    app.add_handler(CommandHandler("voice_on", voice_on_command))
    app.add_handler(CommandHandler("voice_off", voice_off_command))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("ip", ip_command))
    app.add_handler(CommandHandler("search", search))
    app.add_handler(CommandHandler("uptime", uptime_command))
    app.add_handler(CommandHandler("disk", disk_command))
    app.add_handler(CommandHandler("ram", ram_command))
    app.add_handler(CommandHandler("server", server_command))
    app.add_handler(CommandHandler("top", top_command))
    app.add_handler(CommandHandler("services", services_command))
    app.add_handler(CommandHandler("docker", docker_command))
    app.add_handler(CommandHandler("nginx", nginx_command))
    app.add_handler(CommandHandler("logs", logs_command))
    app.add_handler(CommandHandler("net", net_command))
    app.add_handler(CommandHandler("whoami", whoami_command))
    app.add_handler(CommandHandler("reboot", reboot_command))
    app.add_handler(CommandHandler("cancel_reboot", cancel_reboot_command))

    app.add_handler(MessageHandler(filters.VOICE, voice_message))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_message))

    logger.info("Bot started")
    app.run_polling()


if __name__ == "__main__":
    main()
