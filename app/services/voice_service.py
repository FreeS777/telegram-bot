import logging
from pathlib import Path
from telegram import Update

from app.config import TTS_DIR
from app.services.memory_service import ensure_dirs
from app.services.openai_service import synthesize_speech_to_file

logger = logging.getLogger(__name__)


async def send_voice_reply(update: Update, text: str) -> None:
    ensure_dirs()

    if not update.message:
        return

    tts_file = TTS_DIR / f"reply_{update.message.message_id}.opus"

    error = synthesize_speech_to_file(text, tts_file)
    if error:
        await update.message.reply_text(error)
        return

    try:
        with open(tts_file, "rb") as f:
            await update.message.reply_voice(voice=f)
    except Exception as e:
        logger.exception("Failed to send voice reply")
        await update.message.reply_text(f"Не смогла отправить голосовой ответ: {e}")
    finally:
        try:
            tts_file.unlink(missing_ok=True)
        except Exception:
            logger.exception("Failed to delete temporary TTS file")
