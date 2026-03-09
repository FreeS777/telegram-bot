import re

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

from app.security.auth import is_allowed
from app.handlers.command_handlers import (
    deny_access,
    clear_command,
    voice_on_command,
    voice_off_command,
    ping,
    ip_command,
    search,
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
    win_lock_command,
    win_logout_command,
    win_shutdown_command,
    win_reboot_command,
    win_screenshot_command,
    win_unlock_screen,
)


BTN_MAIN_SERVER = "🖥 Сервер"
BTN_MAIN_WINDOWS = "🪟 Windows"
BTN_MAIN_VOICE = "🎤 Голос"
BTN_MAIN_HELP = "ℹ️ Помощь"
BTN_MAIN_CLEAR = "🧠 Очистить память"

BTN_BACK = "🏠 Главное меню"

BTN_SERVER_SUMMARY = "📊 Сводка"
BTN_SERVER_UPTIME = "⏱ Uptime"
BTN_SERVER_DISK = "💾 Disk"
BTN_SERVER_RAM = "🧠 RAM"
BTN_SERVER_TOP = "🔥 Top"
BTN_SERVER_SERVICES = "🧩 Services"
BTN_SERVER_DOCKER = "🐳 Docker"
BTN_SERVER_NGINX = "🌐 Nginx"
BTN_SERVER_LOGS = "📜 Logs"
BTN_SERVER_NET = "🌍 Net"
BTN_SERVER_WHOAMI = "🙋 Whoami"
BTN_SERVER_IP = "🌐 Внешний IP"
BTN_SERVER_PING = "🏓 Ping"

BTN_WIN_STATUS = "✅ Статус"
BTN_WIN_LOCK = "🔒 Lock"
BTN_WIN_UNLOCK = "🔓 Unlock"
BTN_WIN_LOGOUT = "🚪 Logout"
BTN_WIN_SCREENSHOT = "📷 Скриншот"
BTN_WIN_SHUTDOWN = "🔌 Shutdown"
BTN_WIN_REBOOT = "🔄 Reboot"
BTN_WIN_OPEN_URL_HINT = "🌍 Open URL"

BTN_VOICE_ON = "🟢 Голос вкл"
BTN_VOICE_OFF = "🔴 Голос выкл"

MENU_BUTTONS = [
    BTN_MAIN_SERVER,
    BTN_MAIN_WINDOWS,
    BTN_MAIN_VOICE,
    BTN_MAIN_HELP,
    BTN_MAIN_CLEAR,
    BTN_BACK,
    BTN_SERVER_SUMMARY,
    BTN_SERVER_UPTIME,
    BTN_SERVER_DISK,
    BTN_SERVER_RAM,
    BTN_SERVER_TOP,
    BTN_SERVER_SERVICES,
    BTN_SERVER_DOCKER,
    BTN_SERVER_NGINX,
    BTN_SERVER_LOGS,
    BTN_SERVER_NET,
    BTN_SERVER_WHOAMI,
    BTN_SERVER_IP,
    BTN_SERVER_PING,
    BTN_WIN_STATUS,
    BTN_WIN_LOCK,
    BTN_WIN_UNLOCK,
    BTN_WIN_LOGOUT,
    BTN_WIN_SCREENSHOT,
    BTN_WIN_SHUTDOWN,
    BTN_WIN_REBOOT,
    BTN_WIN_OPEN_URL_HINT,
    BTN_VOICE_ON,
    BTN_VOICE_OFF,
]

MENU_BUTTON_PATTERN = r"^(%s)$" % "|".join(re.escape(button) for button in MENU_BUTTONS)


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [BTN_MAIN_SERVER, BTN_MAIN_WINDOWS],
            [BTN_MAIN_VOICE, BTN_MAIN_HELP],
            [BTN_MAIN_CLEAR],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        selective=True,
        input_field_placeholder="Выбери раздел меню…",
    )


def get_server_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [BTN_SERVER_SUMMARY, BTN_SERVER_PING],
            [BTN_SERVER_IP, BTN_SERVER_UPTIME],
            [BTN_SERVER_DISK, BTN_SERVER_RAM],
            [BTN_SERVER_TOP, BTN_SERVER_SERVICES],
            [BTN_SERVER_DOCKER, BTN_SERVER_NGINX],
            [BTN_SERVER_LOGS, BTN_SERVER_NET],
            [BTN_SERVER_WHOAMI],
            [BTN_BACK],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        selective=True,
        input_field_placeholder="Раздел: Сервер",
    )


