"""Detect new wydseoul.org news by probing detail-page boardIds.

Since Oct 2026 the site serves list and detail pages encrypted by pnp4web
(decrypted client-side by obfuscated JS), so list pages can no longer be
parsed. Detail URLs still answer 200 when an item exists and 404 otherwise,
which is enough to detect new items — but not their titles.
"""

import logging
import time

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://wydseoul.org"
CATEGORIES = ("notice", "pressrelease")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; JMJ2027Bot/1.0)",
    "Accept-Language": "pt-PT,pt;q=0.9",
}

# Delay between requests — keeps the daily probe polite.
REQUEST_DELAY_SECONDS = 0.3


def detail_url(category: str, board_id: int | str) -> str:
    return f"{BASE_URL}/pt/news/{category}/detail?boardId={board_id}"


def _exists(category: str, board_id: int) -> bool:
    """True if the detail page exists (HTTP 200). Network errors count as not found."""
    url = detail_url(category, board_id)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
    except requests.RequestException as e:
        logger.error(f"Erro ao obter {url}: {e}")
        return False
    if resp.status_code not in (200, 404):
        logger.warning(f"[{category}] #{board_id}: HTTP {resp.status_code} inesperado")
    return resp.status_code == 200


def find_new_items(last_id: int, window: int) -> list[dict]:
    """Probe boardIds last_id+1 .. last_id+window in every category.

    boardIds are shared across the site's boards, so new items in these two
    categories can appear anywhere after the last seen id.
    Returns items (board_id, category, url) sorted by board_id.
    """
    items = []
    for board_id in range(last_id + 1, last_id + window + 1):
        for category in CATEGORIES:
            if _exists(category, board_id):
                items.append({
                    "board_id": str(board_id),
                    "category": category,
                    "url": detail_url(category, board_id),
                })
            time.sleep(REQUEST_DELAY_SECONDS)

    logger.info(f"Sondagem #{last_id + 1}–#{last_id + window}: {len(items)} novos itens")
    return items
