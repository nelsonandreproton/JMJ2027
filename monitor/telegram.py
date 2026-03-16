import logging
from datetime import date

import requests

logger = logging.getLogger(__name__)

CATEGORY_LABEL = {
    "notice": "Avisos",
    "pressrelease": "Notícias da JMJ",
}


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str):
        self._chat_id = chat_id
        self._url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    def send(self, text: str) -> bool:
        try:
            resp = requests.post(
                self._url,
                json={
                    "chat_id": self._chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                },
                timeout=10,
            )
            if not resp.ok:
                logger.error(
                    f"Erro Telegram: {resp.status_code} — "
                    f"{resp.json().get('description', resp.text)}"
                )
                return False
            return True
        except Exception as e:
            logger.error(f"Erro Telegram: {e}")
            return False

    def send_new_item(self, item: dict) -> bool:
        label = CATEGORY_LABEL.get(item["category"], item["category"])
        text = (
            f"🔔 <b>Nova notícia JMJ Seul 2027</b>\n\n"
            f"📂 {label}\n"
            f"📰 <a href=\"{item['url']}\">{item['title']}</a>\n"
            f"📅 {item['date']}"
        )
        return self.send(text)

    def send_weekly_summary(self, items: list[dict], week_start: date, week_end: date) -> bool:
        n = len(items)
        header = (
            f"📋 <b>Resumo Semanal JMJ Seul 2027</b>\n"
            f"Semana de {week_start.strftime('%d/%m')} a {week_end.strftime('%d/%m/%Y')}\n\n"
            f"{n} notícia{'s' if n != 1 else ''} esta semana:"
        )

        # Group by category preserving order: notice first, then pressrelease
        by_cat: dict[str, list] = {}
        for item in items:
            by_cat.setdefault(item["category"], []).append(item)

        lines = [header]
        for cat in ("notice", "pressrelease"):
            cat_items = by_cat.get(cat, [])
            if not cat_items:
                continue
            label = CATEGORY_LABEL.get(cat, cat)
            lines.append(f"\n📂 <b>{label}</b>")
            for item in cat_items:
                lines.append(
                    f"• <a href=\"{item['url']}\">{item['title']}</a> — {item['date']}"
                )

        return self.send("\n".join(lines))
