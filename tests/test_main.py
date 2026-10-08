"""Tests for the daily check flow, state baseline, and message formatting."""

import json
from datetime import date

from monitor import main
from monitor.state import State
from monitor.telegram import TelegramNotifier


class RecordingNotifier:
    def __init__(self):
        self.items = []

    def send_new_item(self, item: dict) -> bool:
        self.items.append(item)
        return True


def _state_with(tmp_path, seen_ids: dict) -> State:
    path = tmp_path / "state.json"
    path.write_text(json.dumps({
        "seen_ids": seen_ids, "weekly_news": [], "last_daily": None, "last_weekly": None,
    }))
    return State(str(path))


def test_get_last_id_empty_state_returns_default(tmp_path):
    state = State(str(tmp_path / "missing.json"))
    assert state.get_last_id(default=1316) == 1316


def test_get_last_id_mixed_categories_returns_global_max(tmp_path):
    state = _state_with(tmp_path, {"notice": ["1153", "1316"], "pressrelease": ["1320"]})
    assert state.get_last_id(default=0) == 1320


def test_check_new_news_new_item_notifies_marks_seen_and_queues_weekly(tmp_path, monkeypatch):
    state = _state_with(tmp_path, {"notice": ["1316"]})
    probed = {}

    def fake_find(last_id, window):
        probed["last_id"] = last_id
        return [{"board_id": "1317", "category": "notice", "url": "u"}]

    monkeypatch.setattr(main, "find_new_items", fake_find)
    notifier = RecordingNotifier()

    sent = main.check_new_news(state, notifier)

    assert sent == 1
    assert probed["last_id"] == 1316
    assert notifier.items[0]["board_id"] == "1317"
    assert notifier.items[0]["date"]  # detection date filled in
    assert state.is_seen("notice", "1317")
    assert len(state.get_weekly_news()) == 1
    assert state.get_last_id(default=0) == 1317


def test_check_new_news_already_seen_item_not_resent(tmp_path, monkeypatch):
    state = _state_with(tmp_path, {"notice": ["1316", "1317"], "pressrelease": []})
    monkeypatch.setattr(
        main, "find_new_items",
        lambda last_id, window: [{"board_id": "1317", "category": "notice", "url": "u"}],
    )
    notifier = RecordingNotifier()

    assert main.check_new_news(state, notifier) == 0
    assert notifier.items == []


def test_send_new_item_uses_label_and_id_as_link_text(monkeypatch):
    notifier = TelegramNotifier("token", "chat")
    sent = []
    monkeypatch.setattr(notifier, "send", lambda text: sent.append(text) or True)

    notifier.send_new_item({
        "board_id": "1317", "category": "pressrelease",
        "url": "https://wydseoul.org/pt/news/pressrelease/detail?boardId=1317",
        "date": "08/10/2026",
    })

    assert '">Notícia #1317</a>' in sent[0]
    assert "Notícias da JMJ" in sent[0]


def test_send_weekly_summary_lists_items_as_links(monkeypatch):
    notifier = TelegramNotifier("token", "chat")
    sent = []
    monkeypatch.setattr(notifier, "send", lambda text: sent.append(text) or True)

    notifier.send_weekly_summary(
        [{"board_id": "1317", "category": "notice", "url": "u1", "date": "08/10/2026"}],
        date(2026, 10, 5), date(2026, 10, 11),
    )

    assert '<a href="u1">Aviso #1317</a> — 08/10/2026' in sent[0]
