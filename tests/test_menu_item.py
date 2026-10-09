"""#169: one row of a menu -- 48 tall, an icon or a check, a shortcut or a chevron."""

import pytest

from tesserae import App, Signal, ViewModel, tokens
from tesserae.shipped import shipped_views


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.clicks = Signal(0)

    def bump(self):
        self.clicks.set(self.clicks.get() + 1)


def opened(tmp_path, props="label: Cut"):
    (tmp_path / "Views").mkdir(exist_ok=True)
    lines = "\n    ".join(props.split(", "))
    (tmp_path / "Views" / "Main_View.yaml").write_text(f"""name: main
widget: Container
style: {{width: 300, height: 200, align_content: top_left}}
children:
  - widget: MenuItem
    name: mi
    {lines}
    handlers: {{on_click: bump}}
""")
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    for _ in range(6):
        view.window.advance(16)
    return view, app.bindings.viewmodel_for("main")


def role(view, name):
    return (view._scheme or tokens.BASELINE)[name]


def mi(view, part=""):
    return view.node("root.mi" + (f".{part}" if part else ""))


def test_it_is_shipped():
    assert "MenuItem" in shipped_views()


def test_a_row_is_48_tall_as_wide_as_its_place_with_12_pixels_each_side(tmp_path):
    view, _ = opened(tmp_path)
    assert (mi(view).get("layout_width"), mi(view).get("layout_height")) == (300.0, 48.0)
    label = mi(view, "label")
    assert label.get("layout_x") == mi(view).get("layout_x") + 12 and label.get("font_size") == 14.0 and label.get("fill") == role(view, "on_surface")


def test_an_icon_is_24_pixels_with_12_before_the_label(tmp_path):
    view, _ = opened(tmp_path, "label: Cut, icon: home")
    icon, label = mi(view, "lead"), mi(view, "label")
    assert (icon.get("layout_width"), icon.get("fill")) == (24.0, role(view, "on_surface_variant")) and label.get("layout_x") == icon.get("layout_x") + 24 + 12


def test_trailing_text_sits_at_the_far_end_in_on_surface_variant(tmp_path):
    view, _ = opened(tmp_path, "label: Cut, trailing_text: Ctrl+X")
    t = mi(view, "trailing")
    assert t.get("text") == "Ctrl+X" and t.get("fill") == role(view, "on_surface_variant")
    assert t.get("layout_x") + t.get("layout_width") == mi(view).get("layout_x") + 300 - 12


def test_a_chevron_marks_a_submenu(tmp_path):
    view, _ = opened(tmp_path, "label: Share, submenu: true")
    c = mi(view, "chevron")
    assert c.get("layout_x") + 24 == mi(view).get("layout_x") + 300 - 12 and mi(view).get("expanded") is True


def test_checked_shows_a_check_unchecked_keeps_the_room_and_null_is_no_check(tmp_path):
    view, _ = opened(tmp_path, "label: Bold, checked: true")
    assert mi(view).get("checked") is True and view._built.specs["root.mi.lead"]["icon"] == {"name": "check"}
    (tmp_path / "u").mkdir()
    off, _ = opened(tmp_path / "u", "label: Bold, checked: false")
    assert off.node("root.mi.label").get("layout_x") == off.node("root.mi").get("layout_x") + 12 + 24 + 12 and off.node("root.mi").get("checked") is False
    (tmp_path / "n").mkdir()
    none, _ = opened(tmp_path / "n")
    assert none.node("root.mi.label").get("layout_x") == none.node("root.mi").get("layout_x") + 12 and none.node("root.mi").get("checked") is None


def test_it_is_a_pressable_menu_item_named_by_its_label_that_runs_the_calls_handler(tmp_path):
    view, vm = opened(tmp_path)
    assert mi(view).get("role") == "menuitem" and mi(view).get("label") == "Cut" and mi(view).get("focusable")
    view.window.simulate("click", node=mi(view))
    assert vm.clicks.get() == 1


def test_a_disabled_item_is_dimmed_and_does_not_respond(tmp_path):
    view, vm = opened(tmp_path, "label: Cut, disabled: true")
    view.window.simulate("click", node=mi(view))
    assert vm.clicks.get() == 0 and mi(view).get("disabled") is True and mi(view).get("opacity") < 0.5
