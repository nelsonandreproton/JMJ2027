"""Tests for transient-error retries and source-unreachable detection."""

import pytest
import requests

from monitor import main, scraper
from monitor.state import State


class FakeResponse:
    def __init__(self, status_code: int):
        self.status_code = status_code


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(scraper.time, "sleep", lambda s: None)
    monkeypatch.setattr(scraper._exists.retry, "sleep", lambda s: None)


def test_exists_transient_error_retries_then_succeeds(monkeypatch):
    calls = []

    def flaky_get(url, headers=None, timeout=None):
        calls.append(url)
        if len(calls) == 1:
            raise requests.ConnectionError("dns hiccup")
        return FakeResponse(200)

    monkeypatch.setattr(scraper.requests, "get", flaky_get)

    items = scraper.find_new_items(last_id=1316, window=1)

    assert [i["board_id"] for i in items if i["category"] == "notice"] == ["1317"]
    assert len(calls) == 3  # notice: fail + retry, pressrelease: 1


def test_find_new_items_all_requests_fail_raises_source_unreachable(monkeypatch):
    def dead_get(url, headers=None, timeout=None):
        raise requests.ConnectionError("down")

    monkeypatch.setattr(scraper.requests, "get", dead_get)

    with pytest.raises(scraper.SourceUnreachable):
        scraper.find_new_items(last_id=1316, window=2)


class RecordingNotifier:
    def __init__(self):
        self.texts = []

    def send(self, text: str) -> bool:
        self.texts.append(text)
        return True


def test_check_new_news_source_unreachable_sends_telegram_alert(tmp_path, monkeypatch):
    def unreachable(last_id, window):
        raise scraper.SourceUnreachable("400/400 pedidos falharam")

    monkeypatch.setattr(main, "find_new_items", unreachable)
    notifier = RecordingNotifier()

    sent = main.check_new_news(State(str(tmp_path / "s.json")), notifier)

    assert sent == 0
    assert len(notifier.texts) == 1
    assert "wydseoul.org" in notifier.texts[0]
