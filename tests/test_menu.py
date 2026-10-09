"""#168, #169: the Material 3 menu -- items with icons, shortcuts and checks, dividers and headings, submenus, the keyboard."""

import pytest

from tesserae import App, Signal, ViewModel, tokens
from tesserae.shipped import shipped_views

ITEMS = """[{value: cut, label: Cut, shortcut: Ctrl+X}, {value: copy, label: Copy, icon: content_copy}, {divider: true}, {heading: Share},
          {value: paste, label: Paste, disabled: true}, {value: share, label: Share, submenu: [{value: mail, label: Mail}, {value: link, label: Link}]}]"""


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.open = Signal(False)
        self.chosen = Signal("")
        self.checks = Signal(["bold"])
        self.picked = Signal("b")
        self.log = []

    def noted(self):
        self.log.append("picked")


def opened(tmp_path, props="", items=ITEMS, show=True):
    (tmp_path / "Views").mkdir(exist_ok=True)
    lines = "\n    ".join(props.split(", ")) if props else ""
    (tmp_path / "Views" / "Main_View.yaml").write_text(f"""name: main
widget: Container
style: {{width: 600, height: 500}}
children:
  - {{widget: Button, name: btn, label: Open, handlers: {{on_click: "open = True"}}}}
  - widget: Menu
    name: m
    open: "{{{{ open }}}}"
    anchor: btn
    chosen: "{{{{ chosen }}}}"
    items: {items}
    {lines}
""")
    app = App(root=tmp_path, width=600, height=500)
    app.bind(VM)
    view = app.open_view("Main")
    vm = app.bindings.viewmodel_for("main")
    app.show("main")
    settle(view, 4)
    if show:
        vm.open.set(True)
        settle(view, 8)
    return view, vm


def role(view, name):
    return (view._scheme or tokens.BASELINE)[name]


def settle(view, n=20):
    for _ in range(n):
        view.window.advance(16)


def row(view, i, part="item"):
    return view.node(f"root.m.surface.row[{i}].{part}")


def surface(view):
    return view.node("root.m.surface")


def test_it_is_shipped():
    assert {"Menu", "MenuItem"} <= set(shipped_views())


def test_it_opens_below_its_button_as_a_surface_container_with_4_pixel_corners_at_level_two(tmp_path):
    view, vm = opened(tmp_path, show=False)
    assert not view._shown_layers
    vm.open.set(True)
    settle(view, 8)
    s, btn = surface(view), view.node("root.btn")
    assert view._shown_layers and s.get("layout_y") == btn.get("layout_y") + btn.get("layout_height") and s.get("layout_x") == btn.get("layout_x")
    assert s.get("fill") == role(view, "surface_container") and s.get("corner_radius") == 4.0 and s.get("shadows") == tokens.elevation_shadows(2) and s.get("layout_width") == 200.0
    assert s.get("role") == "menu"


def test_the_items_are_48_tall_with_8_pixels_above_and_below(tmp_path):
    view, _ = opened(tmp_path)
    first = row(view, 0)
    assert first.get("layout_height") == 48.0 and first.get("layout_y") == surface(view).get("layout_y") + 8
    assert row(view, 1).get("layout_y") == first.get("layout_y") + 48


def test_an_item_has_its_label_shortcut_and_icon(tmp_path):
    view, _ = opened(tmp_path)
    assert row(view, 0, "item.label").get("text") == "Cut" and row(view, 0, "item.trailing").get("text") == "Ctrl+X"
    assert view._built.specs["root.m.surface.row[1].item.lead"]["icon"] == {"name": "content_copy"}


def test_a_divider_and_a_heading_are_rows_that_are_not_items(tmp_path):
    view, _ = opened(tmp_path)
    assert "root.m.surface.row[2].divider" in view._built.specs and "root.m.surface.row[2].item" not in view._built.specs
    heading = view.node("root.m.surface.row[3].heading")
    assert heading.get("text") == "Share" and heading.get("fill") == role(view, "on_surface_variant") and "root.m.surface.row[3].item" not in view._built.specs


def test_pressing_an_item_chooses_it_and_closes_the_menu(tmp_path):
    view, vm = opened(tmp_path)
    view.window.simulate("click", node=row(view, 1))
    settle(view, 6)
    assert vm.chosen.get() == "copy" and vm.open.get() is False and not view._shown_layers


def test_a_disabled_item_does_not_respond(tmp_path):
    view, vm = opened(tmp_path)
    view.window.simulate("click", node=row(view, 4))
    settle(view, 6)
    assert vm.chosen.get() == "" and vm.open.get() is True and row(view, 4).get("disabled") is True


