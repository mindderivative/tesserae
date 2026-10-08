"""0.4.4 (#99): routed screens in a window view: `view:` with `route:`, and the `navigate.*` handlers."""

import sys

import pytest
import yaml

from tesserae import App, View

SEED = (0x67, 0x50, 0xA4, 0xFF)
WINDOW = """
id: root
kind: Window
title: App
style: {{width: 600, height: 300}}
children:
  - id: rail
    kind: Container
    style: {{width: 100, flex_direction: vertical}}
    children:
      - {{id: go_main, kind: Rect, style: {{height: 30, background: primary}}, handlers: {{on_click: "navigate.{home}"}}}}
      - {{id: go_settings, kind: Rect, style: {{height: 30, background: secondary}}, handlers: {{on_click: "navigate.{settings}"}}}}
      - {{id: go_back, kind: Rect, style: {{height: 30, background: tertiary}}, handlers: {{on_click: "navigate.back"}}}}
      - {{id: go_forward, kind: Rect, style: {{height: 30, background: error}}, handlers: {{on_click: "navigate.forward"}}}}
  - id: screens
    kind: Container
    style: {{flex: fill, gap: 20}}
    children:
      - {{id: main, view: {home}_View.yaml, route: ""}}
      - {{id: settings, view: {settings}_View.yaml, route: settings}}
"""
HOME = "id: root\nkind: Container\nstyle: {width: 200, height: 100}\nchildren:\n  - {id: hi, kind: Text, text: {content: Home, typography_role: body_large}, style: {foreground: on_surface}}\n"
SETTINGS = """
id: root
kind: Container
style: {width: 200, height: 100}
children:
  - {id: shown, kind: Text, text: {content: "", typography_role: body_large}, style: {foreground: on_surface}, bindings: {text: "{{ label.get() }}"}}
  - {id: bump, kind: Rect, style: {width: 20, height: 20, background: primary}, handlers: {on_click: bump}}
"""
SETTINGS_VM = """
from tesserae import Signal, ViewModel


class {name}ViewModel(ViewModel):
    def __init__(self, view):
        self.n = Signal(0)
        self.label = Signal("clicks 0")
        super().__init__(view)

    def bump(self):
        self.n.update(lambda n: n + 1)
        self.label.set(f"clicks {{self.n.get()}}")
"""


@pytest.fixture
def project(tmp_path):
    tag = abs(hash(str(tmp_path))) % 10**8
    home, settings = f"Home{tag}", f"Pref{tag}"
    (tmp_path / "Views").mkdir()
    (tmp_path / "ViewModels").mkdir()
    (tmp_path / "Views" / "Window_View.yaml").write_text(WINDOW.format(home=home, settings=settings))
    (tmp_path / "Views" / f"{home}_View.yaml").write_text(HOME)
    (tmp_path / "Views" / f"{settings}_View.yaml").write_text(SETTINGS)
    (tmp_path / "ViewModels" / f"{settings}_ViewModel.py").write_text(SETTINGS_VM.format(name=settings))
    sys.path.insert(0, str(tmp_path / "ViewModels"))
    yield tmp_path, home, settings
    sys.path.remove(str(tmp_path / "ViewModels"))
    sys.modules.pop(f"{settings}_ViewModel", None)


def _app(project):
    tmp_path, home, settings = project
    app = App(root=tmp_path, theme_seed=SEED, dark=True)
    view, _ = app.load("Window")
    app.window.advance(16)
    return app, view


def _shown(view):
    return {node_id: bool(view.node(node_id).get("visible")) for node_id in ("main", "settings")}


def test_routed_views_are_screens_with_routes_and_none_shows_until_a_route_is(project):
    _, home, settings = project
    app, view = _app(project)
    assert sorted(app._registered) == sorted(["Window", home, settings])
    assert app.screen(home)[0] is view.embedded("main") and app.screen(settings)[1] is view.embedded("settings").viewmodel
    assert _shown(view) == {"main": False, "settings": False}
    app.navigate_to("")
    app.window.advance(16)
    assert app.current == home and _shown(view) == {"main": True, "settings": False}
    assert app.current_screen.get() == home


def test_a_hidden_screen_takes_no_room(project):
    app, view = _app(project)
    app.navigate_to("")
    app.window.advance(16)
    assert view.embedded("main").node("hi").get("layout_width") > 0
    assert view.node("settings").get("layout_width") in (0, 0.0) or not view.node("settings").get("visible")


