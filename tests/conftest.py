"""Shared fixtures."""

import threading
import time

import pytest
from loguru import logger


class LogRecords:
    """Every loguru record at DEBUG and above while a test runs, as
    `(level, message)` pairs. Watcher threads log too, so it's locked."""

    def __init__(self):
        self._lock = threading.Lock()
        self._records: list[tuple[str, str]] = []

    def sink(self, message):
        record = message.record
        with self._lock:
            self._records.append((record["level"].name, record["message"]))

    @property
    def records(self) -> list[tuple[str, str]]:
        with self._lock:
            return list(self._records)

    def messages(self, level: str) -> list[str]:
        return [m for lvl, m in self.records if lvl == level]

    def clear(self) -> None:
        with self._lock:
            self._records.clear()

    def edit_until(self, path, text: str, level: str, contains: str, attempts: int = 40) -> str:
        """Writes `text` to `path` until a `level` record containing
        `contains` is logged -- a background watcher can miss an edit made
        before it started listening."""
        for _ in range(attempts):
            path.write_text(text)
            try:
                return self.wait_for(level, contains, timeout=0.25)
            except AssertionError:
                continue
        raise AssertionError(f"no {level} log containing {contains!r} after editing {path}; got {self.records}")

    def wait_for(self, level: str, contains: str, timeout: float = 5.0) -> str:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            for message in self.messages(level):
                if contains in message:
                    return message
            time.sleep(0.02)
        raise AssertionError(f"no {level} log containing {contains!r}; got {self.records}")


@pytest.fixture
def logs():
    captured = LogRecords()
    handler_id = logger.add(captured.sink, level="DEBUG", format="{message}")
    yield captured
    logger.remove(handler_id)
