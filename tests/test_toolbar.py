"""#172 and #173: the Material 3 toolbar -- docked and floating, with items, an overflow menu, an action button and hide-on-scroll."""

import pytest

from tesserae import App, Signal, ViewModel, tokens
from tesserae.shipped import shipped_views

ITEMS = "[{value: bold, icon: format_bold, label: Bold}, {value: italic, icon: format_italic, label: Italic}, {value: link, icon: link, label: Link, disabled: true}]"
MORE = "[{value: print, label: Print}, {value: share, label: Share}]"


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.chosen = Signal("")
        self.hide = Signal(False)
        self.log = []

    def add(self):
        self.log.append("add")


def opened(tmp_path, props="", width=600, items=ITEMS):
    (tmp_path / "Views").mkdir(exist_ok=True)
    lines = "\n    ".join(props.split("; ")) if props else ""
    (tmp_path / "Views" / "Main_View.yaml").write_text(f"""name: main
widget: Container
style: {{width: 600, height: 400, align_content: top_left, flex_direction: vertical}}
children:
  - widget: Toolbar
    name: tb
    items: {items}
    chosen: "{{{{ chosen }}}}"
    hidden: "{{{{ hide }}}}"
    {lines}
""")
    app = App(root=tmp_path, width=width, height=400)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    for _ in range(8):
        view.window.advance(16)
    return view, app.bindings.viewmodel_for("main")


def role(view, name):
    return (view._scheme or tokens.BASELINE)[name]


def settle(view, n=30):
    for _ in range(n):
        view.window.advance(16)


def tb(view):
    return view.node("root.tb")


def test_it_is_shipped():
    assert "Toolbar" in shipped_views()


def test_docked_spans_the_width_is_64_tall_on_surface_container(tmp_path):
    view, _ = opened(tmp_path)
    t = tb(view)
    assert t.get("layout_width") == 600.0 and t.get("layout_height") == 64.0 and t.get("fill") == role(view, "surface_container")


def test_floating_is_a_pill_with_a_shadow_as_long_as_its_buttons(tmp_path):
    view, _ = opened(tmp_path, "variant: floating")
    t = tb(view)
    assert t.get("layout_width") < 600 and t.get("layout_height") == 64.0 and t.get("corner_radius") == 9999.0 and t.get("shadows")


def test_floating_vertical_is_a_column_64_wide(tmp_path):
    view, _ = opened(tmp_path, "variant: floating; orientation: vertical")
    t = tb(view)
    first, last = view.node("root.tb.group.item[bold]"), view.node("root.tb.group.item[italic]")
    assert t.get("layout_width") == 64.0 and t.get("layout_height") > 64 and last.get("layout_y") > first.get("layout_y") and last.get("layout_x") == first.get("layout_x")


def test_vibrant_uses_primary_container_and_the_icons_on_primary_container(tmp_path):
    view, _ = opened(tmp_path, "vibrant: true")
    assert tb(view).get("fill") == role(view, "primary_container")
    assert view.node("root.tb.group.item[bold].icon").get("fill") == role(view, "on_primary_container")


def test_pressing_an_item_sets_chosen(tmp_path):
    view, vm = opened(tmp_path)
    view.window.simulate("click", node=view.node("root.tb.group.item[italic]"))
    settle(view, 4)
    assert vm.chosen.get() == "italic"


def test_a_disabled_item_does_not_respond(tmp_path):
    view, vm = opened(tmp_path)
    view.window.simulate("click", node=view.node("root.tb.group.item[link]"))
    settle(view, 4)
    assert vm.chosen.get() == ""


def test_every_item_has_a_label_for_a_screen_reader(tmp_path):
    view, _ = opened(tmp_path)
    assert [view.node(f"root.tb.group.item[{k}]").get("label") for k in ("bold", "italic", "link")] == ["Bold", "Italic", "Link"]
    assert tb(view).get("role") == "group" and tb(view).get("label") == "Toolbar"


def test_the_overflow_menu_opens_under_the_more_button_and_chooses(tmp_path):
    view, vm = opened(tmp_path, f"overflow: {MORE}")
    more = view.node("root.tb.more")
    assert more.get("expanded") is False
    view.window.simulate("click", node=more)
    settle(view, 8)
    assert view._shown_layers and more.get("expanded") is True
    view.window.simulate("click", node=view.node("root.tb.menu.surface.row[1].item"))
    settle(view, 8)
    assert vm.chosen.get() == "share" and not view._shown_layers


def test_no_more_button_without_overflow(tmp_path):
    view, _ = opened(tmp_path)
    assert "root.tb.more" not in view._built.specs


def test_the_action_button_is_at_the_end_and_calls_on_fab(tmp_path):
    view, vm = opened(tmp_path, "fab_icon: plus; fab_label: Add; on_fab: add")
    fab, last = view.node("root.tb.fab"), view.node("root.tb.group.item[italic]")
    assert fab.get("layout_x") > last.get("layout_x") and abs(fab.get("layout_x") + fab.get("layout_width") - (600 - 16)) < 0.5
    view.window.simulate("click", node=fab)
    settle(view, 4)
    assert vm.log == ["add"]


