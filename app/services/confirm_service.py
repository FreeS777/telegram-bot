import secrets
import time
from typing import Optional


PENDING_CONFIRMATION_KEY = "pending_confirmation"
DEFAULT_CONFIRM_TTL_SECONDS = 120


def generate_confirmation_code(length: int = 4) -> str:
    digits = "".join(str(secrets.randbelow(10)) for _ in range(length))
    if digits.startswith("0"):
        digits = str(secrets.randbelow(9) + 1) + digits[1:]
    return digits


def create_pending_confirmation(
    context,
    *,
    action: str,
    title: str,
    scope: str,
    ttl_seconds: int = DEFAULT_CONFIRM_TTL_SECONDS,
) -> dict:
    payload = {
        "action": action,
        "title": title,
        "scope": scope,
        "code": generate_confirmation_code(),
        "expires_at": int(time.time()) + ttl_seconds,
    }
    context.user_data[PENDING_CONFIRMATION_KEY] = payload
    return payload


def get_pending_confirmation(context) -> Optional[dict]:
    payload = context.user_data.get(PENDING_CONFIRMATION_KEY)
    if not payload:
        return None

    if int(time.time()) > int(payload.get("expires_at", 0)):
        clear_pending_confirmation(context)
        return None

    return payload


def has_pending_confirmation(context) -> bool:
    return get_pending_confirmation(context) is not None


def clear_pending_confirmation(context) -> None:
    context.user_data.pop(PENDING_CONFIRMATION_KEY, None)


def is_confirmation_code_valid(context, code: str) -> bool:
    payload = get_pending_confirmation(context)
    if not payload:
        return False
    return str(payload.get("code", "")).strip() == str(code).strip()


def get_confirmation_expire_seconds_left(context) -> int:
    payload = get_pending_confirmation(context)
    if not payload:
        return 0
    return max(0, int(payload["expires_at"]) - int(time.time()))