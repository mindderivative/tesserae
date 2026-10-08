"""0.3.0 M4 Phase 4 (#57): title bars hot-reload like anything else. An
edit to a view with a `TitleBar` (its title, its buttons, its content)
reloads it, and its buttons still act.
"""

import os

import pytest
import yaml

from tesserae import App, ViewModel
from tesserae.spec.watch import ViewWatcher

SEED = (0x67, 0x50, 0xA4, 0xFF)


def _page(**bar):
    return {"id": "root", "kind": "Container", "style": {"width": 600, "height": 400, "flex_direction": "vertical"},
            "children": [{"id": "bar", "kind": "TitleBar", "style": {"width": 600}, **bar}]}


def _write(path, spec):
    before = path.stat().st_mtime_ns if path.exists() else 0
    path.write_text(yaml.safe_dump(spec), encoding="utf-8")
    later = max(before + 10**9, path.stat().st_mtime_ns)
    os.utime(path, ns=(later, later))  # a change a watcher sees, however fast the test


def _app_with(tmp_path, spec):
    path = tmp_path / "Home_View.yaml"
    _write(path, spec)
    app = App(width=600, height=400, theme_seed=SEED, borderless=True)
    app._native_controls.set(False)  # the bar as Windows and Linux show it
    view = app.build_view(path)
    app.register("Home", view, None)
    app.show("Home")
    ViewModel(view)
    app.window.advance(16)
    return app, view, path


def test_editing_a_title_bar_reloads_it(tmp_path, monkeypatch):
    app, view, path = _app_with(tmp_path, _page(title="Notes"))
    watcher = ViewWatcher(view, path)
    _write(path, _page(title="Notes, edited", icon="home",
                       children=[{"id": "tag", "kind": "Rect",
                                  "style": {"width": 40, "height": 20, "background": "primary"}}]))
    assert watcher.poll() is True
    app.window.advance(16)
    assert view.node("bar.title").get("text") == "Notes, edited"
    assert view.node("bar.icon") is not None and view.node("tag") is not None
    closed = []
    monkeypatch.setattr(app, "close", lambda: closed.append(True))
    app.window.simulate("click", node=view.node("bar.close"))  # the reloaded button still acts
    assert closed == [True]
    app.window.simulate("maximized", maximized=True)  # and still follows the window
    assert view.node("bar.maximize.window_restore").get("opacity") == 1.0


def test_dropping_buttons_by_hot_reload(tmp_path):
    app, view, path = _app_with(tmp_path, _page(title="Notes"))
    watcher = ViewWatcher(view, path)
    _write(path, _page(title="Notes", buttons=["close"]))
    assert watcher.poll() is True
    app.window.advance(16)
    assert view.node("bar.close").get("layout_x") + 46 == 600  # still at the right edge, alone
    with pytest.raises(ValueError, match="no widget with id 'bar.minimize'"):
        view.node("bar.minimize")  # gone, not just hidden
