import logging
import os
import sys

logger = logging.getLogger(__name__)

DEFAULT_STATE_PATH = "/app/data/state.json"


def load_config() -> dict:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")

    if not token or not chat_id:
        logger.error(
            "TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID são obrigatórios. "
            "Define-os no ficheiro .env."
        )
        sys.exit(1)

    return {
        "telegram_token": token,
        "telegram_chat_id": chat_id,
        "state_path": os.environ.get("STATE_PATH", DEFAULT_STATE_PATH),
    }
