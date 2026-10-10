"""#178: the Material 3 slider in the view language -- a range and steps, ticks, a value bubble, a bound value that follows the drag."""

import pytest

from tesserae import App, Signal, ViewModel, tokens
from tesserae.spec.nodes import LoadError


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.volume = Signal(30.0)
        self.ends = []
        self.live = []

    def committed(self):
        self.ends.append(self.volume.get())

    def moving(self):
        self.live.append(self.volume.get())


def opened(tmp_path, body, **kwargs):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        "name: main\nwidget: Container\nstyle: {flex_direction: vertical, align_content: top_left, width: 300, height: 200}\nchildren:\n" + body)
    app = App(root=tmp_path, **kwargs)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    for _ in range(3):
        view.window.advance(16)
    return view, app.bindings.viewmodel_for("main")


SLIDER = '  - {widget: Slider, name: s, min: 0, max: 100, value: "{{ volume }}", style: {width: 220}%s}\n'


def control(view):
    return view._built.controls["root.s"]


def role(view, name):
    return (view._scheme or tokens.BASELINE)[name]


def drag(view, fractions):
    """Press at the first fraction of the slider's travel, move through the rest, release at the last."""
    node = view.node("root.s")
    c = control(view)
    x = lambda f: c.HANDLE / 2 + f * c._span  # noqa: E731
    y = node.get("layout_y") + 24
    view.window.simulate("pointer_down", node, x=x(fractions[0]), y=24)
    for f in fractions[1:]:
        view.window.simulate("pointer_move", x=node.get("layout_x") + x(f), y=y)
    view.window.simulate("pointer_up", x=node.get("layout_x") + x(fractions[-1]), y=y)
    view.window.advance(16)


def test_a_slider_has_a_four_pixel_track_a_twenty_pixel_handle_and_the_role_of_a_slider(tmp_path):
    view, _ = opened(tmp_path, SLIDER % "")
    c = control(view)
    assert c.inactive.get("layout_height") == 4.0 and c.handle.get("layout_width") == 20.0 and c.node.get("role") == "slider"
    assert c.handle.get("fill") == role(view, "primary") and c.inactive.get("fill") == role(view, "surface_container_highest")
    assert (c.node.get("value_min"), c.node.get("value_max"), c.node.get("value")) == (0.0, 100.0, 30.0)


def test_the_handle_sits_at_its_share_of_the_range(tmp_path):
    view, _ = opened(tmp_path, SLIDER % "")
    c = control(view)
    assert c.handle.get("translate_x") == pytest.approx(0.3 * c._span) and c.active.get("layout_width") == pytest.approx(0.3 * c._span)


def test_dragging_moves_the_value_and_a_bound_signal_follows_while_it_goes(tmp_path):
    view, vm = opened(tmp_path, SLIDER % "")
    node = view.node("root.s")
    c = control(view)
    view.window.simulate("pointer_down", node, x=c.HANDLE / 2 + 0.5 * c._span, y=24)
    assert vm.volume.get() == pytest.approx(50.0)  # at the press, not at the end
    view.window.simulate("pointer_move", x=node.get("layout_x") + c.HANDLE / 2 + 0.8 * c._span, y=node.get("layout_y") + 24)
    assert vm.volume.get() == pytest.approx(80.0)  # while it is still down
    view.window.simulate("pointer_up", x=0, y=0)


def test_on_input_hears_every_step_of_a_drag_and_on_change_only_the_end(tmp_path):
    body = SLIDER % ', handlers: {on_input: moving, on_change: committed}'
    view, vm = opened(tmp_path, body)
    drag(view, [0.2, 0.4, 0.6, 0.9])
    assert len(vm.live) >= 4 and vm.live[-1] == pytest.approx(90.0)
    assert vm.ends == [pytest.approx(90.0)]


def test_a_step_snaps_the_value(tmp_path):
    view, vm = opened(tmp_path, SLIDER % ", step: 10")
    drag(view, [0.37])
    assert vm.volume.get() == 40.0


