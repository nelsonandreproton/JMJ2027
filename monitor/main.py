import logging
import sys
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from .config import load_config
from .scraper import fetch_news
from .state import State
from .telegram import TelegramNotifier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

TZ = ZoneInfo("Europe/Lisbon")
CATEGORIES = ["notice", "pressrelease"]

# Check every 60s — lightweight, just datetime comparisons until trigger time
SLEEP_SECONDS = 60


def now_local() -> datetime:
    return datetime.now(tz=TZ)


def check_new_news(state: State, notifier: TelegramNotifier) -> int:
    """Scrape both URLs and notify for each new item. Returns count sent."""
    sent = 0
    for category in CATEGORIES:
        items = fetch_news(category)
        for item in items:
            if not state.is_seen(category, item["board_id"]):
                logger.info(
                    f"Nova notícia [{category}] #{item['board_id']}: {item['title']}"
                )
                notifier.send_new_item(item)
                state.mark_seen(category, item["board_id"], item)
                sent += 1
    return sent


def do_weekly_summary(state: State, notifier: TelegramNotifier) -> None:
    weekly = state.get_weekly_news()
    if not weekly:
        logger.info("Resumo semanal: sem notícias esta semana, nada a enviar.")
        return

    now = now_local()
    week_end = now.date()
    week_start = week_end - timedelta(days=6)

    logger.info(f"A enviar resumo semanal com {len(weekly)} itens.")
    notifier.send_weekly_summary(weekly, week_start, week_end)
    state.clear_weekly_news()


def run() -> None:
    config = load_config()
    state = State(config["state_path"])
    notifier = TelegramNotifier(config["telegram_token"], config["telegram_chat_id"])

    logger.info("JMJ2027 Bot iniciado.")
    notifier.send("✅ <b>JMJ2027 Bot iniciado</b>\nA monitorizar notícias de wydseoul.org.")

    last_daily: str | None = state.get_last_daily()
    last_weekly: str | None = state.get_last_weekly()

    while True:
        try:
            now = now_local()
            today = now.date().isoformat()

            # Daily check at 10:00 Lisbon time
            if now.hour >= 10 and last_daily != today:
                logger.info("Verificação diária de notícias...")
                count = check_new_news(state, notifier)
                logger.info(f"Verificação concluída — {count} novas notícias enviadas.")
                last_daily = today
                state.set_last_daily(today)

            # Weekly summary on Sunday (weekday==6) at 12:00 Lisbon time
            if now.weekday() == 6 and now.hour >= 12 and last_weekly != today:
                do_weekly_summary(state, notifier)
                last_weekly = today
                state.set_last_weekly(today)

        except Exception as e:
            logger.error(f"Erro no ciclo principal: {e}", exc_info=True)

        time.sleep(SLEEP_SECONDS)


if __name__ == "__main__":
    run()
