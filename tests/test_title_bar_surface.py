"""0.4.4 (#97): a `TitleBar` in a dialog or a sheet (`buttons: [dismiss]`), `surface.dismiss`, and `ViewDialog`; and a
static view's `window.*` and `surface.*` handlers, which need no ViewModel."""

import sys

import pytest
import yaml

from tesserae import App, View
from tesserae.overlays import Dialog, ViewDialog, dismiss_surface
from tesserae.spec.title_bar import TitleBarError, expand_title_bars

SEED = (0x67, 0x50, 0xA4, 0xFF)
SETTINGS = """
id: root
kind: Container
style: {flex_direction: vertical, width: 100%, height: 100%}
children:
  - {id: bar, kind: TitleBar, title: Settings, icon: settings, buttons: [dismiss]}
  - {id: body, kind: Text, text: {content: "Hello", typography_role: body_large}, style: {foreground: on_surface}}
"""
FORM = """
id: root
kind: Container
style: {flex_direction: vertical, width: 100%, height: 100%}
children:
  - {id: bar, kind: TitleBar, title: Form, buttons: [dismiss]}
  - {id: name, kind: Text, text: {content: "", typography_role: body_large}, style: {foreground: on_surface}, bindings: {text: "{{ shown.get() }}"}}
"""
FORM_VM = """
from tesserae import Signal, ViewModel


class {name}ViewModel(ViewModel):
    def __init__(self, view, who="nobody"):
        self.shown = Signal(f"hello {{who}}")
        super().__init__(view)
"""


def _app():
    app = App(width=600, height=400, theme_seed=SEED, dark=True)
    app.window.advance(16)
    return app


# -- the bar -----------------------------------------------------------------------------------

def test_a_dismiss_bar_has_no_window_parts():
    spec = expand_title_bars({"id": "bar", "kind": "TitleBar", "title": "Settings", "buttons": ["dismiss"]})
    ids = []

    def walk(n):
        ids.append(n["id"])
        for c in n.get("children") or []:
            walk(c)

    walk(spec)
    assert spec["window_region"] == "none"
    assert "bar.dismiss" in ids and "bar.inset" not in ids and "bar.minimize" not in ids
    button = next(c for c in spec["children"][-1]["children"])
    assert button["handlers"] == {"on_click": "surface.dismiss"} and button["a11y"] == {"label": "Close"}
    assert "bindings" not in next(c for c in spec["children"] if c["id"] == "bar.title")  # it fades for a window, not a dialog


def test_a_window_bar_is_as_it_was():
    spec = expand_title_bars({"id": "bar", "kind": "TitleBar", "title": "T"})
    assert spec["window_region"] == "drag" and spec["children"][0]["id"] == "bar.inset"


@pytest.mark.parametrize("buttons", [["dismiss", "close"], ["minimize", "dismiss"], ["dismiss", "dismiss"]])
def test_dismiss_is_on_its_own(buttons):
    with pytest.raises(TitleBarError, match="on its own"):
        expand_title_bars({"id": "bar", "kind": "TitleBar", "buttons": buttons})


# -- a dialog with a view ---------------------------------------------------------------------

def test_a_view_dialog_shows_a_static_view_and_its_dismiss_button_closes_it(tmp_path):
    (tmp_path / "Settings_View.yaml").write_text(SETTINGS)
    app = _app()
    dialog = ViewDialog(app.window, tmp_path / "Settings_View.yaml", width=320, height=200)
    closed = []
    dialog.on_close(lambda: closed.append(True))
    dialog.open()
    app.window.advance(16)
    assert dialog.is_open and dialog.viewmodel is None
    assert dialog.content.node("body").get("text") == "Hello"
    app.window.simulate("click", dialog.content.node("bar.dismiss"))
    app.window.advance(16)
    assert not dialog.is_open and closed == [True]


