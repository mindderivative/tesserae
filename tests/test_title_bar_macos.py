"""0.3.0 M3 Phase 4 (#52): macOS. There an undecorated window keeps its
title bar, transparent, with the traffic lights: `app.titlebar_inset`
says how much room they take and `app.native_controls` whether they
show. A TitleBar leaves that room at its start, and hides its own
buttons while the OS's show. Off macOS the inset is `(0, 0)`, so the
same app runs everywhere; here macOS is simulated.
"""

import sys

import pytest
import yaml

from tesserae import App, Signal, View, ViewModel

SEED = (0x67, 0x50, 0xA4, 0xFF)
BAR = {"id": "bar", "kind": "TitleBar", "title": "Notes", "style": {"width": 600}}


class MacWindow:
    """The app's window, answering `native_controls` as macOS would (it
    can't be simulated off a Mac); everything else is the real window."""

    def __init__(self, window):
        self._window = window

    def __getattr__(self, name):
        return getattr(self._window, name)

    def get(self, prop):
        return True if prop == "native_controls" else self._window.get(prop)


def _app_with(tmp_path):
    path = tmp_path / "Home_View.yaml"
    path.write_text(yaml.safe_dump({"id": "root", "kind": "Container", "style": {"width": 600, "height": 400},
                                    "children": [BAR]}), encoding="utf-8")
    app = App(width=600, height=400, theme_seed=SEED, decorations=False)
    view = app.build_view(path)
    app.register("Home", view, None)
    app.show("Home")
    ViewModel(view)
    app.window.advance(16)
    return app, view


@pytest.mark.skipif(sys.platform == "darwin", reason="on macOS the traffic lights show: the test below")
def test_the_inset_and_native_controls_off_macos(tmp_path):
    app, view = _app_with(tmp_path)
    assert app.titlebar_inset.get() == (0.0, 0.0) and app.native_controls.get() is False
    assert not hasattr(app.titlebar_inset, "set") and not hasattr(app.native_controls, "set")  # read-only
    assert view.node("bar.inset").get("layout_width") == 0.0
    assert view.node("bar.buttons").get("visible") is True


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS's own answer, on a Mac (CI's macOS job)")
def test_on_a_real_mac_the_traffic_lights_show_and_the_buttons_hide(tmp_path):
    app, view = _app_with(tmp_path)
    assert app.native_controls.get() is True  # tre's, for an undecorated window on macOS
    assert view.node("bar.buttons").get("visible") is False


def test_on_macos_the_bar_makes_room_and_its_buttons_hide(tmp_path, monkeypatch):
    app, view = _app_with(tmp_path)
    title_x = view.node("bar.title").get("layout_x")
    monkeypatch.setattr(app, "_window", MacWindow(app._window))
    app.window.simulate("titlebar_inset", height=28, width=78)  # the traffic lights, as macOS reports them
    app.window.advance(16)
    assert app.titlebar_inset.get() == (28.0, 78.0) and app.native_controls.get() is True
    assert view.node("bar.inset").get("layout_width") == 78.0
    assert view.node("bar.title").get("layout_x") == title_x + 78  # moved past them
    buttons = view.node("bar.buttons")
    assert buttons.get("visible") is False and buttons.get("layout_width") == 0.0  # out of layout, and clicks


def test_leaving_fullscreen_and_back(tmp_path, monkeypatch):
    """In fullscreen the traffic lights hide and the inset is (0, 0)."""
    app, view = _app_with(tmp_path)
    monkeypatch.setattr(app, "_window", MacWindow(app._window))
    app.window.simulate("titlebar_inset", height=28, width=78)
    app.window.simulate("titlebar_inset", height=0, width=0)
    app.window.advance(16)
    assert view.node("bar.inset").get("layout_width") == 0.0


def _box_bound_to(expression, vm_cls):
    view = View({"id": "root", "kind": "Container", "style": {"width": 200, "height": 100},
                 "children": [{"id": "box", "kind": "Rect", "bindings": {"visible": expression},
                               "style": {"width": 50, "height": 50, "background": "#6750A4"}}]})
    return view, vm_cls(view)


def test_visible_can_be_bound():
    class VM(ViewModel):
        def __init__(self, view):
            self.shown = Signal(True)
            super().__init__(view)

    view, vm = _box_bound_to("{{ shown.get() }}", VM)
    assert view.node("box").get("visible") is True
    vm.shown.set(False)
    assert view.node("box").get("visible") is False


def test_visible_takes_a_boolean():
    class VM(ViewModel):
        shown = "yes"

    with pytest.raises(ValueError, match='widget property "visible" expects a boolean binding'):
        _box_bound_to("{{ shown }}", VM)


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS's own answer, on a Mac (CI's macOS job)")
def test_on_a_real_mac_an_undecorated_window_has_no_drawn_border():
    """macOS keeps the window's frame, so Tesserae's border (M4) is never
    built there."""
    app = App(width=400, height=300, theme_seed=SEED, decorations=False)
    assert app._border is None
