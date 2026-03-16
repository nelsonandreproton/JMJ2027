import logging
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE_URL = "https://wydseoul.org"

URLS = {
    "notice": f"{BASE_URL}/pt/news/notice",
    "pressrelease": f"{BASE_URL}/pt/news/pressrelease",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; JMJ2027Bot/1.0)",
    "Accept-Language": "pt-PT,pt;q=0.9",
}


def _extract_board_id(href: str) -> str | None:
    m = re.search(r"boardId=(\d+)", href)
    return m.group(1) if m else None


def fetch_news(category: str) -> list[dict]:
    """Fetch news items for the given category.

    Returns a list of dicts with keys: board_id, title, date, url, category.
    Returns an empty list on error.
    """
    url = URLS[category]
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        logger.error(f"Erro ao obter {url}: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    items = []

    for li in soup.select(".board-item"):
        a = li.select_one("a.board-item__link")
        title_el = li.select_one(".board-item__title-text")
        date_el = li.select_one(".board-item__date")

        if not a or not title_el or not date_el:
            continue

        href = a.get("href", "")
        board_id = _extract_board_id(href)
        if not board_id:
            continue

        items.append({
            "board_id": board_id,
            "title": title_el.get_text(strip=True),
            "date": date_el.get_text(strip=True),
            "url": urljoin(BASE_URL, href),
            "category": category,
        })

    if not items:
        logger.warning(
            f"[{category}] 0 itens encontrados — o site pode requerer JavaScript. "
            f"Verificar manualmente: {url}"
        )
    else:
        logger.info(f"[{category}] {len(items)} itens encontrados")

    return items
