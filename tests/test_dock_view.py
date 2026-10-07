"""0.4.4 (#100, #104): `kind: Dock` and `kind: DockPanel` in a view, their zones, tabs, handles, splits and reloads."""

import copy

import pytest
import yaml

from tesserae import App, View
from tesserae.spec.dock import DockError, expand_docks

SEED = (0x67, 0x50, 0xA4, 0xFF)
DOCK = """
id: root
kind: Container
style: {width: 800, height: 500}
children:
  - id: dock
    kind: Dock
    children:
      - id: files
        kind: DockPanel
        title: Files
        style: {zone: left, width: 200}
        children:
          - {id: files_text, kind: Text, text: {content: "Files", typography_role: body_large}, style: {foreground: on_surface}}
      - id: outline
        kind: DockPanel
        title: Outline
        style: {zone: left}
        children:
          - {id: outline_text, kind: Text, text: {content: "Outline", typography_role: body_large}, style: {foreground: on_surface}}
      - id: editor
        kind: DockPanel
        title: Editor
        style: {zone: center}
        children:
          - id: left_half
            kind: DockPanel
            style: {width: 300}
            children:
              - {id: left_text, kind: Text, text: {content: "Left half", typography_role: body_large}, style: {foreground: on_surface}}
          - id: right_half
            kind: DockPanel
            children:
              - {id: right_text, kind: Text, text: {content: "Right half", typography_role: body_large}, style: {foreground: on_surface}}
      - id: console
        kind: DockPanel
        title: Console
        style: {zone: bottom, height: 120}
        children:
          - {id: console_text, kind: Text, text: {content: "Console", typography_role: body_large}, style: {foreground: on_surface}}
"""


def _view(text=DOCK, dark=True):
    app = App(width=800, height=500, theme_seed=SEED, dark=dark)
    view = View(yaml.safe_load(text), window=app.window)
    app.window.root.add_child(view.root)
    app.window.advance(32)
    return app, view


# -- the spec ------------------------------------------------------------------------------------

def test_a_dock_becomes_containers_with_its_panels_and_sizes():
    spec = expand_docks(yaml.safe_load(DOCK))
    dock = spec["children"][0]
    assert dock["kind"] == "Container" and dock["dock"]["panels"] == [
        {"id": "files", "title": "Files", "zone": "left"}, {"id": "outline", "title": "Outline", "zone": "left"},
        {"id": "editor", "title": "Editor", "zone": "center"}, {"id": "console", "title": "Console", "zone": "bottom"}]
    assert dock["dock"]["sizes"] == {"left": 200.0, "bottom": 120.0}
    files = dock["children"][0]
    assert "zone" not in files["style"] and files["style"]["width"] == "100%"  # the zone has the size; the panel fills it
    assert files["dock_panel"] == {"title": "Files", "zone": "left"}


def test_a_split_has_a_handle_between_its_halves():
    spec = expand_docks(yaml.safe_load(DOCK))
    editor = spec["children"][0]["children"][2]
    first, handle, second = editor["children"]
    assert handle["split_handle"] == {"axis": "x", "before": "left_half", "after": "right_half"}
    assert first["style"]["flex"] == "none" and second["style"]["flex"] == "fill"  # one with a width keeps it
    vertical = yaml.safe_load(DOCK.replace("style: {zone: center}", "style: {zone: center, flex_direction: vertical}"))
    assert expand_docks(vertical)["children"][0]["children"][2]["children"][1]["split_handle"]["axis"] == "y"


@pytest.mark.parametrize("change, message", [
    (lambda d: d["children"][0]["children"][0]["style"].pop("zone"), "says which zone it is in"),
    (lambda d: d["children"][0]["children"][0]["style"].update(zone="middle"), "says which zone it is in"),
    (lambda d: d["children"][0]["children"][0]["style"].update(width=-4), "a left zone's width is a number of pixels"),
    (lambda d: d["children"][0]["children"][0].update(title=3), "title is text"),
    (lambda d: d["children"][0]["children"][0].update(bogus=1), "takes .*not bogus"),
    (lambda d: d["children"][0]["children"].append({"id": "x", "kind": "Rect"}), "a Dock holds DockPanels"),
    (lambda d: d["children"][0]["children"][2]["children"].append({"id": "t", "kind": "Text"}), "splits .* or content, not both"),
    (lambda d: d["children"][0]["children"][2]["children"][0]["style"].update(zone="left"), "a split of it and has no zone"),
    (lambda d: d["children"].append({"id": "second", "kind": "Dock", "children": []}), "a window has one Dock"),
    (lambda d: d["children"].append({"id": "loose", "kind": "DockPanel"}), "a DockPanel is in a Dock"),
    (lambda d: d["children"].append({"id": "r", "kind": "Rect", "style": {"zone": "left"}}), "style.zone is for a DockPanel in a Dock"),
])
def test_a_badly_written_dock_is_refused(change, message):
    spec = yaml.safe_load(DOCK)
    change(spec)
    with pytest.raises(DockError, match=message):
        expand_docks(spec)