def test_the_keys_step_page_and_go_to_the_ends(tmp_path):
    view, vm = opened(tmp_path, SLIDER % ", step: 10")
    view.node("root.s").focus()
    view.window.simulate("key_down", key="arrow_right")
    assert vm.volume.get() == 40.0
    view.window.simulate("key_down", key="page_down")
    assert vm.volume.get() == 0.0
    view.window.simulate("key_down", key="end")
    assert vm.volume.get() == 100.0
    view.window.simulate("key_down", key="home")
    assert vm.volume.get() == 0.0


def test_a_screen_reader_can_increment_and_set(tmp_path):
    view, vm = opened(tmp_path, SLIDER % ", step: 10")
    view.window.simulate("a11y_action", view.node("root.s"), action="increment")
    assert vm.volume.get() == 40.0
    view.window.simulate("a11y_action", view.node("root.s"), action="set_value", value=75.0)
    assert vm.volume.get() == 80.0


def test_following_a_signal_moves_the_handle(tmp_path):
    view, vm = opened(tmp_path, SLIDER % "")
    vm.volume.set(100.0)
    for _ in range(3):
        view.window.advance(16)
    assert control(view).handle.get("translate_x") == pytest.approx(control(view)._span)


def test_ticks_mark_each_step_and_colour_the_ones_reached(tmp_path):
    view, _ = opened(tmp_path, SLIDER % ", step: 25, ticks: true")
    c = control(view)
    assert len(c.tick_marks) == 5
    reached = [m.get("fill") for m in c.tick_marks]
    assert reached[0] == role(view, "on_primary") and reached[1] == role(view, "on_primary") and reached[4] == role(view, "on_surface_variant")
    assert [round(m.get("layout_x") - c.tick_marks[0].get("layout_x")) for m in c.tick_marks] == [round(i * c._span / 4) for i in range(5)]


def test_no_step_no_ticks(tmp_path):
    view, _ = opened(tmp_path, SLIDER % ", ticks: true")
    assert control(view).tick_marks == []


def test_the_value_bubble_shows_while_dragging_and_on_keyboard_focus_only(tmp_path):
    view, vm = opened(tmp_path, SLIDER % ", value_indicator: true, step: 10")
    c = control(view)
    assert c.bubble.get("visible") is False
    node = view.node("root.s")
    view.window.simulate("pointer_down", node, x=c.HANDLE / 2 + 0.5 * c._span, y=24)
    assert c.bubble.get("visible") is True and c.bubble_text.get("text") == "50"
    view.window.simulate("pointer_up", x=0, y=0)
    assert c.bubble.get("visible") is False  # a mouse press that focused it is not the keyboard


def test_the_value_bubble_shows_on_keyboard_focus_and_goes_when_focus_leaves(tmp_path):
    view, _ = opened(tmp_path, (SLIDER % ", value_indicator: true, step: 10") + "  - {widget: Checkbox, name: x}\n")
    c = control(view)
    view.window.simulate("key_down", key="tab")
    view.window.advance(16)
    assert c.bubble.get("visible") is True and c.bubble_text.get("text") == "30"
    view.window.simulate("key_down", key="tab")  # on to the checkbox
    view.window.advance(16)
    assert c.bubble.get("visible") is False


def test_without_value_indicator_there_is_never_a_bubble(tmp_path):
    view, _ = opened(tmp_path, SLIDER % "")
    view.window.simulate("key_down", key="tab")
    view.window.advance(16)
    assert control(view).bubble.get("visible") is False


def test_disabled_is_dimmed_and_does_not_move(tmp_path):
    view, vm = opened(tmp_path, SLIDER % ", disabled: true")
    drag(view, [0.9])
    view.window.simulate("key_down", key="end")
    assert vm.volume.get() == 30.0 and not view.node("root.s").get("focusable")


def test_the_label_names_it_and_the_colour_is_the_foreground(tmp_path):
    view, _ = opened(tmp_path, SLIDER.replace("style: {width: 220}", "style: {width: 220, foreground: '#CC3300'}") % ", label: Volume")
    assert view.node("root.s").get("label") == "Volume" and control(view).handle.get("fill") == (0xCC, 0x33, 0x00, 255)


def test_a_range_with_no_room_is_an_error_naming_the_widget(tmp_path):
    with pytest.raises(Exception, match="max > min"):
        opened(tmp_path, '  - {widget: Slider, name: s, min: 5, max: 5}\n')


