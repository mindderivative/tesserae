"""Tesserae's logging through loguru (`tesserae.log`).

Tesserae logs with loguru's shared `logger` and adds no output of its
own; `configure_logging()` is an app's one-call console setup.
"""

import importlib.util
import io
import os
import sys
import warnings
from pathlib import Path

import pytest
from loguru import logger

import tesserae.fonts as fonts
from tesserae import App, configure_logging
from tesserae.fonts import FontFallbackWarning, check_font_families
from tesserae.spec import ViewWatcher, load_view

RECT = 'id: box\nkind: Rect\nstyle: {width: 10, height: 10, background: "#112233"}\n'


@pytest.fixture
def configured(monkeypatch):
    """`configure_logging` into a buffer; undone afterwards."""
    monkeypatch.setattr(warnings, "showwarning", warnings.showwarning)
    ids = []

    def configure(**kwargs):
        buffer = io.StringIO()
        ids.append(configure_logging(sink=buffer, **kwargs))
        return buffer

    yield configure
    for handler_id in ids:
        logger.remove(handler_id)


def _reload_once(tmp_path: Path) -> Path:
    path = tmp_path / "Home_View.yaml"
    path.write_text(RECT)
    watcher = ViewWatcher(load_view(path), path)
    path.write_text(RECT.replace("10, height: 10", "12, height: 12"))
    stat = path.stat()
    os.utime(path, ns=(stat.st_mtime_ns + 10**9, stat.st_mtime_ns + 10**9))
    assert watcher.poll() is True
    return path


def test_configure_logging_writes_tesserae_messages_in_its_format(tmp_path: Path, configured):
    buffer = configured()
    path = _reload_once(tmp_path)
    line = next(l for l in buffer.getvalue().splitlines() if "reloaded" in l)
    assert f"| INFO     | tesserae.spec.watch - reloaded {path}" in line


def test_the_level_filters(tmp_path: Path, configured):
    buffer = configured(level="WARNING")
    _reload_once(tmp_path)
    assert "reloaded" not in buffer.getvalue()


def test_an_app_can_silence_tesserae(tmp_path: Path, configured):
    buffer = configured()
    logger.disable("tesserae")
    try:
        _reload_once(tmp_path)
    finally:
        logger.enable("tesserae")
    assert "reloaded" not in buffer.getvalue()


def test_warnings_show_through_loguru_and_still_can_be_errors(configured, monkeypatch):
    monkeypatch.setattr(fonts, "_registered", set())
    buffer = configured()
    with warnings.catch_warnings():
        warnings.simplefilter("always")
        check_font_families(["Inter"], "brand.yaml")
    assert "WARNING  |" in buffer.getvalue()
    assert "FontFallbackWarning: brand.yaml: font_family 'Inter'" in buffer.getvalue()

    with warnings.catch_warnings():
        warnings.simplefilter("error", FontFallbackWarning)
        with pytest.raises(FontFallbackWarning):
            check_font_families(["Inter"], "brand.yaml")


def test_capture_warnings_can_be_turned_off(configured):
    before = warnings.showwarning
    configured(capture_warnings=False)
    assert warnings.showwarning is before


def test_run_with_hot_reload_says_what_it_watches(tmp_path: Path, logs):
    (tmp_path / "Home_View.yaml").write_text(RECT)
    vm = tmp_path / "Home_ViewModel.py"
    vm.write_text("from tesserae import ViewModel\n\n\nclass HomeViewModel(ViewModel):\n    pass\n")
    spec = importlib.util.spec_from_file_location(vm.stem, vm)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    sheet = tmp_path / "default.yaml"
    sheet.write_text("styles: []\n")

    app = App(stylesheet=sheet)
    app.load(tmp_path / "Home_View.yaml", module.HomeViewModel)

    class Handle:
        def call_soon(self, fn):
            pass

    watchers = app._start_watchers(Handle())
    try:
        assert "hot reload on: watching 1 screen(s) and 1 theme/stylesheet file(s)" in logs.messages("INFO")
    finally:
        for watcher in watchers:
            watcher.stop()