def test_a_view_dialog_gets_its_viewmodel_and_arguments(tmp_path):
    name = f"Form{abs(hash(str(tmp_path))) % 10**8}"
    (tmp_path / f"{name}_View.yaml").write_text(FORM)
    (tmp_path / f"{name}_ViewModel.py").write_text(FORM_VM.format(name=name))
    sys.path.insert(0, str(tmp_path))
    try:
        app = _app()
        dialog = ViewDialog(app.window, tmp_path / f"{name}_View.yaml", arguments={"who": "Ada"})
        dialog.open()
        app.window.advance(16)
        assert dialog.content.node("name").get("text") == "hello Ada"
        app.window.simulate("click", dialog.content.node("bar.dismiss"))
        assert not dialog.is_open
    finally:
        sys.path.remove(str(tmp_path))
        sys.modules.pop(f"{name}_ViewModel", None)


def test_a_view_dialog_follows_the_apps_theme(tmp_path):
    (tmp_path / "Settings_View.yaml").write_text(SETTINGS)
    app = _app()
    dialog = ViewDialog(app.window, tmp_path / "Settings_View.yaml")
    dialog.open()
    app.window.advance(16)
    before = dialog.content.node("body").get("fill")
    app.set_dark(False)
    app.window.advance(16)
    assert dialog.content.node("body").get("fill") != before


def test_a_view_dialog_by_name_in_a_project(tmp_path):
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Settings_View.yaml").write_text(SETTINGS)
    app = App(width=600, height=400, theme_seed=SEED, root=tmp_path)
    dialog = ViewDialog(app.window, "Settings")
    dialog.open()
    assert dialog.content.node("body").get("text") == "Hello"


def test_escape_still_closes_it(tmp_path):
    (tmp_path / "Settings_View.yaml").write_text(SETTINGS)
    app = _app()
    dialog = ViewDialog(app.window, tmp_path / "Settings_View.yaml")
    dialog.open()
    app.window.simulate("key_down", key="escape")
    app.window.advance(16)
    assert not dialog.is_open


def test_dismiss_surface_closes_the_nearest_overlay_and_says_if_there_was_none():
    app = _app()
    dialog = Dialog(app.window, "Sure?", "Really.", actions=[("OK", None)])
    dialog.open()
    assert dismiss_surface(dialog.widget.part("panel.action0")) is True and not dialog.is_open
    lone = app.window.create("box", width=10, height=10)
    app.window.root.add_child(lone)
    assert dismiss_surface(lone) is False


# -- handlers that need no ViewModel -------------------------------------------------------------

def test_a_static_views_surface_handler_works_with_no_viewmodel():
    app = _app()
    spec = yaml.safe_load("""
id: root
kind: Container
children:
  - {id: x, kind: Rect, style: {width: 20, height: 20, background: primary}, handlers: {on_click: surface.dismiss}}
""")
    view = View(spec, window=app.window)
    assert view.viewmodel is None and view._wiring  # wired without one


def test_a_static_views_window_button_works_with_no_viewmodel(monkeypatch):
    app = _app()
    closed = []
    monkeypatch.setattr(app, "close", lambda: closed.append(True))
    spec = yaml.safe_load("""
id: root
kind: Container
children:
  - {id: x, kind: Rect, style: {width: 20, height: 20, background: primary}, handlers: {on_click: window.close}}
""")
    view = View(spec, window=app.window)
    app.window.root.add_child(view.root)
    app.window.advance(16)
    app.window.simulate("click", view.node("x"))
    assert closed == [True]


def test_an_unknown_surface_action_is_one_line_when_a_viewmodel_attaches():
    from tesserae import ViewModel

    view = View(yaml.safe_load("""
id: root
kind: Container
children:
  - {id: x, kind: Rect, style: {width: 20, height: 20, background: primary}, handlers: {on_click: surface.explode}}
"""))
    with pytest.raises(ValueError, match=r'widget "x": handler "on_click" names "surface.explode", which isn\'t a surface action'):
        ViewModel(view)
