import io

from telegram import Update
from telegram.ext import ContextTypes

from app.security.auth import is_allowed
from app.services.action_service import (
    cancel_pending_action_text,
    confirm_pending_action_by_code,
    execute_action,
    is_confirmation_required,
    request_action_confirmation,
)


async def deny_access(update: Update) -> None:
    if update.message:
        await update.message.reply_text("Доступ запрещён.")


async def send_action_result(update: Update, result: dict) -> None:
    if not update.message:
        return

    result_type = result.get("type")

    if result_type == "photo":
        image_bytes = result.get("bytes")
        filename = result.get("filename", "image.png")
        caption = result.get("caption", "")

        if not image_bytes:
            await update.message.reply_text("Не получила картинку от действия.")
            return

        bio = io.BytesIO(image_bytes)
        bio.name = filename
        bio.seek(0)

        await update.message.reply_photo(photo=bio, caption=caption)
        return

    text = result.get("text", "Готово.")
    await update.message.reply_text(text)


async def _run_named_action(
    update: Update,
    action_name: str,
    args: dict | None = None,
    *,
    ask_confirmation: bool = False,
) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    if ask_confirmation or is_confirmation_required(action_name):
        text = request_action_confirmation(action_name, args)
        await update.message.reply_text(text)
        return

    result = execute_action(action_name, args)
    await send_action_result(update, result)


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
        "/reboot — перезагрузка Linux сервера через подтверждение\n"
        "/clear — очистить память диалога\n"
        "/voice_on — включить голосовые ответы\n"
        "/voice_off — выключить голосовые ответы\n\n"
        "Windows agent:\n"
        "/win_status — статус Windows-агента\n"
        "/win_lock — заблокировать экран Windows\n"
        "/win_unlock_screen — попытаться снять блокировку экрана\n"
        "/win_logout — выйти из текущей сессии Windows\n"
        "/win_shutdown — выключить Windows ПК\n"
        "/win_reboot — перезагрузить ПК\n"
        "/win_screenshot — сделать скриншот Windows\n"
        "/win_camera — фото с веб-камеры Windows\n"
        "/win_open_url URL — открыть ссылку в браузере Windows\n"
        "/confirm CODE — подтвердить опасное действие\n"
        "/cancel_action — отменить опасное действие\n\n"
        "Также можно писать обычные сообщения и присылать голосовухи человеческим языком."
    )
    await update.message.reply_text(text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await start(update, context)


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _run_named_action(update, "ping")


async def ip_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _run_named_action(update, "ip")


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = " ".join(context.args).strip()
    await _run_named_action(update, "search", {"query": query})


async def uptime_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _run_named_action(update, "uptime")


async def disk_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _run_named_action(update, "disk")


async def ram_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _run_named_action(update, "ram")


async def server_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _run_named_action(update, "server")


async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _run_named_action(update, "top")


async def services_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _run_named_action(update, "services")


async def docker_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _run_named_action(update, "docker")


async def nginx_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _run_named_action(update, "nginx")


async def logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _run_named_action(update, "logs")


async def net_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _run_named_action(update, "net")


async def whoami_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _run_named_action(update, "whoami")


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _run_named_action(update, "clear")


async def voice_on_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _run_named_action(update, "voice_on")


async def voice_off_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _run_named_action(update, "voice_off")


async def reboot_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _run_named_action(update, "reboot", ask_confirmation=True)


async def win_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _run_named_action(update, "win_status")


async def win_screenshot_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _run_named_action(update, "win_screenshot")


async def win_camera_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _run_named_action(update, "win_camera")


async def win_open_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    url = " ".join(context.args).strip()
    await _run_named_action(update, "win_open_url", {"url": url})


async def win_unlock_screen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _run_named_action(update, "win_unlock_screen", ask_confirmation=True)


async def win_lock_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _run_named_action(update, "win_lock", ask_confirmation=True)


async def win_logout_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _run_named_action(update, "win_logout", ask_confirmation=True)


async def win_shutdown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _run_named_action(update, "win_shutdown", ask_confirmation=True)


async def win_reboot_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _run_named_action(update, "win_reboot", ask_confirmation=True)


async def confirm_code_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    code = " ".join(context.args).strip()
    if not code:
        await update.message.reply_text("Напиши так: /confirm 1234")
        return

    result = confirm_pending_action_by_code(code)
    await send_action_result(update, result)


async def cancel_pending_action_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    text = cancel_pending_action_text()
    await update.message.reply_text(text)