def test_escape_and_a_press_outside_close_it_without_choosing(tmp_path):
    view, vm = opened(tmp_path)
    view.window.simulate("key_down", key="escape")
    settle(view, 6)
    assert vm.open.get() is False and vm.chosen.get() == ""
    vm.open.set(True)
    settle(view, 8)
    view.window.simulate("pointer_down", x=550, y=450)
    settle(view, 6)
    assert vm.open.get() is False


def test_on_pick_runs_after_an_item_is_chosen(tmp_path):
    view, vm = opened(tmp_path, "on_pick: noted")
    view.window.simulate("click", node=row(view, 0))
    settle(view, 6)
    assert vm.log == ["picked"]


def test_the_arrows_move_between_items_and_one_tab_stop(tmp_path):
    view, _ = opened(tmp_path)
    tab = [row(view, 0).get("tab_index"), row(view, 1).get("tab_index"), row(view, 5, "parent_item").get("tab_index")]
    assert tab.count(0) == 1
    row(view, 0).focus()
    view.window.simulate("key_down", key="arrow_down")
    settle(view, 4)
    assert row(view, 1).get("focused") is True


def test_enter_on_a_focused_item_chooses_it(tmp_path):
    view, vm = opened(tmp_path)
    row(view, 1).focus()
    settle(view, 2)
    view.window.simulate("key_down", key="enter")
    settle(view, 6)
    assert vm.chosen.get() == "copy"


def test_check_mode_flips_the_checks_and_shows_them(tmp_path):
    items = "[{value: bold, label: Bold}, {value: italic, label: Italic}]"
    view, vm = opened(tmp_path, 'mode: check, checks: "{{ checks }}"', items)
    assert row(view, 0).get("checked") is True and row(view, 1).get("checked") is False
    view.window.simulate("click", node=row(view, 1))
    settle(view, 6)
    assert vm.checks.get() == ["bold", "italic"]
    vm.open.set(True)
    settle(view, 8)
    assert row(view, 1).get("checked") is True
    view.window.simulate("click", node=row(view, 0))
    settle(view, 6)
    assert vm.checks.get() == ["italic"]


def test_radio_mode_keeps_one_checked(tmp_path):
    items = "[{value: a, label: A}, {value: b, label: B}, {value: c, label: C}]"
    view, vm = opened(tmp_path, 'mode: radio, selected: "{{ picked }}"', items)
    assert [row(view, i).get("checked") for i in range(3)] == [False, True, False]
    view.window.simulate("click", node=row(view, 2))
    settle(view, 6)
    assert vm.picked.get() == "c"


def test_an_item_with_a_submenu_has_a_chevron_and_opens_another_menu_beside_it(tmp_path):
    view, vm = opened(tmp_path)
    parent = row(view, 5, "parent_item")
    assert parent.get("expanded") is True and "root.m.surface.row[5].parent_item.chevron" in view._built.specs
    assert len(view._shown_layers) == 1
    view.window.simulate("click", node=parent)
    settle(view, 8)
    sub = view.node("root.m.surface.row[5].sub.surface")
    assert len(view._shown_layers) == 2
    assert sub.get("layout_x") >= parent.get("layout_x") + parent.get("layout_width") - 1 and abs(sub.get("layout_y") - parent.get("layout_y")) <= 12


def test_the_right_arrow_opens_a_submenu_too(tmp_path):
    view, _ = opened(tmp_path)
    row(view, 5, "parent_item").focus()
    settle(view, 2)
    view.window.simulate("key_down", key="arrow_right")
    settle(view, 8)
    assert len(view._shown_layers) == 2


def test_choosing_in_a_submenu_sets_chosen_and_closes_both_menus(tmp_path):
    view, vm = opened(tmp_path)
    view.window.simulate("click", node=row(view, 5, "parent_item"))
    settle(view, 8)
    view.window.simulate("click", node=view.node("root.m.surface.row[5].sub.surface.row[1].item"))
    settle(view, 8)
    assert vm.chosen.get() == "link" and vm.open.get() is False and not view._shown_layers


def test_escape_closes_the_submenu_first(tmp_path):
    view, vm = opened(tmp_path)
    view.window.simulate("click", node=row(view, 5, "parent_item"))
    settle(view, 8)
    view.window.simulate("key_down", key="escape")
    settle(view, 6)
    assert len(view._shown_layers) == 1 and vm.open.get() is True
    view.window.simulate("click", node=row(view, 5, "parent_item"))
    settle(view, 8)
    assert len(view._shown_layers) == 2  # it can be opened again


def test_the_width_is_held_between_112_and_280(tmp_path):
    view, _ = opened(tmp_path, "width: 900")
    assert surface(view).get("layout_width") == 280.0
    (tmp_path / "n").mkdir()
    narrow, _ = opened(tmp_path / "n", "width: 10")
    assert surface(narrow).get("layout_width") == 112.0
