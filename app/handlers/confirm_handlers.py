from telegram import Update
from telegram.ext import ContextTypes

from app.handlers.command_handlers import (
    reboot_command,
    win_lock_command,
    win_logout_command,
    win_shutdown_command,
    win_reboot_command,
)
from app.keyboards.menu_keyboards import (
    BTN_CANCEL,
    get_confirmation_keyboard,
    get_keyboard_for_scope,
)
from app.security.auth import is_allowed
from app.handlers.command_handlers import deny_access
from app.services.confirm_service import (
    clear_pending_confirmation,
    create_pending_confirmation,
    get_confirmation_expire_seconds_left,
    get_pending_confirmation,
    has_pending_confirmation,
    is_confirmation_code_valid,
)


ACTION_EXECUTORS = {
    "server_reboot": reboot_command,
    "win_lock": win_lock_command,
    "win_logout": win_logout_command,
    "win_shutdown": win_shutdown_command,
    "win_reboot": win_reboot_command,
}


async def _request_confirmation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    *,
    action: str,
    title: str,
    scope: str,
) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    payload = create_pending_confirmation(
        context,
        action=action,
        title=title,
        scope=scope,
    )

    await update.message.reply_text(
        "⚠️ Подтверждение действия\n\n"
        f"Команда: {title}\n"
        f"Код: {payload['code']}\n"
        "Действует: 120 секунд\n\n"
        "Отправь код следующим сообщением\n"
        "или командой:\n"
        f"/confirm {payload['code']}\n\n"
        "Для отмены нажми ❌ Отмена.",
        reply_markup=get_confirmation_keyboard(),
    )


async def request_server_reboot_confirmation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    await _request_confirmation(
        update,
        context,
        action="server_reboot",
        title="Перезагрузка сервера",
        scope="server",
    )


async def request_win_lock_confirmation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    await _request_confirmation(
        update,
        context,
        action="win_lock",
        title="Блокировка Windows",
        scope="windows",
    )


async def request_win_logout_confirmation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    await _request_confirmation(
        update,
        context,
        action="win_logout",
        title="Выход из Windows-сессии",
        scope="windows",
    )


async def request_win_shutdown_confirmation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    await _request_confirmation(
        update,
        context,
        action="win_shutdown",
        title="Выключение Windows",
        scope="windows",
    )


async def request_win_reboot_confirmation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    await _request_confirmation(
        update,
        context,
        action="win_reboot",
        title="Перезагрузка Windows",
        scope="windows",
    )


async def cancel_pending_action(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    payload = get_pending_confirmation(context)
    if not payload:
        await update.message.reply_text(
            "Сейчас нет действия, которое ждёт подтверждения.",
            reply_markup=get_keyboard_for_scope("main"),
        )
        return

    scope = payload.get("scope", "main")
    clear_pending_confirmation(context)

    await update.message.reply_text(
        "Окей, действие отменено.",
        reply_markup=get_keyboard_for_scope(scope),
    )


async def confirm_code_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    if not context.args:
        payload = get_pending_confirmation(context)
        if not payload:
            await update.message.reply_text("Сейчас нет ожидающего подтверждения.")
            return

        ttl_left = get_confirmation_expire_seconds_left(context)
        await update.message.reply_text(
            "Нужно передать код.\n\n"
            "Пример:\n"
            f"/confirm {payload['code']}\n\n"
            f"Осталось времени: {ttl_left} сек.",
            reply_markup=get_confirmation_keyboard(),
        )
        return

    code = str(context.args[0]).strip()
    await _process_confirmation_code(update, context, code)


async def confirmation_text_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not is_allowed(update):
        await deny_access(update)
        return

    if not update.message or not update.message.text:
        return

    if not has_pending_confirmation(context):
        return

    text = update.message.text.strip()

    if text == BTN_CANCEL:
        await cancel_pending_action(update, context)
        return

    if not text.isdigit():
        return

    await _process_confirmation_code(update, context, text)


async def _process_confirmation_code(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    code: str,
) -> None:
    payload = get_pending_confirmation(context)
    if not payload:
        await update.message.reply_text("Подтверждение уже истекло или было отменено.")
        return

    if not is_confirmation_code_valid(context, code):
        ttl_left = get_confirmation_expire_seconds_left(context)
        await update.message.reply_text(
            "Код не совпал.\n\n"
            f"Осталось времени: {ttl_left} сек.\n"
            "Попробуй ещё раз или нажми ❌ Отмена.",
            reply_markup=get_confirmation_keyboard(),
        )
        return

    action = payload["action"]
    scope = payload.get("scope", "main")
    title = payload.get("title", action)

    executor = ACTION_EXECUTORS.get(action)
    clear_pending_confirmation(context)

    if not executor:
        await update.message.reply_text(
            "Не нашла обработчик для этого действия.",
            reply_markup=get_keyboard_for_scope(scope),
        )
        return

    await update.message.reply_text(
        f"✅ Код принят. Выполняю: {title}",
        reply_markup=get_keyboard_for_scope(scope),
    )

    await executor(update, context)