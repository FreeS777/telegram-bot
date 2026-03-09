from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from app.config import MAX_TEXT_REPLY_CHARS
from app.security.auth import is_allowed
from app.handlers.command_handlers import deny_access
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

    answer = ask_openai(user_text)
    answer = truncate(answer, MAX_TEXT_REPLY_CHARS)

    add_to_memory("user", user_text)
    add_to_memory("assistant", answer)

    await update.message.reply_text(answer)

    if get_voice_mode():
        await update.message.chat.send_action(action=ChatAction.RECORD_VOICE)
        await send_voice_reply(update, answer)
