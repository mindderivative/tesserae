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


# -- M43: tre's recorded answers (tests/reference.py) -----------------------

import reference  # noqa: E402


@pytest.fixture(autouse=True)
def _tre_reference(request):
    """Keys `reference.tre()` answers by the running test."""
    reference.begin(request.module.__name__, request.node.name)
    yield


def pytest_sessionfinish(session, exitstatus):
    """Recording: saved only if every test passed, so a mismatch is never
    written in as `tre`'s answer."""
    if reference.RECORDING and exitstatus == 0:
        reference.STORE.save()


@pytest.fixture(autouse=True)
def os_appearance(monkeypatch):
    """The OS's light/dark appearance, as `App(dark="system")` reads it
    (M53): unknown (`None`) by default, so an app starts dark whatever the
    desktop running the tests uses. A test sets `os_appearance.dark`."""
    import tesserae.app

    class Appearance:
        dark = None

    appearance = Appearance()
    monkeypatch.setattr(tesserae.app, "_os_dark", lambda window: appearance.dark)
    return appearance


@pytest.fixture(autouse=True)
def _the_os_does_not_ask_for_reduced_motion(monkeypatch):
    """An `App` that follows the OS (the default) would read reduced motion from the machine running the tests: GitHub's Windows and macOS
    runners ask for it, so every animation finished at once and the tests that watch one in progress failed. A test that cares passes
    `reduced_motion=True` or `False` itself; `test_os_preferences.py` drives the OS events directly."""
    from tesserae.app import App

    wanted = App._wanted

    def not_reduced(self, name, mode):
        return False if (name == "reduced_motion" and mode == "system") else wanted(self, name, mode)

    monkeypatch.setattr(App, "_wanted", not_reduced)
