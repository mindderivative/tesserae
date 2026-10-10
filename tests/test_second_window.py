"""Several windows (#105): `app.open_window`, closing, a modal window that blocks its parent, and a second window's own title bar."""

import pytest

from tesserae import App

MAIN = """name: main
widget: Container
style: {width: 300, height: 200, align_content: top_left}
children:
  - {widget: Rect, name: open, style: {width: 40, height: 20, background: primary}, handlers: {on_click: "open_window('Prefs')"}}
  - {widget: Rect, name: open_modal, style: {width: 40, height: 20, background: secondary}, handlers: {on_click: "open_window('Prefs', True)"}}
"""
PREFS = """name: prefs
widget: Window
title: Preferences
min_width: 200
min_height: 100
style: {width: 360, height: 240}
title_bar: {title: Preferences}
children:
  - {widget: Text, name: hello, text: Hello, typography_role: body_medium, style: {foreground: on_surface}}
  - {widget: Rect, name: close, style: {width: 40, height: 20, background: primary}, handlers: {on_click: window.close}}
  - {widget: Rect, name: grow, style: {width: 40, height: 20, background: error}, handlers: {on_click: window.maximize}}
  - {widget: Rect, name: more, style: {width: 40, height: 20, background: tertiary}, handlers: {on_click: "open_window('Plain', True)"}}
"""
PLAIN = "name: plain\nwidget: Container\nstyle: {width: 100, height: 50}\nchildren:\n  - {widget: Text, name: t, text: Plain, typography_role: body_medium, style: {foreground: on_surface}}\n"


@pytest.fixture
def app(tmp_path):
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text(MAIN)
    (tmp_path / "Views" / "Prefs_View.yaml").write_text(PREFS)
    (tmp_path / "Views" / "Plain_View.yaml").write_text(PLAIN)
    a = App(root=tmp_path, width=300, height=200, theme_seed=(0x67, 0x50, 0xA4, 0xFF), dark=False)
    a.open_view("Main")
    a.show("main")
    a.window.advance(16)
    return a


def test_a_window_view_opens_a_second_window_with_its_title_size_and_flags(app):
    aw = app.open_window("Prefs")
    aw.window.advance(16)
    assert aw.name == "prefs" and app.windows == {"prefs": aw} and app.window_of("prefs") is aw
    assert aw.window.get("title") == "Preferences" and (aw.window.get("width"), aw.window.get("height")) == (360, 240)
    assert aw.window.get("min_width") == 200 and aw.window is not app.window
    assert aw.view.node("root.hello").get("text") == "Hello"


def test_the_main_window_is_untouched(app):
    app.open_window("Prefs").window.advance(16)
    assert app.window.get("title") != "Preferences" and (app.window.get("width"), app.window.get("height")) == (300, 200)
    assert app.current == "main"


def test_a_view_without_a_window_root_opens_at_the_default_size(app):
    aw = app.open_window("Plain")
    assert (aw.window.get("width"), aw.window.get("height")) == (480, 320) and aw.view.node("root.t").get("text") == "Plain"


def test_the_same_name_twice_is_an_error_and_a_wrong_name_is_named(app):
    app.open_window("Prefs")
    with pytest.raises(ValueError, match="already open"):
        app.open_window("Prefs")
    with pytest.raises(KeyError, match="no window named 'nope'"):
        app.window_of("nope")


def test_a_handler_opens_a_window_from_a_view(app):
    app.window.simulate("click", node=app.window_of if False else app.screen("main")[0].node("root.open"))
    app.window.advance(16)
    assert list(app.windows) == ["prefs"]


def test_the_close_handler_in_the_second_window_closes_that_window_only(app):
    aw = app.open_window("Prefs")
    aw.window.advance(16)
    aw.window.simulate("click", node=aw.view.node("root.close"))
    aw.window.advance(16)
    aw.window.simulate("closed")
    assert "prefs" not in app.windows and aw.closed.get() is True


def test_closing_a_window_runs_its_on_close_and_a_second_close_does_nothing(app):
    aw = app.open_window("Prefs")
    seen = []
    aw.on_close(lambda: seen.append("closed"))
    aw.window.simulate("closed")
    aw._closed()
    assert seen == ["closed"]


def test_a_second_windows_views_follow_the_apps_theme(app):
    aw = app.open_window("Prefs")
    aw.window.advance(16)
    before = aw.view.node("root.hello").get("fill")
    app.set_dark(not app._dark)
    aw.window.advance(16)
    assert aw.view.node("root.hello").get("fill") != before


def test_a_modal_window_blocks_its_parent_until_it_closes(app):
    aw = app.open_window("Prefs", modal=True)
    assert aw._scrim is not None
    app.window.simulate("click", node=app.screen("main")[0].node("root.open"))
    app.window.advance(16)
    assert list(app.windows) == ["prefs"]  # the click did not reach the main window's button
    aw.window.simulate("closed")
    assert aw._scrim is None
    app.window.simulate("click", node=app.screen("main")[0].node("root.open"))
    app.window.advance(16)
    assert list(app.windows) == ["prefs"] and app.windows["prefs"] is not aw


def test_a_window_opened_from_a_second_window_has_it_as_its_parent_and_blocks_it(app):
    aw = app.open_window("Prefs")
    aw.window.advance(16)
    aw.window.simulate("click", node=aw.view.node("root.more"))
    aw.window.advance(16)
    plain = app.window_of("plain")
    assert plain.parent is aw and plain._scrim[0] == aw.window
    assert app.window.get("title") != "x"
    plain.window.simulate("closed")
    assert plain._scrim is None


def test_toggling_maximized_acts_on_its_own_window_and_not_the_main_one(app):
    aw = app.open_window("Prefs")
    aw.window.advance(16)
    aw.toggle_maximized()
    aw.window.advance(16)
    assert aw.window.get("maximized") is True and not app.window.get("maximized")
    aw.toggle_maximized()
    aw.window.advance(16)
    assert not aw.window.get("maximized")


def test_a_window_handler_in_a_second_window_acts_on_that_window(app):
    aw = app.open_window("Prefs")
    aw.window.advance(16)
    aw.window.simulate("click", node=aw.view.node("root.grow"))
    aw.window.advance(16)
    assert aw.window.get("maximized") is True and not app.window.get("maximized")
