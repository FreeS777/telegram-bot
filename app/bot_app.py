from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

from app.config import BOT_TOKEN
from app.handlers.command_handlers import (
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
    win_screenshot_command,
    win_open_url,
    win_unlock_screen,
)
from app.handlers.chat_handlers import chat_message
from app.handlers.confirm_handlers import (
    cancel_pending_action,
    confirm_code_command,
    confirmation_text_handler,
    request_server_reboot_confirmation,
    request_win_lock_confirmation,
    request_win_logout_confirmation,
    request_win_reboot_confirmation,
    request_win_shutdown_confirmation,
)
from app.handlers.menu_handlers import (
    awaiting_menu_input_handler,
    help_with_menu,
    hide_menu_command,
    menu_command,
    menu_text_handler,
    start_with_menu,
)
from app.handlers.voice_handlers import voice_message
from app.keyboards.menu_keyboards import MENU_BUTTON_PATTERN


def create_bot_app():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Основные команды
    app.add_handler(CommandHandler("start", start_with_menu))
    app.add_handler(CommandHandler("help", help_with_menu))
    app.add_handler(CommandHandler("menu", menu_command))
    app.add_handler(CommandHandler("hide_menu", hide_menu_command))

    # Команды подтверждения
    app.add_handler(CommandHandler("confirm", confirm_code_command))
    app.add_handler(CommandHandler("cancel_action", cancel_pending_action))

    # Старые безопасные команды
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
    app.add_handler(CommandHandler("win_status", win_status_command))
    app.add_handler(CommandHandler("win_screenshot", win_screenshot_command))
    app.add_handler(CommandHandler("win_open_url", win_open_url))
    app.add_handler(CommandHandler("win_unlock_screen", win_unlock_screen))

    # Опасные команды теперь через подтверждение
    app.add_handler(CommandHandler("reboot", request_server_reboot_confirmation))
    app.add_handler(CommandHandler("win_lock", request_win_lock_confirmation))
    app.add_handler(CommandHandler("win_logout", request_win_logout_confirmation))
    app.add_handler(CommandHandler("win_shutdown", request_win_shutdown_confirmation))
    app.add_handler(CommandHandler("win_reboot", request_win_reboot_confirmation))

    # Голос
    app.add_handler(MessageHandler(filters.VOICE, voice_message))

    # Сначала кнопки меню
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.Regex(MENU_BUTTON_PATTERN),
            menu_text_handler,
        )
    )

    # Потом режим ожидания URL
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            awaiting_menu_input_handler,
        )
    )

    # Потом подтверждение кодом:
    # ловим либо цифры, либо кнопку отмены
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & (filters.Regex(r"^\d{4,6}$") | filters.Regex(r"^❌ Отмена$")),
            confirmation_text_handler,
        )
    )

    # И только потом обычный чат
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_message))

    return app