def test_zone_from_a_stylesheet_on_another_node_is_a_build_error():
    sheet = {"styles": [{"id": "r", "style": {"zone": "left"}}]}
    spec = {"id": "root", "kind": "Container", "children": [{"id": "r", "kind": "Rect", "style": {"width": 10, "height": 10, "background": "primary"}}]}
    app = App(width=100, height=100, theme_seed=SEED)
    with pytest.raises(ValueError, match="style.zone is for a DockPanel in a Dock"):
        View(spec, window=app.window, stylesheet_spec=sheet)


# -- the dock -------------------------------------------------------------------------------------

def test_panels_in_a_zone_are_its_tabs_and_the_first_shows():
    app, view = _view()
    host = view.dock_host("dock")
    layout = host.layout()["zones"]
    assert layout["left"] == {"panels": ["Files", "Outline"], "shown": "Files", "size": 200.0}
    assert layout["center"]["panels"] == ["Editor"] and layout["bottom"] == {"panels": ["Console"], "shown": "Console", "size": 120.0}
    assert view.node("files").get("layout_width") == 200.0 and view.node("files_text").get("text") == "Files"
    with pytest.raises(ValueError):
        host.size("right")


def test_a_zone_is_as_big_as_its_panel_said_and_the_rest_is_the_centre():
    _, view = _view()
    assert view.node("files").get("layout_width") == 200.0
    editor = view.node("editor")
    assert editor.get("layout_x") >= 200.0 + 16 and editor.get("layout_width") == pytest.approx(800 - 200 - 16, abs=1)
    assert view.node("left_half").get("layout_width") == 300.0


def test_dragging_a_zones_handle_resizes_it_and_the_keys_do_too():
    app, view = _view()
    host = view.dock_host("dock")
    handle = host._handles["left"].node
    x, y = handle.get("layout_x") + 8, handle.get("layout_y") + 8
    app.window.simulate("pointer_down", handle, x=8, y=8)
    app.window.simulate("pointer_move", x=x + 60, y=y)
    app.window.simulate("pointer_up", x=x + 60, y=y)
    app.window.advance(16)
    assert host.size("left") == 260.0 and view.node("files").get("layout_width") == 260.0
    handle.focus()
    app.window.simulate("key_down", key="arrow_left")
    assert host.size("left") == 244.0
    high = host._bounds("left")[1]
    app.window.simulate("key_down", key="end")
    assert host.size("left") == high
    app.window.simulate("key_down", key="home")
    assert host.size("left") == 120.0
    assert host.set_size("left", 9999) <= host._bounds("left")[1]


def test_a_panel_moves_to_another_zone_and_the_layout_comes_back():
    app, view = _view()
    host = view.dock_host("dock")
    host.dock.move(view.node("outline"), "bottom")
    app.window.advance(16)
    assert host.layout()["zones"]["bottom"]["panels"] == ["Console", "Outline"] and host.layout()["zones"]["left"]["panels"] == ["Files"]
    saved = copy.deepcopy(host.layout())
    host.dock.move(view.node("outline"), "left")
    host.set_size("left", 300)
    host.restore(saved)
    assert host.layout()["zones"]["bottom"]["panels"] == ["Console", "Outline"] and host.size("left") == 200.0


