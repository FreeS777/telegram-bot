import re

from telegram import ReplyKeyboardMarkup


BTN_MAIN_SERVER = "🖥 Сервер"
BTN_MAIN_WINDOWS = "🪟 Windows"
BTN_MAIN_VOICE = "🎤 Голос"
BTN_MAIN_HELP = "ℹ️ Помощь"
BTN_MAIN_CLEAR = "🧠 Очистить память"
BTN_HIDE_MENU = "🙈 Скрыть меню"

BTN_BACK = "🏠 Главное меню"
BTN_CANCEL = "❌ Отмена"

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
BTN_SERVER_REBOOT = "♻️ Reboot Server"

BTN_WIN_STATUS = "✅ Статус"
BTN_WIN_LOCK = "🔒 Lock"
BTN_WIN_UNLOCK = "🔓 Unlock"
BTN_WIN_LOGOUT = "🚪 Logout"
BTN_WIN_SCREENSHOT = "📷 Скриншот"
BTN_WIN_CAMERA = "📸 Камера"
BTN_WIN_SHUTDOWN = "🔌 Shutdown"
BTN_WIN_REBOOT = "🔄 Reboot"
BTN_WIN_OPEN_URL = "🌍 Open URL"

BTN_VOICE_ON = "🟢 Голос вкл"
BTN_VOICE_OFF = "🔴 Голос выкл"

MENU_BUTTONS = [
    BTN_MAIN_SERVER,
    BTN_MAIN_WINDOWS,
    BTN_MAIN_VOICE,
    BTN_MAIN_HELP,
    BTN_MAIN_CLEAR,
    BTN_HIDE_MENU,
    BTN_BACK,
    BTN_CANCEL,
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
    BTN_SERVER_REBOOT,
    BTN_WIN_STATUS,
    BTN_WIN_LOCK,
    BTN_WIN_UNLOCK,
    BTN_WIN_LOGOUT,
    BTN_WIN_SCREENSHOT,
    BTN_WIN_CAMERA,
    BTN_WIN_SHUTDOWN,
    BTN_WIN_REBOOT,
    BTN_WIN_OPEN_URL,
    BTN_VOICE_ON,
    BTN_VOICE_OFF,
]

MENU_BUTTON_PATTERN = r"^(%s)$" % "|".join(re.escape(button) for button in MENU_BUTTONS)


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [BTN_MAIN_SERVER, BTN_MAIN_WINDOWS],
            [BTN_MAIN_VOICE, BTN_MAIN_HELP],
            [BTN_MAIN_CLEAR, BTN_HIDE_MENU],
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
            [BTN_SERVER_WHOAMI, BTN_SERVER_REBOOT],
            [BTN_BACK, BTN_HIDE_MENU],
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
            [BTN_WIN_CAMERA, BTN_WIN_OPEN_URL],
            [BTN_WIN_LOCK, BTN_WIN_UNLOCK],
            [BTN_WIN_LOGOUT],
            [BTN_WIN_SHUTDOWN, BTN_WIN_REBOOT],
            [BTN_BACK, BTN_HIDE_MENU],
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
            [BTN_BACK, BTN_HIDE_MENU],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        selective=True,
        input_field_placeholder="Раздел: Голос",
    )


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[BTN_CANCEL, BTN_BACK]],
        resize_keyboard=True,
        one_time_keyboard=False,
        selective=True,
        input_field_placeholder="Жду ввод…",
    )


def get_confirmation_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[BTN_CANCEL]],
        resize_keyboard=True,
        one_time_keyboard=False,
        selective=True,
        input_field_placeholder="Введи код подтверждения…",
    )


def get_keyboard_for_scope(scope: str) -> ReplyKeyboardMarkup:
    if scope == "windows":
        return get_windows_menu_keyboard()
    if scope == "server":
        return get_server_menu_keyboard()
    if scope == "voice":
        return get_voice_menu_keyboard()
    return get_main_menu_keyboard()