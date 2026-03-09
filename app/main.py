import logging

from app.config import validate_config
from app.services.memory_service import ensure_dirs
from app.bot_app import create_bot_app

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main() -> None:
    validate_config()
    ensure_dirs()

    app = create_bot_app()

    logger.info("Bot started")
    app.run_polling()


if __name__ == "__main__":
    main()
