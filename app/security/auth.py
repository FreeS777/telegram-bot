from telegram import Update
from app.config import get_allowed_user_id


def is_allowed(update: Update) -> bool:
    user = update.effective_user
    return bool(user and user.id == get_allowed_user_id())