def test_the_default_range_is_zero_to_one(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: Slider, name: s, value: 0.5, style: {width: 220}}\n")
    assert (view.node("root.s").get("value_min"), view.node("root.s").get("value_max")) == (0.0, 1.0)


def test_on_input_on_something_that_is_not_a_slider_says_so(tmp_path):
    with pytest.raises(Exception, match="on_input is for a Slider"):
        opened(tmp_path, '  - {widget: Container, name: c, handlers: {on_input: moving}}\n')


def test_a_key_is_one_input_and_one_change_and_a_key_that_moves_nothing_is_neither(tmp_path):
    body = SLIDER % ', step: 10, handlers: {on_input: moving, on_change: committed}'
    view, vm = opened(tmp_path, body)
    view.node("root.s").focus()
    view.window.simulate("key_down", key="arrow_right")
    assert vm.live == [40.0] and vm.ends == [40.0]
    view.window.simulate("key_down", key="end")
    view.window.simulate("key_down", key="end")  # already there
    assert vm.live == [40.0, 100.0] and vm.ends == [40.0, 100.0]


def test_a_range_can_start_below_zero(tmp_path):
    view, vm = opened(tmp_path, '  - {widget: Slider, name: s, min: -50, max: 50, value: 0, style: {width: 220}}\n')
    c = control(view)
    assert c.handle.get("translate_x") == pytest.approx(c._span / 2)
    assert (view.node("root.s").get("value_min"), view.node("root.s").get("value_max")) == (-50.0, 50.0)


def test_moving_within_one_step_is_not_a_new_input(tmp_path):
    view, vm = opened(tmp_path, SLIDER % ", step: 10, handlers: {on_input: moving}")
    drag(view, [0.5, 0.51, 0.52, 0.49])
    assert vm.live == [50.0]  # the press set it to 50; the small moves stayed on the same step


def test_a_flex_expanded_slider_maps_the_pointer_with_its_laid_out_width(tmp_path):
    """#252: the span was the width at build (220), so a press in the middle of a slider laid out at 300 read the wrong value."""
    view, vm = opened(tmp_path, '  - widget: Container\n    name: row\n    style: {flex_direction: horizontal, width: 300, height: 48}\n    children:\n'
                      '      - {widget: Slider, name: s, min: 0, max: 100, value: "{{ volume }}", style: {width: 120, flex: expand_horizontal}}\n')
    node = view.node("root.row.s")
    laid = node.get("layout_width")
    assert laid > 250  # it did expand past the built 120
    c = view._built.controls["root.row.s"]
    handle = c.HANDLE
    view.window.simulate("pointer_down", node, x=handle / 2 + (laid - handle) / 2, y=24)
    view.window.simulate("pointer_up", x=node.get("layout_x") + laid / 2, y=node.get("layout_y") + 24)
    assert vm.volume.get() == pytest.approx(50.0, abs=1.0)
    # and the track and the handle follow the laid-out width, not the built one
    assert c.inactive.get("width") == pytest.approx(laid - handle, abs=0.5)


def test_a_flex_expanded_slider_moves_its_tick_marks_and_its_handle_with_the_laid_out_width(tmp_path):
    view, vm = opened(tmp_path, '  - widget: Container\n    name: row\n    style: {flex_direction: horizontal, width: 300, height: 48}\n    children:\n'
                      '      - {widget: Slider, name: s, min: 0, max: 100, step: 25, ticks: true, value: "{{ volume }}", style: {width: 120, flex: expand_horizontal}}\n')
    c = view._built.controls["root.row.s"]
    laid = view.node("root.row.s").get("layout_width")
    view.window.simulate("resize", width=300, height=200)  # headless `advance` lays out but draws no frame; the slider looks on a frame or a resize
    assert c.width == pytest.approx(laid, abs=0.5) and laid > 250
    assert c.tick_marks[-1].get("x") == pytest.approx(c.HANDLE / 2 + c._span - 1.0)
    vm.volume.set(100.0)
    view.window.advance(16)
    assert c.handle.get("translate_x") == pytest.approx(c._span)


def test_a_slider_with_its_built_width_is_left_alone(tmp_path):
    view, _ = opened(tmp_path, SLIDER % "")
    assert control(view).width == 220.0
