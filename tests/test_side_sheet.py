"""#154, #155: the Material 3 side sheets -- standard (inline) and modal (over a scrim), with a header, scrolling content and actions."""

import pytest

from tesserae import App, Signal, ViewModel, tokens
from tesserae.shipped import shipped_views


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.open = Signal(True)
        self.log = []

    def went_back(self):
        self.log.append("back")


def opened(tmp_path, props="", children="", widget="SideSheet", after=""):
    (tmp_path / "Views").mkdir(exist_ok=True)
    props_lines = "\n    ".join(props.split(", ")) if props else ""
    kids = children or "      - {widget: Text, name: body, text: Hello, typography_role: body_medium, style: {foreground: on_surface}}\n"
    (tmp_path / "Views" / "Main_View.yaml").write_text(f"""name: main
widget: Container
style: {{flex_direction: horizontal, align_content: top_left, width: 700, height: 400}}
children:
  - {{widget: Container, name: main, style: {{flex: fill, height: 100%, background: surface_container}}}}
  - widget: {widget}
    name: s
    open: "{{{{ open }}}}"
    title: Filters
    {props_lines}
    children:
{kids}{after}""")
    app = App(root=tmp_path, width=700, height=400)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    for _ in range(20):
        view.window.advance(16)
    return view, app.bindings.viewmodel_for("main")


def role(view, name):
    return (view._scheme or tokens.BASELINE)[name]


def s(view, part=""):
    return view.node("root.s" + (f".{part}" if part else ""))


def settle(view, n=30):
    for _ in range(n):
        view.window.advance(16)


def test_they_are_shipped():
    assert {"SideSheet", "SideSheetPanel"} <= set(shipped_views())


def outer(view, path):
    return view._built.outer[path]


def test_a_standard_sheet_is_a_surface_column_at_the_end_and_pushes_the_content(tmp_path):
    view, _ = opened(tmp_path)
    assert (s(view).get("layout_width"), s(view).get("layout_height")) == (360.0, 400.0)
    assert s(view).get("layout_x") == 340.0 and view.node("root.main").get("layout_width") == 340.0  # the content gave up its room
    assert s(view).get("fill") == role(view, "surface")


def test_the_header_has_the_title_in_title_large_and_a_close_button_at_the_far_end(tmp_path):
    view, _ = opened(tmp_path)
    title, close = s(view, "panel.header.title"), s(view, "panel.header.close")
    assert title.get("font_size") == 22.0 and title.get("fill") == role(view, "on_surface") and title.get("level") == 2
    assert title.get("layout_x") == s(view).get("layout_x") + 24
    assert close.get("layout_x") + close.get("layout_width") == s(view).get("layout_x") + 360 - 16 and close.get("label") == "Close"


def test_the_close_button_closes_the_sheet_and_the_content_gets_its_room_back(tmp_path):
    view, vm = opened(tmp_path)
    view.window.simulate("click", node=s(view, "panel.header.close"))
    settle(view)
    assert vm.open.get() is False and s(view).get("layout_width") == 0.0 and view.node("root.main").get("layout_width") == 700.0


def test_opening_makes_room_again(tmp_path):
    view, vm = opened(tmp_path)
    vm.open.set(False)
    settle(view)
    vm.open.set(True)
    settle(view)
    assert s(view).get("layout_width") == 360.0 and view.node("root.main").get("layout_width") == 340.0


def test_the_width_eases_rather_than_jumping(tmp_path):
    view, vm = opened(tmp_path)
    vm.open.set(False)
    for _ in range(6):
        view.window.advance(16)
    assert 0.0 < s(view).get("layout_width") < 360.0


def test_the_width_is_held_between_256_and_400(tmp_path):
    view, _ = opened(tmp_path, "width: 900")
    assert s(view).get("layout_width") == 400.0
    (tmp_path / "n").mkdir()
    narrow, _ = opened(tmp_path / "n", "width: 100")
    assert s(narrow).get("layout_width") == 256.0


def test_a_back_button_runs_on_back(tmp_path):
    view, vm = opened(tmp_path, "back: true, on_back: went_back")
    back = s(view, "panel.header.back")
    assert back.get("label") == "Back" and back.get("layout_x") < s(view, "panel.header.title").get("layout_x")
    view.window.simulate("click", node=back)
    assert vm.log == ["back"]


def test_a_sheet_that_is_not_closable_has_no_close_button(tmp_path):
    view, _ = opened(tmp_path, "closable: false")
    assert "root.s.panel.header.close" not in view._built.specs


def test_the_content_is_the_childrens_and_the_actions_sit_at_the_bottom_right(tmp_path):
    after = "      - {widget: Button, name: apply, slot: actions, label: Apply, variant: filled}\n      - {widget: Button, name: cancel, slot: actions, label: Cancel, variant: text}\n"
    view, _ = opened(tmp_path, after=after)
    assert s(view, "body").get("layout_y") >= s(view).get("layout_y") + 56
    apply, cancel = s(view, "apply"), s(view, "cancel")
    assert apply.get("layout_y") > 300 and cancel.get("layout_x") + cancel.get("layout_width") == s(view).get("layout_x") + 360 - 16 - 8
    assert apply.get("layout_x") + apply.get("layout_width") + 8 == cancel.get("layout_x")