def test_hidden_fades_it_out_and_takes_it_out_of_the_tab_order(tmp_path):
    view, vm = opened(tmp_path, "fab_icon: plus; fab_label: Add; on_fab: add")
    assert tb(view).get("opacity") == 1.0
    vm.hide.set(True)
    settle(view, 30)
    assert tb(view).get("opacity") == 0.0 and view.node("root.tb.fab").get("disabled")
    view.window.simulate("click", node=view.node("root.tb.fab"))
    settle(view, 4)
    assert vm.log == []


def test_disabled_stops_every_button(tmp_path):
    view, vm = opened(tmp_path, "disabled: true")
    view.window.simulate("click", node=view.node("root.tb.group.item[bold]"))
    settle(view, 4)
    assert vm.chosen.get() == ""


def test_arrow_keys_move_between_the_buttons(tmp_path):
    view, _ = opened(tmp_path)
    view.node("root.tb.group.item[bold]").focus()
    view.window.simulate("key_down", key="arrow_right")
    settle(view, 2)
    assert view.node("root.tb.group.item[italic]").get("focused") is True


def test_a_slot_holds_your_own_content_after_the_items(tmp_path):
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text(f"""name: main
widget: Container
style: {{width: 600, height: 400, align_content: top_left}}
children:
  - widget: Toolbar
    name: tb
    items: {ITEMS}
    children:
      - {{widget: Text, name: extra, text: Hello, typography_role: body_medium, style: {{foreground: on_surface}}}}
""")
    app = App(root=tmp_path, width=600, height=400)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    settle(view, 8)
    assert view.node("root.tb.extra").get("layout_x") > view.node("root.tb.group.item[italic]").get("layout_x")


# -- fit: what does not fit moves into the overflow menu -----------------------------------------------------------------------

MANY = "[" + ", ".join(f"{{value: v{i}, icon: star, label: Item {i}}}" for i in range(10)) + "]"


def count(view):
    return len([k for k in view._built.specs if k.startswith("root.tb.group.item[") and k.endswith("]")])


def test_without_fit_every_item_shows_however_narrow(tmp_path):
    (tmp_path / "a").mkdir()
    view, _ = opened(tmp_path / "a", "width: 200", items=MANY)
    assert count(view) == 10 and "root.tb.more" not in view._built.specs


def test_fit_keeps_the_items_that_fit_and_puts_the_rest_in_the_menu_under_a_more_button(tmp_path):
    view, vm = opened(tmp_path, "fit: true; width: 300", items=MANY)
    n = count(view)
    assert 0 < n < 10 and "root.tb.more" in view._built.specs
    more = view.node("root.tb.more")
    assert more.get("layout_x") + more.get("layout_width") <= 300 - 16 + 0.5
    view.window.simulate("click", node=more)
    settle(view, 8)
    rows = [k for k in view._built.specs if k.startswith("root.tb.menu.surface.row[") and k.endswith(".item")]
    assert len(rows) == 10 - n
    view.window.simulate("click", node=view.node(rows[0]))
    settle(view, 8)
    assert vm.chosen.get() == f"v{n}"


def test_fit_with_room_for_everything_shows_everything_and_no_more_button(tmp_path):
    view, _ = opened(tmp_path, "fit: true; width: 400")
    assert count(view) == 3 and "root.tb.more" not in view._built.specs


def test_fit_follows_the_width_it_is_given(tmp_path):
    view, vm = opened(tmp_path, "fit: true; width: 600", items=MANY)
    assert count(view) == 10
    (tmp_path / "b").mkdir()
    narrow, _ = opened(tmp_path / "b", "fit: true; width: 200", items=MANY)
    assert count(narrow) < count(view)


def test_a_floating_toolbar_fits_to_max_length_and_the_fab_takes_room(tmp_path):
    view, _ = opened(tmp_path, "fit: true; variant: floating; max_length: 300", items=MANY)
    with_fab_dir = tmp_path / "f"
    with_fab_dir.mkdir()
    fab, _ = opened(with_fab_dir, "fit: true; variant: floating; max_length: 300; fab_icon: plus; fab_label: Add", items=MANY)
    assert 0 < count(fab) < count(view) < 10 and tb(view).get("layout_width") <= 300.5


def test_spilled_items_and_the_callers_overflow_rows_share_one_menu_with_a_divider(tmp_path):
    view, _ = opened(tmp_path, f"fit: true; width: 300; overflow: {MORE}", items=MANY)
    view.window.simulate("click", node=view.node("root.tb.more"))
    settle(view, 8)
    labels = [view.node(k).get("label") for k in view._built.specs if k.startswith("root.tb.menu.surface.row[") and k.endswith(".item")]
    assert labels[-2:] == ["Print", "Share"] and len(labels) == 10 - count(view) + 2
    assert any(k.endswith(".divider") for k in view._built.specs if k.startswith("root.tb.menu"))
