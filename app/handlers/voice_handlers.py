from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from app.config import VOICE_DIR, MAX_TEXT_REPLY_CHARS
from app.handlers.command_handlers import deny_access, send_action_result
from app.security.auth import is_allowed
from app.services.action_service import (
    execute_action,
    is_confirmation_required,
    request_action_confirmation,
    try_handle_confirmation_text,
)
from app.services.intent_service import resolve_user_intent
from app.services.memory_service import ensure_dirs, add_to_memory
from app.services.openai_service import transcribe_audio_file, ask_openai
from app.services.voice_service import send_voice_reply
from app.utils.text_utils import truncate


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
        await update.message.reply_text(f"Не смогла скачать голосовуху: {e}")
        return

    transcript_text = transcribe_audio_file(local_path)

    try:
        local_path.unlink(missing_ok=True)
    except Exception:
        pass

    if not transcript_text:
        await update.message.reply_text("Не смогла распознать голосовуху.")
        return

    if transcript_text.startswith("Ошибка распознавания аудио:"):
        await update.message.reply_text(transcript_text)
        return

    await update.message.reply_text(f"Распознала так:\n\n{transcript_text}")

    confirmation_result = try_handle_confirmation_text(transcript_text)
    if confirmation_result is not None:
        await send_action_result(update, confirmation_result)

        if confirmation_result.get("type") == "text":
            await update.message.chat.send_action(action=ChatAction.RECORD_VOICE)
            await send_voice_reply(update, confirmation_result.get("text", "Готово."))
        return

    intent = resolve_user_intent(transcript_text)

    if intent["kind"] == "action":
        action_name = intent["action"]
        args = intent.get("args", {})

        if is_confirmation_required(action_name):
            text = request_action_confirmation(action_name, args)
            await update.message.reply_text(text)
            await update.message.chat.send_action(action=ChatAction.RECORD_VOICE)
            await send_voice_reply(update, text)
            return

        result = execute_action(action_name, args)
        await send_action_result(update, result)

        if result.get("type") == "text":
            await update.message.chat.send_action(action=ChatAction.RECORD_VOICE)
            await send_voice_reply(update, result.get("text", "Готово."))
        return

    answer = ask_openai(transcript_text)
    answer = truncate(answer, MAX_TEXT_REPLY_CHARS)

    add_to_memory("user", transcript_text)
    add_to_memory("assistant", answer)

    await update.message.reply_text(answer)

    await update.message.chat.send_action(action=ChatAction.RECORD_VOICE)
    await send_voice_reply(update, answer)