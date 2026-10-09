"""#208: routed views read the params they were reached with (`app.params`), and a handler navigates by name with params or by route path."""

import pytest

from tesserae import App

WINDOW = """name: shell
widget: Window
title: Notes
style: {width: 600, height: 300}
children:
  - {widget: Rect, name: open3, style: {width: 40, height: 20, background: primary}, handlers: {on_click: "navigate_to('Note', {'id': 3})"}}
  - {widget: Rect, name: open7, style: {width: 40, height: 20, background: secondary}, handlers: {on_click: "navigate_route('notes/' + str(7))"}}
  - {widget: Rect, name: back, style: {width: 40, height: 20, background: tertiary}, handlers: {on_click: "navigate.back"}}
  - {widget: Text, name: here, text: "{{ 'id=' + str(app.params.get('id', 'none')) }}", typography_role: body_medium, style: {foreground: on_surface}}
  - {widget: Container, name: screens, children: [{widget: Home, name: home, route: ""}, {widget: Note, name: note, route: "notes/{id:int}"}]}
"""
NOTE = """name: note
widget: Container
state: {n: 0}
style: {width: 100, height: 50}
children:
  - {widget: Rect, name: bump, style: {width: 20, height: 20, background: primary}, handlers: {on_click: "n += 1"}}
  - {widget: Text, name: t, text: "{{ 'n=' + str(n) }}", typography_role: body_medium, style: {foreground: on_surface}}
"""
SCREEN = "name: {n}\nwidget: Container\nstyle: {{width: 100, height: 50}}\nchildren:\n  - {{widget: Text, name: t, text: {n}, typography_role: body_medium, style: {{foreground: on_surface}}}}\n"


@pytest.fixture
def shell(tmp_path):
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Shell_View.yaml").write_text(WINDOW)
    (tmp_path / "Views" / "Home_View.yaml").write_text(SCREEN.format(n="home"))
    (tmp_path / "Views" / "Note_View.yaml").write_text(NOTE)
    app = App(root=tmp_path)
    view = app.open_view("Shell")
    app.window.advance(16)
    app.navigate_to("")
    app.window.advance(16)
    return app, view


def text(view):
    return view._built.specs["root.here"]["text"]["content"]


def click(app, view, name):
    app.window.simulate("click", node=view.node(f"root.{name}"))
    app.window.advance(16)


def test_there_are_no_params_until_a_screen_is_reached_with_some(shell):
    app, view = shell
    assert app.params.get() == {} and text(view) == "id=none"


def test_navigating_by_name_with_params_makes_them_readable(shell):
    app, view = shell
    click(app, view, "open3")
    assert app.current == "Note" and app.params.get() == {"id": 3} and text(view) == "id=3"


def test_navigating_by_route_path_reads_the_params_from_the_path(shell):
    app, view = shell
    click(app, view, "open7")
    assert app.current == "Note" and text(view) == "id=7"


def test_back_and_forward_restore_each_entrys_params(shell):
    app, view = shell
    click(app, view, "open3")
    click(app, view, "open7")
    assert text(view) == "id=7"
    click(app, view, "back")
    assert text(view) == "id=3"
    click(app, view, "back")
    assert app.current == "Home" and text(view) == "id=none"
    app.forward()
    app.window.advance(16)
    assert text(view) == "id=3"


def test_a_jump_with_show_clears_the_params(shell):
    app, view = shell
    click(app, view, "open3")
    app.show("Home")
    app.window.advance(16)
    assert app.params.get() == {} and text(view) == "id=none"


def shown(view):
    return {name: bool(view.node(f"root.screens.{name}").get("visible")) for name in ("home", "note")}


def test_no_screen_shows_until_a_route_is_current_and_then_only_that_one(shell):
    app, view = shell
    assert shown(view) == {"home": True, "note": False}
    click(app, view, "open3")
    assert shown(view) == {"home": False, "note": True}
    click(app, view, "back")
    assert shown(view) == {"home": True, "note": False}


def test_a_hidden_screen_keeps_its_state_and_the_view_resyncing_does_not_show_it(shell):
    app, view = shell
    click(app, view, "open3")
    app.window.simulate("click", node=view.node("root.screens.note.bump"))
    app.window.advance(16)
    click(app, view, "open7")  # the same screen with other params: the view re-syncs
    click(app, view, "back")
    click(app, view, "back")  # home: the note screen is hidden
    assert shown(view) == {"home": True, "note": False}
    click(app, view, "open3")
    assert view._built.specs["root.screens.note.t"]["text"]["content"] == "n=1"


def test_a_view_routed_twice_is_named(tmp_path):
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Shell_View.yaml").write_text(
        "name: shell\nwidget: Window\ntitle: T\nstyle: {width: 300, height: 200}\nchildren:\n  - {widget: Home, name: a, route: ''}\n  - {widget: Home, name: b, route: other}\n")
    (tmp_path / "Views" / "Home_View.yaml").write_text(SCREEN.format(n="home"))
    with pytest.raises(ValueError, match="the screen 'Home' is already the routed view"):
        App(root=tmp_path).open_view("Shell")


def test_a_transition_plays_between_routed_screens(shell):
    app, view = shell
    app.transition = "fade_through"
    app.navigate("Note", id=3)
    app.window.advance(16)
    assert shown(view) == {"home": True, "note": True}  # both are there while it plays
    for _ in range(40):
        app.window.advance(16)
    assert shown(view) == {"home": False, "note": True}


def test_a_routed_call_that_appears_later_becomes_a_screen(tmp_path):
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Shell_View.yaml").write_text(
        "name: shell\nwidget: Window\ntitle: T\nstate: {more: false}\nstyle: {width: 300, height: 200}\nchildren:\n"
        "  - {widget: Rect, name: add, style: {width: 20, height: 20, background: primary}, handlers: {on_click: 'more = True'}}\n"
        "  - {widget: Home, name: home, route: ''}\n"
        "  - {widget: Note, name: note, route: 'notes/{id:int}', if: more}\n")
    (tmp_path / "Views" / "Home_View.yaml").write_text(SCREEN.format(n="home"))
    (tmp_path / "Views" / "Note_View.yaml").write_text(NOTE)
    app = App(root=tmp_path)
    view = app.open_view("Shell")
    app.window.advance(16)
    with pytest.raises(KeyError):
        app.navigate_to("notes/5")
    app.window.simulate("click", node=view.node("root.add"))
    app.window.advance(16)
    app.navigate_to("notes/5")
    assert app.current == "Note" and app.params.get() == {"id": 5}