def test_navigating_shows_the_other_and_back_returns(project):
    app, view = _app(project)
    _, home, settings = project
    app.navigate_to("")
    app.navigate_to("settings")
    assert app.current == settings and _shown(view) == {"main": False, "settings": True}
    app.back()
    assert app.current == home and _shown(view) == {"main": True, "settings": False}
    assert app.can_go_forward.get() is True


def test_the_navigate_handlers_work_from_the_window_view(project):
    app, view = _app(project)
    _, home, settings = project
    app.navigate_to("")
    app.window.simulate("click", view.node("go_settings"))
    assert app.current == settings
    app.window.simulate("click", view.node("go_back"))
    assert app.current == home
    app.window.simulate("click", view.node("go_forward"))
    assert app.current == settings
    app.window.simulate("click", view.node("go_main"))
    assert app.current == home


def test_a_routed_view_keeps_its_state_while_hidden(project):
    app, view = _app(project)
    app.navigate_to("settings")
    settings = view.embedded("settings")
    app.window.simulate("click", settings.node("bump"))
    app.navigate_to("")
    app.navigate_to("settings")
    assert settings.node("shown").get("text") == "clicks 1"


def test_a_route_outside_a_window_view_is_an_error(tmp_path):
    (tmp_path / "Left_View.yaml").write_text(HOME)
    (tmp_path / "Host_View.yaml").write_text("id: root\nkind: Container\nchildren:\n  - {id: l, view: Left_View.yaml, route: x}\n")
    with pytest.raises(ValueError, match="a `route:` is for a view in the window view"):
        View(tmp_path / "Host_View.yaml")


def test_a_view_routed_twice_is_an_error(project):
    tmp_path, home, _ = project
    text = (tmp_path / "Views" / "Window_View.yaml").read_text()
    (tmp_path / "Views" / "Window_View.yaml").write_text(
        text + f"      - {{id: again, view: {home}_View.yaml, route: again}}\n")
    app = App(root=tmp_path, theme_seed=SEED, dark=True)
    with pytest.raises(ValueError, match="is already the routed view"):
        app.load("Window")


def test_navigating_to_an_unknown_screen_is_the_apps_error(project):
    app, view = _app(project)
    (project[0] / "Views" / "Window_View.yaml").write_text(
        (project[0] / "Views" / "Window_View.yaml").read_text().replace("navigate.back", "navigate.Nowhere"))
    spec = yaml.safe_load((project[0] / "Views" / "Window_View.yaml").read_text())
    view.reconcile(spec)
    app.navigate_to("")
    before = app.current
    app.window.simulate("click", view.node("go_back"))  # a handler's error is logged by the event loop, the app goes on
    assert app.current == before
    with pytest.raises(KeyError, match="Nowhere"):
        app.navigate("Nowhere")


def test_editing_the_window_view_adds_and_removes_screens(project):
    app, view = _app(project)
    _, home, settings = project
    app.navigate_to("")
    spec = yaml.safe_load((project[0] / "Views" / "Window_View.yaml").read_text())
    spec["children"][1]["children"].pop(1)  # the settings screen goes
    view.reconcile(spec)
    assert settings not in app._registered and app.current == home
    with pytest.raises(KeyError):
        app.navigate_to("settings")
    spec["children"][1]["children"].append({"id": "settings", "view": f"{settings}_View.yaml", "route": "settings"})
    view.reconcile(spec)
    app.navigate_to("settings")
    assert app.current == settings and view.node("settings").get("visible")


def test_a_rail_of_screens_follows_the_current_screen(project):
    tmp_path, home, settings = project
    text = (tmp_path / "Views" / "Window_View.yaml").read_text()
    rail = f"""  - id: nav
    component: NavigationRailScreens
    with:
      items:
        - {{label: Tasks, icon: home, screen: {home}}}
        - {{label: Prefs, icon: settings, screen: {settings}}}
"""
    (tmp_path / "Views" / "Window_View.yaml").write_text(text.replace("  - id: rail\n", rail + "  - id: rail\n", 1))
    app = App(root=tmp_path, theme_seed=SEED, dark=True)
    view, _ = app.load("Window")
    app.navigate_to("")
    app.window.advance(16)
    filled = app.theme.role("secondary_container")
    assert view.node("nav.item.0.pill").get("fill") == filled and view.node("nav.item.1.pill").get("fill") != filled
    app.window.simulate("click", view.node("nav.item.1"))
    app.window.advance(16)
    assert app.current == settings
    assert view.node("nav.item.1.pill").get("fill") == filled and view.node("nav.item.0.pill").get("fill") != filled
    assert view.node("nav.item.1.label").get("fill") == app.theme.role("on_surface")
