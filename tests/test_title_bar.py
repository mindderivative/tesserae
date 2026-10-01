"""0.3.0 M3 Phase 2 (#50): `kind: TitleBar`, expanded into a drag-region
bar with the app's icon, title and content, and the window buttons,
which call the app's actions and follow `app.maximized`.
"""

import pytest
import yaml

from tesserae import App, ViewModel
from tesserae.icons import icon_path
from tesserae.spec.title_bar import BUTTONS, TitleBarError, expand_title_bars

SEED = (0x67, 0x50, 0xA4, 0xFF)


def _page(bar):
    return {"id": "root", "kind": "Container", "style": {"width": 600, "height": 400, "flex_direction": "vertical"},
            "children": [bar, {"id": "body", "kind": "Rect",
                               "style": {"width": 600, "height": 300, "background": "surface"}}]}


def _app_with(tmp_path, bar, **app_kwargs):
    path = tmp_path / "Home_View.yaml"
    path.write_text(yaml.safe_dump(_page(bar)), encoding="utf-8")
    app = App(width=600, height=400, theme_seed=SEED, decorations=False, **app_kwargs)
    # The bar as Windows and Linux show it, with its own buttons: on macOS
    # the OS's traffic lights show instead and they hide (test_title_bar_macos).
    app._native_controls.set(False)
    view = app.build_view(path)
    app.register("Home", view, None)
    app.show("Home")
    ViewModel(view)
    app.window.advance(16)
    return app, view


BAR = {"id": "bar", "kind": "TitleBar", "title": "Notes", "icon": "home", "style": {"width": 600}}


def test_the_expansion():
    given = _page(BAR)
    spec = expand_title_bars(given)
    assert given == _page(BAR)  # the spec given is left as it was (a view keeps it for hot reload)
    bar = spec["children"][0]
    assert (bar["kind"], bar["window_region"], bar["classes"]) == ("Container", "drag", ["title_bar"])
    assert [c["id"] for c in bar["children"]] == ["bar.inset", "bar.icon", "bar.title", "bar.content",
                                                  "bar.buttons"]
    buttons = bar["children"][4]["children"]
    assert [b["id"] for b in buttons] == ["bar.minimize", "bar.maximize", "bar.close"]
    assert [b["handlers"]["on_click"] for b in buttons] == ["window.minimize", "window.toggle_maximized",
                                                            "window.close"]
    assert buttons[2]["classes"] == ["title_bar_button", "title_bar_close"]


def test_the_window_glyphs_are_in_the_icon_set():
    for name in ("window_minimize", "window_maximize", "window_restore", "close"):
        assert icon_path(name)


def test_it_lays_out_as_a_desktop_title_bar(tmp_path):
    app, view = _app_with(tmp_path, BAR)
    x = {i: view.node(i).get("layout_x") for i in ("bar.icon", "bar.title", "bar.content", "bar.minimize",
                                                     "bar.maximize", "bar.close")}
    assert x["bar.icon"] < x["bar.title"] < x["bar.content"] < x["bar.minimize"]
    assert x["bar.maximize"] - x["bar.minimize"] == x["bar.close"] - x["bar.maximize"] == 46  # flush
    assert x["bar.close"] + 46 == 600  # at the right edge
    assert view.node("bar").get("layout_height") == 40.0 and view.node("bar").get("window_region") == "drag"


def test_the_buttons_act_and_maximize_follows_the_window(tmp_path, monkeypatch):
    app, view = _app_with(tmp_path, BAR)
    glyph = lambda name: view.node(f"bar.maximize.{name}").get("opacity")  # noqa: E731
    assert (glyph("window_maximize"), glyph("window_restore")) == (1.0, 0.0)
    app.window.simulate("click", node=view.node("bar.maximize"))
    assert app.maximized.get() is True  # before run(): how it opens
    assert (glyph("window_maximize"), glyph("window_restore")) == (0.0, 1.0)
    app.window.simulate("maximized", maximized=False)  # as the OS would report a restore
    assert (glyph("window_maximize"), glyph("window_restore")) == (1.0, 0.0)
    called = []
    monkeypatch.setattr(app, "minimize", lambda: called.append("minimize"))
    monkeypatch.setattr(app, "close", lambda: called.append("close"))
    app.window.simulate("click", node=view.node("bar.minimize"))
    app.window.simulate("click", node=view.node("bar.close"))
    assert called == ["minimize", "close"]


