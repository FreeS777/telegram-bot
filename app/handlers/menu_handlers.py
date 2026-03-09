from telegram import Update
from telegram.ext import ContextTypes

from app.handlers.command_handlers import send_action_result
from app.security.auth import is_allowed
from app.services.action_service import (
    execute_action,
    is_confirmation_required,
    request_action_confirmation,
)
from app.keyboards.menu_keyboards import (
    HIDDEN_MENU,
    MAIN_MENU_KEYBOARD,
    SERVER_MENU_KEYBOARD,
    WINDOWS_MENU_KEYBOARD,
)


async def _deny(update: Update) -> None:
    if update.message:
        await update.message.reply_text("Доступ запрещён.")


async def start_with_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await _deny(update)
        return

    text = (
        "Бот запущен.\n\n"
        "Можно:\n"
        "- жать кнопки меню\n"
        "- писать обычным текстом\n"
        "- слать голосовухи человеческим языком\n"
        "- использовать slash-команды\n\n"
        "Выбирай, что делаем."
    )
    await update.message.reply_text(text, reply_markup=MAIN_MENU_KEYBOARD)


async def help_with_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await _deny(update)
        return

    text = (
        "Что умею:\n\n"
        "Linux/VPS:\n"
        "/server /uptime /disk /ram /top /logs /net /whoami /services /docker /ip\n\n"
        "Windows:\n"
        "/win_status /win_screenshot /win_camera /win_lock /win_logout /win_reboot /win_shutdown /win_unlock_screen\n\n"
        "Также понимаю обычный текст и голосовухи.\n"
        "Опасные действия идут через подтверждение."
    )
    await update.message.reply_text(text, reply_markup=MAIN_MENU_KEYBOARD)


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await _deny(update)
        return

    await update.message.reply_text(
        "Вернула тебя в главное меню.",
        reply_markup=MAIN_MENU_KEYBOARD,
    )


async def hide_menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await _deny(update)
        return

    await update.message.reply_text(
        "Меню скрыла. Вернуть можно командой /menu или /start.",
        reply_markup=HIDDEN_MENU,
    )


async def menu_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        await _deny(update)
        return

    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    if text == "🏠 Главное меню":
        await update.message.reply_text(
            "Вернула тебя в главное меню.",
            reply_markup=MAIN_MENU_KEYBOARD,
        )
        return

    if text == "📚 Помощь":
        await help_with_menu(update, context)
        return

    if text == "🙈 Скрыть меню":
        await hide_menu_command(update, context)
        return

    if text == "🖥️ Сервер":
        await update.message.reply_text(
            "Раздел сервера.",
            reply_markup=SERVER_MENU_KEYBOARD,
        )
        return

    if text == "🪟 Windows":
        await update.message.reply_text(
            "Раздел Windows.",
            reply_markup=WINDOWS_MENU_KEYBOARD,
        )
        return

    if text == "🎤 Голос on":
        result = execute_action("voice_on")
        await send_action_result(update, result)
        return

    if text == "🔇 Голос off":
        result = execute_action("voice_off")
        await send_action_result(update, result)
        return

    action_map = {
        "✅ Статус": "win_status",
        "📊 Сводка": "server",
        "⏱️ Uptime": "uptime",
        "💾 Disk": "disk",
        "🧠 RAM": "ram",
        "📈 Top": "top",
        "🧾 Logs": "logs",
        "🌐 Net": "net",
        "👤 Whoami": "whoami",
        "⚙️ Services": "services",
        "🐳 Docker": "docker",
        "🌍 IP": "ip",
        "📸 Скриншот": "win_screenshot",
        "📷 Камера": "win_camera",
        "🔒 Lock": "win_lock",
        "🚪 Logout": "win_logout",
        "🔁 Reboot": "win_reboot",
        "🔌 Shutdown": "win_shutdown",
        "🔓 Unlock": "win_unlock_screen",
    }

    if text == "🌐 Открыть URL":
        await update.message.reply_text(
            "Пришли обычным сообщением что-то вроде:\n\n"
            "открой https://youtube.com"
        )
        return

    action_name = action_map.get(text)
    if not action_name:
        await update.message.reply_text(
            "Не поняла кнопку. Нажми ещё раз или напиши текстом."
        )
        return

    if is_confirmation_required(action_name):
        confirm_text = request_action_confirmation(action_name, {})
        await update.message.reply_text(confirm_text)
        return

    result = execute_action(action_name, {})
    await send_action_result(update, result)