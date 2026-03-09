from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from app.config import MAX_TEXT_REPLY_CHARS
from app.handlers.command_handlers import deny_access, send_action_result
from app.security.auth import is_allowed
from app.services.action_service import (
    is_confirmation_required,
    request_action_confirmation,
    try_handle_confirmation_text,
    execute_action,
)
from app.services.intent_service import resolve_user_intent
from app.services.memory_service import add_to_memory, get_voice_mode
from app.services.openai_service import ask_openai
from app.services.voice_service import send_voice_reply
from app.utils.text_utils import truncate


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

    confirmation_result = try_handle_confirmation_text(user_text)
    if confirmation_result is not None:
        await send_action_result(update, confirmation_result)
        return

    intent = resolve_user_intent(user_text)

    if intent["kind"] == "action":
        action_name = intent["action"]
        args = intent.get("args", {})

        if is_confirmation_required(action_name):
            text = request_action_confirmation(action_name, args)
            await update.message.reply_text(text)
            return

        result = execute_action(action_name, args)
        await send_action_result(update, result)
        return

    answer = ask_openai(user_text)
    answer = truncate(answer, MAX_TEXT_REPLY_CHARS)

    add_to_memory("user", user_text)
    add_to_memory("assistant", answer)

    await update.message.reply_text(answer)

    if get_voice_mode():
        await update.message.chat.send_action(action=ChatAction.RECORD_VOICE)
        await send_voice_reply(update, answer)