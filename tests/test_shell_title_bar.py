"""0.3.0 M4 Phase 1 (#54): an app shell's top bar is the title bar of an
undecorated window: the window's drag region, with the window buttons
after its trailing icons, the maximize swap, the fade while unfocused,
and (on macOS) room for the traffic lights. From code and from a shell
file; a decorated app's top bar is as it was.
"""

import pytest
import yaml

from tesserae import App, View
from tesserae.widgets.navigation import top_app_bar

SEED = (0x67, 0x50, 0xA4, 0xFF)


def _app(**kwargs):
    app = App(width=800, height=500, theme_seed=SEED, **kwargs)
    app._native_controls.set(False)  # the bar as Windows and Linux show it (macOS: below)
    return app


def _bar(app, **kwargs):
    bar = top_app_bar(app.window, "Studio", leading_icon="menu", trailing_icons=["settings"], width=800, **kwargs)
    app.window.root.add_child(bar.node)
    app.window.advance(16)
    return bar


def test_an_undecorated_apps_top_bar_is_the_title_bar():
    app = _app(decorations=False)
    bar = _bar(app)
    node = bar.view.node
    assert bar.node.get("window_region") == "drag"
    ids = [c["id"] for c in bar.spec["children"]]
    assert ids == ["top_app_bar.inset", "top_app_bar.leading", "top_app_bar.title", "top_app_bar.trailing0",
                   "top_app_bar.buttons"]  # the window buttons after the trailing icons
    assert node("top_app_bar.buttons").get("layout_x") >= node("top_app_bar.trailing0").get("layout_x") + 48
    assert [n["id"] for n in bar.spec["children"][-1]["children"]] == [
        "top_app_bar.minimize", "top_app_bar.maximize", "top_app_bar.close"]


def test_its_buttons_act_and_it_follows_the_window(monkeypatch):
    app = _app(decorations=False)
    bar = _bar(app)
    node = bar.view.node
    app.window.simulate("click", node=node("top_app_bar.maximize"))
    assert app.maximized.get() is True and node("top_app_bar.maximize.window_restore").get("opacity") == 1.0
    closed = []
    monkeypatch.setattr(app, "close", lambda: closed.append(True))
    app.window.simulate("click", node=node("top_app_bar.close"))
    assert closed == [True]
    assert node("top_app_bar.title").get("opacity") == 0.6  # unfocused before it opens
    app.window.simulate("active", active=True)
    assert node("top_app_bar.title").get("opacity") == 1.0 and node("top_app_bar.buttons").get("opacity") == 1.0


def test_its_own_buttons_still_work():
    app = _app(decorations=False)
    bar = _bar(app)
    clicked = []
    bar.on_click(lambda: clicked.append("menu"), part="leading")
    app.window.simulate("click", node=bar.view.node("top_app_bar.leading"))
    assert clicked == ["menu"]


def test_on_macos_it_makes_room_and_hides_its_buttons():
    app = _app(decorations=False)
    bar = _bar(app)
    app._native_controls.set(True)  # as tre reports it on a Mac
    app._titlebar_inset.set((28.0, 78.0))
    app.window.advance(16)
    node = bar.view.node
    assert node("top_app_bar.inset").get("layout_width") == 78.0
    assert node("top_app_bar.buttons").get("visible") is False


def test_a_decorated_apps_top_bar_is_as_it_was():
    app = _app()
    bar = _bar(app)
    assert bar.node.get("window_region") is None
    assert [c["id"] for c in bar.spec["children"]] == ["top_app_bar.leading", "top_app_bar.title",
                                                       "top_app_bar.trailing0"]


def test_window_controls_can_be_asked_for_or_refused():
    assert _bar(_app(), window_controls=True).node.get("window_region") == "drag"
    assert _bar(_app(decorations=False), window_controls=False).node.get("window_region") is None
    with pytest.raises(ValueError, match="window_controls needs the window to be an App's"):
        top_app_bar(View({"id": "r", "kind": "Container", "style": {}}).window, "x", window_controls=True)


def test_a_shell_files_top_bar_is_the_title_bar(tmp_path):
    (tmp_path / "Home_View.yaml").write_text(yaml.safe_dump(
        {"id": "home", "kind": "Container", "style": {"width": 200, "height": 100}}), encoding="utf-8")
    shell = tmp_path / "Studio_Shell.yaml"
    shell.write_text(yaml.safe_dump({"top_bar": {"title": "Studio", "trailing_icons": ["settings"]}}),
                     encoding="utf-8")
    app = _app(decorations=False)
    app.register("Home", app.build_view(tmp_path / "Home_View.yaml"), None)
    app.load_shell(shell)
    app.window.advance(16)
    top = app._shell.top_bar
    assert top.node.get("window_region") == "drag"
    assert top.view.node("top_app_bar.close") is not None