def test_the_bar_drags_and_the_buttons_dont(tmp_path):
    """A press where the title is moves the window (the bar, the drag
    region, gets `pointer_cancel`); a button has a click handler, so a
    press on it is pressed and released as usual."""
    app, view = _app_with(tmp_path, BAR)
    seen = []
    for node_id in ("bar", "bar.close"):  # Tesserae's shared listeners: `node.on` would replace its own
        for event in ("pointer_up", "pointer_cancel"):
            view._events.listen(view.node(node_id), event, lambda e, n=node_id, ev=event: seen.append((n, ev)))

    def press(node_id):  # at the node's centre, as a pointer would
        node = view.node(node_id)
        x = node.get("layout_x") + node.get("layout_width") / 2
        y = node.get("layout_y") + node.get("layout_height") / 2
        app.window.simulate("pointer_down", x=x, y=y)
        app.window.simulate("pointer_up", x=x, y=y)

    app.window.advance(0)
    press("bar.title")
    assert seen == [("bar", "pointer_cancel")]
    seen.clear()
    app.window.advance(1000)  # not a double-click
    press("bar.close")
    assert ("bar.close", "pointer_up") in seen and ("bar", "pointer_cancel") not in seen


def test_its_children_are_the_content(tmp_path):
    bar = {**BAR, "children": [{"id": "search", "kind": "Rect",
                                "style": {"width": 120, "height": 24, "background": "surface_container"}}]}
    app, view = _app_with(tmp_path, bar)
    search = view.node("search")
    assert search.get("layout_x") >= view.node("bar.content").get("layout_x")
    assert search.get("layout_x") + 120 <= view.node("bar.minimize").get("layout_x")


def test_fewer_buttons_and_no_icon_or_title():
    spec = expand_title_bars(_page({"id": "bar", "kind": "TitleBar", "buttons": ["close"]}))
    assert [c["id"] for c in spec["children"][0]["children"]] == ["bar.inset", "bar.content", "bar.buttons"]
    assert [b["id"] for b in spec["children"][0]["children"][2]["children"]] == ["bar.close"]
    none = expand_title_bars(_page({"id": "bar", "kind": "TitleBar", "buttons": []}))
    assert [c["id"] for c in none["children"][0]["children"]] == ["bar.inset", "bar.content"]


@pytest.mark.parametrize("bar, message", [
    ({"id": "bar", "kind": "TitleBar", "subtitle": "x"}, "widget 'bar': a TitleBar takes .*; not subtitle"),
    ({"id": "bar", "kind": "TitleBar", "title": 3}, "widget 'bar': a TitleBar's title is text, got 3"),
    ({"id": "bar", "kind": "TitleBar", "icon": ["home"]}, "a TitleBar's icon is an icon name"),
    ({"id": "bar", "kind": "TitleBar", "buttons": ["help"]}, f"buttons are some of {', '.join(BUTTONS)}"),
    ({"id": "bar", "kind": "TitleBar", "buttons": ["close", "close"]}, "each once"),
])
def test_a_title_bar_written_wrongly_is_one_line(bar, message):
    with pytest.raises(TitleBarError, match=message):
        expand_title_bars(_page(bar))


def test_reconcile_and_the_stylesheet_classes(tmp_path):
    app, view = _app_with(tmp_path, BAR)
    view.reconcile(_page({**BAR, "title": "Notes, edited"}))
    assert view.node("bar.title").get("text") == "Notes, edited"
    assert expand_title_bars(_page({**BAR, "classes": ["mine"]}))["children"][0]["classes"] == ["title_bar", "mine"]
