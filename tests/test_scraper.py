"""Tests for boardId probing (wydseoul.org list pages are pnp4web-encrypted since Oct 2026)."""

import requests

from monitor import scraper


class FakeResponse:
    def __init__(self, status_code: int):
        self.status_code = status_code


def _fake_get(existing: set[tuple[str, int]], failing: set[int] = frozenset()):
    """Build a requests.get stub: 200 for (category, id) in existing, 404 otherwise."""
    calls = []

    def fake_get(url, headers=None, timeout=None):
        calls.append(url)
        board_id = int(url.split("boardId=")[1])
        if board_id in failing:
            raise requests.ConnectionError("boom")
        category = url.split("/news/")[1].split("/")[0]
        return FakeResponse(200 if (category, board_id) in existing else 404)

    return fake_get, calls


def test_find_new_items_protected_list_page_detects_new_detail_page(monkeypatch):
    fake_get, _ = _fake_get({("notice", 1320)})
    monkeypatch.setattr(scraper.requests, "get", fake_get)
    monkeypatch.setattr(scraper.time, "sleep", lambda s: None)

    items = scraper.find_new_items(last_id=1316, window=10)

    assert [(i["category"], i["board_id"]) for i in items] == [("notice", "1320")]
    assert items[0]["url"] == "https://wydseoul.org/pt/news/notice/detail?boardId=1320"


def test_find_new_items_both_categories_returns_sorted_by_id(monkeypatch):
    fake_get, _ = _fake_get({("pressrelease", 1318), ("notice", 1317)})
    monkeypatch.setattr(scraper.requests, "get", fake_get)
    monkeypatch.setattr(scraper.time, "sleep", lambda s: None)

    items = scraper.find_new_items(last_id=1316, window=5)

    assert [(i["category"], i["board_id"]) for i in items] == [
        ("notice", "1317"),
        ("pressrelease", "1318"),
    ]


def test_find_new_items_probes_only_ids_inside_window(monkeypatch):
    fake_get, calls = _fake_get({("notice", 1330)})
    monkeypatch.setattr(scraper.requests, "get", fake_get)
    monkeypatch.setattr(scraper.time, "sleep", lambda s: None)

    items = scraper.find_new_items(last_id=1316, window=5)

    assert items == []
    probed = {int(u.split("boardId=")[1]) for u in calls}
    assert probed == {1317, 1318, 1319, 1320, 1321}


def test_find_new_items_network_error_skips_id_without_crashing(monkeypatch):
    fake_get, _ = _fake_get({("notice", 1318)}, failing={1317})
    monkeypatch.setattr(scraper.requests, "get", fake_get)
    monkeypatch.setattr(scraper.time, "sleep", lambda s: None)

    items = scraper.find_new_items(last_id=1316, window=3)

    assert [i["board_id"] for i in items] == ["1318"]
