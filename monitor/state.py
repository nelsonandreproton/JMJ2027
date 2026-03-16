import json
import logging
import os

logger = logging.getLogger(__name__)


def _empty() -> dict:
    return {
        "seen_ids": {},      # {category: [board_id, ...]}
        "weekly_news": [],   # items sent since last Sunday summary
        "last_daily": None,  # ISO date string of last daily check
        "last_weekly": None, # ISO date string of last Sunday summary
    }


def _load(path: str) -> dict:
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erro a carregar estado de {path}: {e}")
    return _empty()


def _save(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class State:
    def __init__(self, path: str):
        self._path = path
        self._data = _load(path)

    def is_seen(self, category: str, board_id: str) -> bool:
        return board_id in self._data["seen_ids"].get(category, [])

    def mark_seen(self, category: str, board_id: str, item: dict) -> None:
        self._data["seen_ids"].setdefault(category, [])
        if board_id not in self._data["seen_ids"][category]:
            self._data["seen_ids"][category].append(board_id)
        self._data["weekly_news"].append(item)
        _save(self._path, self._data)

    def get_weekly_news(self) -> list:
        return list(self._data["weekly_news"])

    def clear_weekly_news(self) -> None:
        self._data["weekly_news"] = []
        _save(self._path, self._data)

    def get_last_daily(self) -> str | None:
        return self._data.get("last_daily")

    def set_last_daily(self, date_str: str) -> None:
        self._data["last_daily"] = date_str
        _save(self._path, self._data)

    def get_last_weekly(self) -> str | None:
        return self._data.get("last_weekly")

    def set_last_weekly(self, date_str: str) -> None:
        self._data["last_weekly"] = date_str
        _save(self._path, self._data)
