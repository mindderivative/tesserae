"""#221: a Window, its TitleBar and a Dock written with `widget:` work in a composed view as they do in a 0.4.x one -- the bindings and handlers
the expansion produces are wired, and the OS window is set from the Window."""

import pytest

from tesserae import App, ViewModel

SEED = (0x67, 0x50, 0xA4, 0xFF)

WINDOW = """name: main
widget: Window
title: Notes
min_width: 320
min_height: 200
borderless: true
style: {width: 700, height: 500}
children:
  - {widget: TitleBar, name: bar, title: Notes, icon: home}
  - widget: Dock
    name: dock
    children:
      - widget: DockPanel
        name: files
        title: Files
        style: {zone: left, width: 200}
        children:
          - {widget: Text, name: ft, text: Files, typography_role: body_large, style: {foreground: on_surface}}
      - widget: DockPanel
        name: outline
        title: Outline
        style: {zone: left}
        children:
          - {widget: Text, name: ot, text: Outline, typography_role: body_large, style: {foreground: on_surface}}
      - widget: DockPanel
        name: editor
        title: Editor
        style: {zone: center}
        children:
          - {widget: Text, name: et, text: Editor, typography_role: body_large, style: {foreground: on_surface}}
"""


class VM(ViewModel):
    views = "main"


def opened(tmp_path, text=WINDOW, native_controls=False):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(text)
    app = App(root=tmp_path, width=700, height=500, theme_seed=SEED, borderless=True)
    app._native_controls.set(native_controls)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    app.window.advance(32)
    return app, view


def test_the_window_sets_the_os_window(tmp_path):
    app, _ = opened(tmp_path)
    assert app.window.get("title") == "Notes" and app.borderless is True
    assert (app.min_width, app.min_height) == (320, 200)


def test_a_second_window_view_is_refused(tmp_path):
    app, _ = opened(tmp_path)
    (tmp_path / "Views" / "Other_View.yaml").write_text(WINDOW.replace("name: main", "name: other"))
    with pytest.raises(ValueError, match="an app has one window"):
        app.open_view("Other")


def test_the_title_bar_buttons_act_and_maximize_follows_the_window(tmp_path, monkeypatch):
    app, view = opened(tmp_path)
    glyph = lambda name: view.node(f"root.bar.maximize.{name}").get("opacity")  # noqa: E731
    assert (glyph("window_maximize"), glyph("window_restore")) == (1.0, 0.0)
    app.window.simulate("click", node=view.node("root.bar.maximize"))
    assert app.maximized.get() is True
    assert (glyph("window_maximize"), glyph("window_restore")) == (0.0, 1.0)
    app.window.simulate("maximized", maximized=False)
    assert (glyph("window_maximize"), glyph("window_restore")) == (1.0, 0.0)
    called = []
    monkeypatch.setattr(app, "minimize", lambda: called.append("minimize"))
    monkeypatch.setattr(app, "close", lambda: called.append("close"))
    app.window.simulate("click", node=view.node("root.bar.minimize"))
    app.window.simulate("click", node=view.node("root.bar.close"))
    assert called == ["minimize", "close"]


def test_the_title_bar_dims_while_the_window_is_not_active(tmp_path):
    app, view = opened(tmp_path)
    title = lambda: view.node("root.bar.title").get("opacity")  # noqa: E731
    app.window.simulate("active", active=True)
    assert title() == 1.0
    app.window.simulate("active", active=False)
    assert title() == pytest.approx(0.6)
    app.window.simulate("active", active=True)
    assert title() == 1.0


def test_the_os_buttons_replace_the_bars_own_where_the_os_draws_them(tmp_path):
    app, view = opened(tmp_path, native_controls=True)
    assert view.node("root.bar.buttons").get("visible") is False
    app._native_controls.set(False)
    assert view.node("root.bar.buttons").get("visible") is True


def test_the_dock_is_built_from_the_panels(tmp_path):
    _, view = opened(tmp_path)
    layout = view.dock_host("root.dock").layout()["zones"]
    assert layout["left"] == {"panels": ["Files", "Outline"], "shown": "Files", "size": 200.0}
    assert layout["center"]["panels"] == ["Editor"]
    assert view.node("root.dock.files").get("layout_width") == 200.0 and view.node("root.dock.files.ft").get("text") == "Files"


def test_dragging_a_docks_handle_resizes_its_zone(tmp_path):
    app, view = opened(tmp_path)
    host = view.dock_host("root.dock")
    handle = host._handles["left"].node
    x, y = handle.get("layout_x") + 8, handle.get("layout_y") + 8
    app.window.simulate("pointer_down", handle, x=8, y=8)
    app.window.simulate("pointer_move", x=x + 60, y=y)
    app.window.simulate("pointer_up", x=x + 60, y=y)
    app.window.advance(16)
    assert host.size("left") == 260.0 and view.node("root.dock.files").get("layout_width") == 260.0


def test_a_dock_keeps_where_its_panels_were_put_when_the_view_changes(tmp_path):
    app, view = opened(tmp_path)
    host = view.dock_host("root.dock")
    host.dock.move(view.node("root.dock.outline"), "center")
    app.window.advance(16)
    assert host.layout()["zones"]["center"]["panels"] == ["Editor", "Outline"]
    view.reconcile(view._spec)  # as a re-sync does
    app.window.advance(16)
    assert view.dock_host("root.dock").layout()["zones"]["center"]["panels"] == ["Editor", "Outline"]


def test_a_view_with_no_window_is_as_before(tmp_path):
    app, view = opened(tmp_path, "name: main\nwidget: Container\nstyle: {width: 100, height: 100}\n")
    assert app.window.get("title") != "Notes" and not view._docks


def test_a_binding_that_needs_a_viewmodel_waits_for_one(tmp_path):
    import yaml

    from tesserae import Signal

    page = {"id": "root", "kind": "Container", "style": {"width": 200, "height": 100},
            "children": [{"id": "shown", "kind": "Text", "text": {"content": "", "typography_role": "body_large"},
                          "style": {"foreground": "on_surface"}, "bindings": {"text": "{{ label.get() }}"}}]}
    path = tmp_path / "Home_View.yaml"
    path.write_text(yaml.safe_dump(page), encoding="utf-8")
    app = App(width=200, height=100, theme_seed=SEED)
    view = app.build_view(path)  # an app, and no ViewModel yet: not an error, the binding is for the ViewModel to wire
    app.register("Home", view, None)
    app.show("Home")

    class Mine(ViewModel):
        def __init__(self, view):
            self.label = Signal("mine")
            super().__init__(view)

    Mine(view)
    assert view.node("shown").get("text") == "mine"
