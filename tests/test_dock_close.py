"""#206, #207: a DockPanel can have a close button on its tab, and a Dock's `closed` list says which panels are shut."""

import pytest

from tesserae import App, Signal, ViewModel

WINDOW = """name: main
widget: Window
title: Notes
borderless: true
style: {width: 700, height: 500, flex_direction: vertical}
children:
  - widget: Dock
    name: dock
    closed: "{{ shut }}"
    children:
      - widget: DockPanel
        name: files
        title: Files
        closable: true
        style: {zone: left, width: 200}
        children: [{widget: Text, name: ft, text: Files, typography_role: body_large, style: {foreground: on_surface}}]
      - widget: DockPanel
        name: outline
        title: Outline
        closable: true
        style: {zone: left}
        children: [{widget: Text, name: ot, text: Outline, typography_role: body_large, style: {foreground: on_surface}}]
      - widget: DockPanel
        name: editor
        title: Editor
        style: {zone: center}
        children: [{widget: Text, name: et, text: Editor, typography_role: body_large, style: {foreground: on_surface}}]
"""


class VM(ViewModel):
    views = "main"
    start = []

    def __init__(self):
        super().__init__()
        self.shut = Signal(list(self.start))


def opened(tmp_path, start=()):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(WINDOW)
    VM.start = list(start)
    app = App(root=tmp_path, width=700, height=500, theme_seed=(0x67, 0x50, 0xA4, 0xFF), borderless=True)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    for _ in range(6):
        app.window.advance(16)
    return app, view, app.bindings.viewmodel_for("main")


def host(view):
    return view.dock_host("root.dock")


def tabs(view, side="left"):
    return host(view).dock.titles(side)


def close_button(view, side, index):
    zone = host(view).dock._zones[side]
    tab = zone.tabs[index]
    return next(c for c in tab.node.children() if c.get("role") == "button")


def test_a_closable_panels_tab_has_a_close_button_and_the_others_do_not(tmp_path):
    app, view, _ = opened(tmp_path)
    assert tabs(view) == ["Files", "Outline"]
    assert close_button(view, "left", 0).get("label") == "Close Files"
    zone = host(view).dock._zones["center"]
    assert zone.tabs == [] or all(c.get("role") != "button" for t in zone.tabs for c in t.node.children())


def test_pressing_the_close_button_shuts_the_panel_and_names_it_in_closed(tmp_path):
    app, view, vm = opened(tmp_path)
    app.window.simulate("click", node=close_button(view, "left", 0))
    for _ in range(4):
        app.window.advance(16)
    assert tabs(view) == ["Outline"] and vm.shut.get() == ["files"] and host(view).closed() == ["root.dock.files"]


def test_the_other_panel_is_shown_after_one_is_closed(tmp_path):
    app, view, _ = opened(tmp_path)
    app.window.simulate("click", node=close_button(view, "left", 0))
    for _ in range(4):
        app.window.advance(16)
    assert host(view).dock.shown_title("left") == "Outline"


def test_taking_a_name_out_of_closed_opens_the_panel_again_as_the_last_tab(tmp_path):
    app, view, vm = opened(tmp_path)
    app.window.simulate("click", node=close_button(view, "left", 0))
    for _ in range(4):
        app.window.advance(16)
    vm.shut.set([])
    for _ in range(6):
        app.window.advance(16)
    assert tabs(view) == ["Outline", "Files"] and host(view).closed() == []


def test_putting_a_name_in_closed_shuts_the_panel_without_the_button(tmp_path):
    app, view, vm = opened(tmp_path)
    vm.shut.set(["outline"])
    for _ in range(6):
        app.window.advance(16)
    assert tabs(view) == ["Files"] and host(view).closed() == ["root.dock.outline"]


def test_a_dock_that_starts_with_a_panel_shut_opens_without_it(tmp_path):
    app, view, vm = opened(tmp_path, start=["files"])
    assert tabs(view) == ["Outline"] and vm.shut.get() == ["files"]


def test_a_panel_that_is_not_closable_cannot_be_shut_by_the_list(tmp_path):
    app, view, vm = opened(tmp_path)
    vm.shut.set(["editor"])
    for _ in range(6):
        app.window.advance(16)
    assert host(view).dock.titles("center") == ["Editor"] and host(view).closed() == []
