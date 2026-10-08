"""Detect new wydseoul.org news by probing detail-page boardIds.

Since Oct 2026 the site serves list and detail pages encrypted by pnp4web
(decrypted client-side by obfuscated JS), so list pages can no longer be
parsed. Detail URLs still answer 200 when an item exists and 404 otherwise,
which is enough to detect new items — but not their titles.
"""

import logging
import time

import requests
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

BASE_URL = "https://wydseoul.org"
CATEGORIES = ("notice", "pressrelease")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; JMJ2027Bot/1.0)",
    "Accept-Language": "pt-PT,pt;q=0.9",
}

# Delay between requests — keeps the daily probe polite.
REQUEST_DELAY_SECONDS = 0.3


class SourceUnreachable(Exception):
    """Every probe request failed — the site is down or blocking us."""


def detail_url(category: str, board_id: int | str) -> str:
    return f"{BASE_URL}/pt/news/{category}/detail?boardId={board_id}"


@retry(
    retry=retry_if_exception_type(requests.RequestException),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, max=10),
    reraise=True,
)
def _exists(category: str, board_id: int) -> bool:
    """True if the detail page exists (HTTP 200). Retries network errors, then raises."""
    resp = requests.get(detail_url(category, board_id), headers=HEADERS, timeout=15)
    if resp.status_code not in (200, 404):
        logger.warning(f"[{category}] #{board_id}: HTTP {resp.status_code} inesperado")
    return resp.status_code == 200


def find_new_items(last_id: int, window: int) -> list[dict]:
    """Probe boardIds last_id+1 .. last_id+window in every category.

    boardIds are shared across the site's boards, so new items in these two
    categories can appear anywhere after the last seen id.
    Returns items (board_id, category, url) sorted by board_id.
    Raises SourceUnreachable if every request failed.
    """
    items = []
    failures = 0
    for board_id in range(last_id + 1, last_id + window + 1):
        for category in CATEGORIES:
            try:
                found = _exists(category, board_id)
            except requests.RequestException as e:
                logger.error(f"Erro ao obter {detail_url(category, board_id)}: {e}")
                failures += 1
                found = False
            if found:
                items.append({
                    "board_id": str(board_id),
                    "category": category,
                    "url": detail_url(category, board_id),
                })
            time.sleep(REQUEST_DELAY_SECONDS)

    total = window * len(CATEGORIES)
    if failures == total:
        raise SourceUnreachable(f"{failures}/{total} pedidos falharam")
    logger.info(f"Sondagem #{last_id + 1}–#{last_id + window}: {len(items)} novos itens")
    return items
