import logging
from pathlib import Path
from openai import OpenAI

from app.config import (
    OPENAI_API_KEY,
    OPENAI_MODEL,
    OPENAI_TRANSCRIBE_MODEL,
    OPENAI_TTS_MODEL,
    OPENAI_TTS_VOICE,
    SYSTEM_PROMPT,
    MAX_TTS_CHARS,
)
from app.services.memory_service import load_memory
from app.utils.text_utils import truncate_for_tts

logger = logging.getLogger(__name__)

client = OpenAI(api_key=OPENAI_API_KEY)


def build_openai_input(user_text: str) -> list[dict]:
    memory = load_memory()

    input_items = [
        {
            "role": "system",
            "content": [{"type": "input_text", "text": SYSTEM_PROMPT}],
        }
    ]

    for item in memory:
        role = item.get("role")
        text = item.get("text", "")
        if role not in {"user", "assistant"} or not text:
            continue

        if role == "user":
            content = [{"type": "input_text", "text": text}]
        else:
            content = [{"type": "output_text", "text": text}]

        input_items.append(
            {
                "role": role,
                "content": content,
            }
        )

    input_items.append(
        {
            "role": "user",
            "content": [{"type": "input_text", "text": user_text}],
        }
    )

    return input_items


def ask_openai(user_text: str) -> str:
    try:
        response = client.responses.create(
            model=OPENAI_MODEL,
            input=build_openai_input(user_text),
        )

        if hasattr(response, "output_text") and response.output_text:
            return response.output_text.strip()

        return str(response)

    except Exception as e:
        logger.exception("OpenAI request failed")
        return f"Ошибка OpenAI API: {e}"


def transcribe_audio_file(file_path: Path) -> str:
    try:
        with open(file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model=OPENAI_TRANSCRIBE_MODEL,
                file=audio_file,
            )

        text = getattr(transcript, "text", None)
        if text and text.strip():
            return text.strip()

        return ""
    except Exception as e:
        logger.exception("Audio transcription failed")
        return f"Ошибка распознавания аудио: {e}"


def synthesize_speech_to_file(text: str, output_path: Path) -> str | None:
    try:
        text_for_tts = truncate_for_tts(text, MAX_TTS_CHARS)

        response = client.audio.speech.create(
            model=OPENAI_TTS_MODEL,
            voice=OPENAI_TTS_VOICE,
            input=text_for_tts,
            response_format="opus",
        )

        audio_bytes = response.read()
        output_path.write_bytes(audio_bytes)
        return None
    except Exception as e:
        logger.exception("TTS generation failed")
        return f"Ошибка генерации голоса: {e}"