def get_windows_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [BTN_WIN_STATUS, BTN_WIN_SCREENSHOT],
            [BTN_WIN_LOCK, BTN_WIN_UNLOCK],
            [BTN_WIN_LOGOUT],
            [BTN_WIN_SHUTDOWN, BTN_WIN_REBOOT],
            [BTN_WIN_OPEN_URL_HINT],
            [BTN_BACK],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        selective=True,
        input_field_placeholder="Раздел: Windows",
    )


def get_voice_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [BTN_VOICE_ON, BTN_VOICE_OFF],
            [BTN_MAIN_CLEAR],
            [BTN_BACK],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        selective=True,
        input_field_placeholder="Раздел: Голос",
    )


async def start_with_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    text = (
        "Бот запущен и готов к работе.\n\n"
        "Теперь можно не помнить весь зоопарк команд вручную — "
        "пользуйся кнопками ниже.\n\n"
        "Что есть сейчас:\n"
        "• управление сервером\n"
        "• управление Windows-агентом\n"
        "• голосовые ответы\n"
        "• обычный AI-чат\n\n"
        "Если нужно — напиши /help или открой меню командой /menu."
    )

    await update.message.reply_text(
        text,
        reply_markup=get_main_menu_keyboard(),
    )


async def help_with_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    text = (
        "Главное управление теперь через кнопки 👇\n\n"
        "Что где лежит:\n"
        "• 🖥 Сервер — статус, RAM, диск, процессы, docker, nginx, логи\n"
        "• 🪟 Windows — статус агента, скриншот, lock/logout/shutdown/reboot\n"
        "• 🎤 Голос — включить или выключить голосовые ответы\n"
        "• 🧠 Очистить память — сброс истории диалога\n\n"
        "Старые команды тоже работают.\n"
        "Например:\n"
        "/server\n"
        "/disk\n"
        "/ram\n"
        "/win_status\n"
        "/win_screenshot\n\n"
        "Для открытия меню в любой момент: /menu\n"
        "Для открытия сайта на Windows пока оставляем текстовую команду:\n"
        "/win_open_url https://youtube.com"
    )

    await update.message.reply_text(
        text,
        reply_markup=get_main_menu_keyboard(),
    )


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    await update.message.reply_text(
        "Открыла главное меню.",
        reply_markup=get_main_menu_keyboard(),
    )


async def open_server_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    await update.message.reply_text(
        "Раздел сервера. Тут уже кнопки без шаманства с командами.",
        reply_markup=get_server_menu_keyboard(),
    )


async def open_windows_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    await update.message.reply_text(
        "Раздел Windows. Опасные кнопки тут уже пахнут приключениями.",
        reply_markup=get_windows_menu_keyboard(),
    )


async def open_voice_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    await update.message.reply_text(
        "Раздел голоса.",
        reply_markup=get_voice_menu_keyboard(),
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
        await clear_command(update, context)
        await update.message.reply_text(
            "Главное меню снова тут.",
            reply_markup=get_main_menu_keyboard(),
        )
        return

    if text == BTN_BACK:
        await update.message.reply_text(
            "Вернула тебя в главное меню.",
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

    # WINDOWS
    if text == BTN_WIN_STATUS:
        await win_status_command(update, context)
        return

    if text == BTN_WIN_LOCK:
        await win_lock_command(update, context)
        return

    if text == BTN_WIN_UNLOCK:
        await win_unlock_screen(update, context)
        return

    if text == BTN_WIN_LOGOUT:
        await win_logout_command(update, context)
        return

    if text == BTN_WIN_SCREENSHOT:
        await win_screenshot_command(update, context)
        return

    if text == BTN_WIN_SHUTDOWN:
        await win_shutdown_command(update, context)
        return

    if text == BTN_WIN_REBOOT:
        await win_reboot_command(update, context)
        return

    if text == BTN_WIN_OPEN_URL_HINT:
        await update.message.reply_text(
            "Эту команду пока удобнее текстом:\n"
            "/win_open_url https://youtube.com",
            reply_markup=get_windows_menu_keyboard(),
        )
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