import re

from telegram import ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes

from app.security.auth import is_allowed
from app.handlers.command_handlers import (
    deny_access,
    clear_command,
    voice_on_command,
    voice_off_command,
    ping,
    ip_command,
    uptime_command,
    disk_command,
    ram_command,
    server_command,
    top_command,
    services_command,
    docker_command,
    nginx_command,
    logs_command,
    net_command,
    whoami_command,
    win_status_command,
    win_screenshot_command,
    win_camera_command,
    win_open_url,
    win_unlock_screen,
)
from app.handlers.confirm_handlers import (
    cancel_pending_action,
    request_server_reboot_confirmation,
    request_win_lock_confirmation,
    request_win_logout_confirmation,
    request_win_shutdown_confirmation,
    request_win_reboot_confirmation,
)
from app.keyboards.menu_keyboards import (
    BTN_BACK,
    BTN_CANCEL,
    BTN_HIDE_MENU,
    BTN_MAIN_CLEAR,
    BTN_MAIN_HELP,
    BTN_MAIN_SERVER,
    BTN_MAIN_VOICE,
    BTN_MAIN_WINDOWS,
    BTN_SERVER_DISK,
    BTN_SERVER_DOCKER,
    BTN_SERVER_IP,
    BTN_SERVER_LOGS,
    BTN_SERVER_NET,
    BTN_SERVER_NGINX,
    BTN_SERVER_PING,
    BTN_SERVER_RAM,
    BTN_SERVER_REBOOT,
    BTN_SERVER_SERVICES,
    BTN_SERVER_SUMMARY,
    BTN_SERVER_TOP,
    BTN_SERVER_UPTIME,
    BTN_SERVER_WHOAMI,
    BTN_VOICE_OFF,
    BTN_VOICE_ON,
    BTN_WIN_CAMERA,
    BTN_WIN_LOCK,
    BTN_WIN_LOGOUT,
    BTN_WIN_OPEN_URL,
    BTN_WIN_REBOOT,
    BTN_WIN_SCREENSHOT,
    BTN_WIN_SHUTDOWN,
    BTN_WIN_STATUS,
    BTN_WIN_UNLOCK,
    get_cancel_keyboard,
    get_main_menu_keyboard,
    get_server_menu_keyboard,
    get_voice_menu_keyboard,
    get_windows_menu_keyboard,
)
from app.services.confirm_service import clear_pending_confirmation, has_pending_confirmation


AWAITING_WIN_URL_KEY = "awaiting_win_url"


def normalize_url(url: str) -> str:
    url = url.strip()
    if not url:
        return url

    if not re.match(r"^https?://", url, flags=re.IGNORECASE):
        url = f"https://{url}"

    return url


def is_probably_url(text: str) -> bool:
    text = text.strip()

    if " " in text:
        return False

    return bool(
        re.match(
            r"^(https?://)?([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}([/:?#][^\s]*)?$",
            text,
            flags=re.IGNORECASE,
        )
    )


def set_awaiting_win_url(context: ContextTypes.DEFAULT_TYPE, value: bool) -> None:
    context.user_data[AWAITING_WIN_URL_KEY] = value


def is_awaiting_win_url(context: ContextTypes.DEFAULT_TYPE) -> bool:
    return bool(context.user_data.get(AWAITING_WIN_URL_KEY, False))