def test_a_splits_handle_resizes_the_half_before_it():
    app, view = _view()
    host = view.dock_host("dock")
    handle = view.node("editor.split.0")
    x, y = handle.get("layout_x") + 8, handle.get("layout_y") + 8
    app.window.simulate("pointer_down", handle, x=8, y=8)
    app.window.simulate("pointer_move", x=x + 40, y=y)
    app.window.simulate("pointer_up", x=x + 40, y=y)
    app.window.advance(16)
    assert view.node("left_half").get("layout_width") == 340.0
    assert host.layout()["splits"] == {"left_half": 340.0}
    handle.focus()
    app.window.simulate("key_down", key="arrow_left")
    assert view.node("left_half").get("layout_width") == 324.0
    app.window.simulate("key_down", key="home")
    assert view.node("left_half").get("layout_width") == 48.0  # a half is never smaller than that


def test_the_dock_follows_the_apps_theme():
    app, view = _view(dark=True)
    host = view.dock_host("dock")
    before = host._handles["left"].grip.get("fill")
    app.set_dark(False)
    app.window.advance(16)
    assert host._handles["left"].grip.get("fill") != before
    assert host._handles["left"].grip.get("fill") == app.theme.role("outline")


# -- reloads ----------------------------------------------------------------------------------

def _reload(view, change):
    spec = yaml.safe_load(DOCK)
    change(spec)
    view.reconcile(spec)
    view.window.advance(16)


def test_a_reload_leaves_a_panel_the_user_moved_where_it_is():
    app, view = _view()
    host = view.dock_host("dock")
    host.dock.move(view.node("outline"), "bottom")
    host.set_size("left", 260)
    _reload(view, lambda d: d["children"][0]["children"][1].update(title="Outline"))  # nothing about it changed
    assert view.dock_host("dock") is host
    assert host.layout()["zones"]["bottom"]["panels"] == ["Console", "Outline"] and host.size("left") == 260.0


def test_a_reload_patches_the_panels_content_in_place():
    app, view = _view()
    node = view.node("files_text")
    _reload(view, lambda d: d["children"][0]["children"][0]["children"][0]["text"].update(content="Documents"))
    assert view.node("files_text").get("text") == "Documents"
    assert view.dock_host("dock").layout()["zones"]["left"]["shown"] == "Files"
    del node


def test_a_reload_that_renames_moves_resizes_adds_and_removes_panels():
    app, view = _view()
    host = view.dock_host("dock")

    def change(spec):
        panels = spec["children"][0]["children"]
        panels[0]["title"] = "Documents"                      # renamed
        panels[1]["style"]["zone"] = "bottom"                 # the file moves it
        panels[3]["style"]["height"] = 200                    # the file resizes its zone
        panels.append({"id": "notes", "kind": "DockPanel", "title": "Notes", "style": {"zone": "left"},
                       "children": [{"id": "notes_text", "kind": "Text", "text": {"content": "Notes", "typography_role": "body_large"},
                                     "style": {"foreground": "on_surface"}}]})   # added
    _reload(view, change)
    zones = host.layout()["zones"]
    assert zones["left"]["panels"] == ["Documents", "Notes"] and zones["bottom"]["panels"] == ["Console", "Outline"]
    assert host.size("bottom") == 200.0
    assert view.node("notes_text").get("text") == "Notes"
    _reload(view, lambda d: d["children"][0]["children"].pop(0))  # Files removed
    assert host.layout()["zones"]["left"]["panels"] == ["Outline"] or "Files" not in host.layout()["zones"]["left"]["panels"]
    with pytest.raises(ValueError):
        view.node("files")


def test_a_reload_that_adds_a_zone_makes_the_dock_again():
    app, view = _view()
    before = view.dock_host("dock")

    def change(spec):
        spec["children"][0]["children"].append({"id": "props", "kind": "DockPanel", "title": "Props", "style": {"zone": "right", "width": 180},
                                                "children": []})
    _reload(view, change)
    after = view.dock_host("dock")
    assert after is not before and "right" in after.layout()["zones"] and after.size("right") == 180.0


def test_a_split_keeps_its_size_through_a_reload():
    app, view = _view()
    host = view.dock_host("dock")
    host._splits["editor.split.0"].set(380)
    _reload(view, lambda d: None)
    app.window.advance(16)
    assert view.node("left_half").get("layout_width") == 380.0


def test_a_dock_in_a_removed_view_is_disposed():
    app, view = _view()
    host = view.dock_host("dock")
    view._dispose_controls()
    assert not host._handles and not view._docks