def test_tall_content_scrolls_and_a_line_shows_over_the_actions(tmp_path):
    kids = "      - {widget: Container, name: tall, style: {width: 100, height: 900}}\n"
    view, _ = opened(tmp_path, children=kids, after="      - {widget: Button, name: ok, slot: actions, label: OK, variant: text}\n")
    scroller = outer(view, "root.s.panel.content")
    assert scroller.get("layout_height") < 400 and "root.s.panel.line" not in view._built.specs
    view.window.simulate("wheel", node=scroller, delta_x=0.0, delta_y=80.0)
    settle(view, 4)
    assert "root.s.panel.line" in view._built.specs


def test_the_sheet_is_where_it_is_put_so_first_in_the_row_is_the_start_side(tmp_path):
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text("""name: main
widget: Container
style: {flex_direction: horizontal, align_content: top_left, width: 700, height: 400}
children:
  - {widget: SideSheet, name: s, open: true, title: Filters}
  - {widget: Container, name: main, style: {flex: fill, height: 100%}}
""")
    app = App(root=tmp_path, width=700, height=400)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    settle(view, 20)
    assert s(view).get("layout_x") == 0.0 and view.node("root.main").get("layout_x") == 360.0


# -- the modal sheet (#155) ---------------------------------------------------------------------------------------------------


def modal(tmp_path, props="", **kw):
    view, vm = opened(tmp_path, props, widget="SideSheetModal", **kw)
    vm.open.set(False)
    settle(view, 4)
    vm.open.set(True)
    settle(view, 6)
    return view, vm


def test_the_modal_sheet_is_a_scrim_with_a_panel_at_the_end_taking_no_room_from_the_content(tmp_path):
    view, _ = modal(tmp_path)
    assert view.node("root.main").get("layout_width") == 700.0  # it is over the content, not beside it
    sheet = s(view, "sheet")
    assert (sheet.get("layout_width"), sheet.get("layout_height")) == (360.0, 400.0) and sheet.get("layout_x") == 340.0
    assert view._built.nodes["root.s"].get("fill")[3] == round(0.32 * 255)


def test_the_modal_panel_is_surface_container_low_with_16_pixel_corners_on_its_open_side_at_level_one(tmp_path):
    view, _ = modal(tmp_path)
    sheet = s(view, "sheet")
    assert sheet.get("fill") == role(view, "surface_container_low") and sheet.get("shadows")
    assert sheet.get("corner_radius") == (16.0, 0.0, 0.0, 16.0)


def test_the_modal_sheet_can_come_from_the_start(tmp_path):
    view, _ = modal(tmp_path, "side: start")
    sheet = s(view, "sheet")
    assert sheet.get("layout_x") == 0.0 and sheet.get("corner_radius") == (0.0, 16.0, 16.0, 0.0)


def test_the_modal_sheet_is_a_dialog_named_by_its_title(tmp_path):
    view, _ = modal(tmp_path)
    assert s(view, "sheet").get("role") == "dialog" and s(view, "sheet").get("label") == "Filters"


def test_escape_and_the_scrim_and_the_close_button_close_it(tmp_path):
    view, vm = modal(tmp_path)
    view.window.simulate("key_down", key="escape")
    settle(view, 4)
    assert vm.open.get() is False
    vm.open.set(True)
    settle(view, 6)
    view.window.simulate("pointer_down", x=5, y=5)
    settle(view, 4)
    assert vm.open.get() is False
    vm.open.set(True)
    settle(view, 6)
    view.window.simulate("click", node=s(view, "sheet.panel.header.close"))
    settle(view, 4)
    assert vm.open.get() is False


def test_a_press_inside_the_modal_sheet_does_not_close_it(tmp_path):
    view, vm = modal(tmp_path)
    view.window.simulate("pointer_down", x=500, y=200)
    settle(view, 4)
    assert vm.open.get() is True


def test_not_dismissible_ignores_escape_but_the_close_button_still_closes(tmp_path):
    view, vm = modal(tmp_path, "dismissible: false")
    view.window.simulate("key_down", key="escape")
    view.window.simulate("pointer_down", x=5, y=5)
    settle(view, 4)
    assert vm.open.get() is True
    view.window.simulate("click", node=s(view, "sheet.panel.header.close"))
    settle(view, 4)
    assert vm.open.get() is False


def test_the_modal_sheet_has_the_same_header_content_and_actions(tmp_path):
    after = "      - {widget: Button, name: ok, slot: actions, label: OK, variant: text}\n"
    view, vm = modal(tmp_path, "back: true, on_back: went_back", after=after)
    view.window.simulate("click", node=s(view, "sheet.panel.header.back"))
    assert vm.log == ["back"]
    assert s(view, "body").get("layout_y") >= 56 and s(view, "ok").get("layout_y") > 300