def clear_awaiting_states(context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop(AWAITING_WIN_URL_KEY, None)


def clear_transient_states(context: ContextTypes.DEFAULT_TYPE) -> None:
    clear_awaiting_states(context)
    clear_pending_confirmation(context)


async def start_with_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    clear_transient_states(context)

    text = (
        "Бот запущен и готов к работе.\n\n"
        "Теперь можно не помнить весь список команд вручную — пользуйся кнопками ниже.\n\n"
        "Что есть сейчас:\n"
        "• управление сервером\n"
        "• управление Windows-агентом\n"
        "• скриншот и фото с камеры\n"
        "• голосовые ответы\n"
        "• обычный AI-чат\n\n"
        "Если нужно — напиши /help или открой меню командой /menu."
    )

    await update.message.reply_text(text, reply_markup=get_main_menu_keyboard())


async def help_with_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    clear_transient_states(context)

    text = (
        "Главное управление теперь через кнопки 👇\n\n"
        "Что где лежит:\n"
        "• 🖥 Сервер — статус, RAM, диск, процессы, docker, nginx, логи, reboot\n"
        "• 🪟 Windows — статус агента, скриншот, камера, lock, logout, shutdown, reboot, open url\n"
        "• 🎤 Голос — включить или выключить голосовые ответы\n"
        "• 🧠 Очистить память — сброс истории диалога\n\n"
        "Опасные действия требуют код подтверждения.\n\n"
        "Старые команды тоже работают.\n"
        "Например:\n"
        "/server\n"
        "/disk\n"
        "/ram\n"
        "/win_status\n"
        "/win_screenshot\n"
        "/win_camera\n"
        "/win_open_url https://youtube.com\n\n"
        "Для открытия меню в любой момент: /menu"
    )

    await update.message.reply_text(text, reply_markup=get_main_menu_keyboard())


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    clear_transient_states(context)
    await update.message.reply_text("Открыла главное меню.", reply_markup=get_main_menu_keyboard())


async def hide_menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    clear_transient_states(context)
    await update.message.reply_text(
        "Спрятала клавиатуру. Вернуть можно через /menu",
        reply_markup=ReplyKeyboardRemove(),
    )


async def open_server_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    clear_transient_states(context)
    await update.message.reply_text("Раздел сервера.", reply_markup=get_server_menu_keyboard())


async def open_windows_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    clear_transient_states(context)
    await update.message.reply_text("Раздел Windows.", reply_markup=get_windows_menu_keyboard())


async def open_voice_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    clear_transient_states(context)
    await update.message.reply_text("Раздел голоса.", reply_markup=get_voice_menu_keyboard())


async def begin_win_open_url_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    clear_pending_confirmation(context)
    set_awaiting_win_url(context, True)

    await update.message.reply_text(
        "Пришли ссылку следующим сообщением.\n\n"
        "Например:\n"
        "https://youtube.com\n"
        "или просто\n"
        "youtube.com\n\n"
        "Если передумал — нажми ❌ Отмена.",
        reply_markup=get_cancel_keyboard(),
    )


async def awaiting_menu_input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    if not is_awaiting_win_url(context):
        return

    if text == BTN_CANCEL:
        clear_awaiting_states(context)
        await update.message.reply_text(
            "Отменила ввод ссылки.",
            reply_markup=get_windows_menu_keyboard(),
        )
        return

    if text == BTN_BACK:
        clear_transient_states(context)
        await update.message.reply_text(
            "Вернула тебя в главное меню.",
            reply_markup=get_main_menu_keyboard(),
        )
        return

    if text == BTN_HIDE_MENU:
        clear_transient_states(context)
        await update.message.reply_text(
            "Спрятала клавиатуру. Вернуть можно через /menu",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    if not is_probably_url(text):
        await update.message.reply_text(
            "Это не похоже на ссылку.\n\n"
            "Пришли что-то вроде:\n"
            "https://youtube.com\n"
            "или\n"
            "google.com",
            reply_markup=get_cancel_keyboard(),
        )
        return

    normalized = normalize_url(text)

    context.args = [normalized]
    clear_awaiting_states(context)

    await win_open_url(update, context)

    await update.message.reply_text(
        "Готово. Возвращаю меню Windows.",
        reply_markup=get_windows_menu_keyboard(),
    )


async def menu_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    if text == BTN_MAIN_SERVER:
        await open_server_menu(update, context)
        return

    if text == BTN_MAIN_WINDOWS:
        await open_windows_menu(update, context)
        return

    if text == BTN_MAIN_VOICE:
        await open_voice_menu(update, context)
        return

    if text == BTN_MAIN_HELP:
        await help_with_menu(update, context)
        return

    if text == BTN_MAIN_CLEAR:
        clear_transient_states(context)
        await clear_command(update, context)
        await update.message.reply_text(
            "Главное меню снова тут.",
            reply_markup=get_main_menu_keyboard(),
        )
        return

    if text == BTN_HIDE_MENU:
        await hide_menu_command(update, context)
        return

    if text == BTN_BACK:
        clear_transient_states(context)
        await update.message.reply_text(
            "Вернула тебя в главное меню.",
            reply_markup=get_main_menu_keyboard(),
        )
        return

    if text == BTN_CANCEL:
        if has_pending_confirmation(context):
            await cancel_pending_action(update, context)
            return

        if is_awaiting_win_url(context):
            clear_awaiting_states(context)
            await update.message.reply_text(
                "Отменила ввод ссылки.",
                reply_markup=get_windows_menu_keyboard(),
            )
            return

        clear_transient_states(context)
        await update.message.reply_text(
            "Окей, отмена.",
            reply_markup=get_main_menu_keyboard(),
        )
        return

    # SERVER
    if text == BTN_SERVER_SUMMARY:
        await server_command(update, context)
        return

    if text == BTN_SERVER_UPTIME:
        await uptime_command(update, context)
        return

    if text == BTN_SERVER_DISK:
        await disk_command(update, context)
        return

    if text == BTN_SERVER_RAM:
        await ram_command(update, context)
        return

    if text == BTN_SERVER_TOP:
        await top_command(update, context)
        return

    if text == BTN_SERVER_SERVICES:
        await services_command(update, context)
        return

    if text == BTN_SERVER_DOCKER:
        await docker_command(update, context)
        return

    if text == BTN_SERVER_NGINX:
        await nginx_command(update, context)
        return

    if text == BTN_SERVER_LOGS:
        await logs_command(update, context)
        return

    if text == BTN_SERVER_NET:
        await net_command(update, context)
        return

    if text == BTN_SERVER_WHOAMI:
        await whoami_command(update, context)
        return

    if text == BTN_SERVER_IP:
        await ip_command(update, context)
        return

    if text == BTN_SERVER_PING:
        await ping(update, context)
        return

    if text == BTN_SERVER_REBOOT:
        await request_server_reboot_confirmation(update, context)
        return

    # WINDOWS
    if text == BTN_WIN_STATUS:
        await win_status_command(update, context)
        return

    if text == BTN_WIN_SCREENSHOT:
        await win_screenshot_command(update, context)
        return

    if text == BTN_WIN_CAMERA:
        await win_camera_command(update, context)
        return

    if text == BTN_WIN_OPEN_URL:
        await begin_win_open_url_flow(update, context)
        return

    if text == BTN_WIN_LOCK:
        await request_win_lock_confirmation(update, context)
        return

    if text == BTN_WIN_UNLOCK:
        await win_unlock_screen(update, context)
        return

    if text == BTN_WIN_LOGOUT:
        await request_win_logout_confirmation(update, context)
        return

    if text == BTN_WIN_SHUTDOWN:
        await request_win_shutdown_confirmation(update, context)
        return

    if text == BTN_WIN_REBOOT:
        await request_win_reboot_confirmation(update, context)
        return

    # VOICE
    if text == BTN_VOICE_ON:
        await voice_on_command(update, context)
        await update.message.reply_text(
            "Меню голоса оставила открытым.",
            reply_markup=get_voice_menu_keyboard(),
        )
        return

    if text == BTN_VOICE_OFF:
        await voice_off_command(update, context)
        await update.message.reply_text(
            "Меню голоса оставила открытым.",
            reply_markup=get_voice_menu_keyboard(),
        )
        return