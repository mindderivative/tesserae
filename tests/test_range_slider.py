"""#250: the range slider -- two handles and two bound values that never cross, each handle its own stop, slider and state layer."""

import pytest

from tesserae import App, Signal, ViewModel, tokens
from tesserae.controls import RangeSlider
from tesserae.spec.nodes import LoadError


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.lo = Signal(20.0)
        self.hi = Signal(70.0)
        self.live = []
        self.ends = []

    def moving(self):
        self.live.append((self.lo.get(), self.hi.get()))

    def committed(self):
        self.ends.append((self.lo.get(), self.hi.get()))


def opened(tmp_path, extra="", style="width: 220", body=None):
    (tmp_path / "Views").mkdir(exist_ok=True)
    node = body or ('  - {widget: RangeSlider, name: s, min: 0, max: 100, low: "{{ lo }}", high: "{{ hi }}", style: {%s}%s}\n' % (style, extra))
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        "name: main\nwidget: Container\nstyle: {flex_direction: vertical, align_content: top_left, width: 300, height: 300}\nchildren:\n" + node)
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    for _ in range(3):
        view.window.advance(16)
    return view, app.bindings.viewmodel_for("main")


def control(view):
    return view._built.controls["root.s"]


def role(view, name):
    return (view._scheme or tokens.BASELINE)[name]


def press(view, along, up=True, y=24):
    """Presses `along` the track (from its start), moves nowhere and lets go."""
    node, c = view.node("root.s"), control(view)
    view.window.simulate("pointer_down", node, x=along, y=y)
    if up:
        view.window.simulate("pointer_up", x=node.get("layout_x") + along, y=node.get("layout_y") + y)
        view.window.advance(16)


def at(view, fraction):
    c = control(view)
    return c._edge + fraction * c._span


def drag(view, start, *stops):
    node = view.node("root.s")
    view.window.simulate("pointer_down", node, x=start, y=24)
    for x in stops:
        view.window.simulate("pointer_move", x=node.get("layout_x") + x, y=node.get("layout_y") + 24)
    view.window.simulate("pointer_up", x=node.get("layout_x") + (stops[-1] if stops else start), y=node.get("layout_y") + 24)
    view.window.advance(16)


def test_two_handles_sit_at_their_share_of_the_range_and_the_track_between_them_is_active(tmp_path):
    view, _ = opened(tmp_path)
    c = control(view)
    assert isinstance(c, RangeSlider)
    assert c.thumbs[0].handle.get("translate_x") == pytest.approx(0.2 * c._span) and c.thumbs[1].handle.get("translate_x") == pytest.approx(0.7 * c._span)
    assert c.active.get("layout_x") == pytest.approx(c._edge + 0.2 * c._span) and c.active.get("layout_width") == pytest.approx(0.5 * c._span)
    assert c.thumbs[0].handle.get("fill") == role(view, "primary") and c.inactive.get("fill") == role(view, "surface_container_highest")


def test_the_group_is_not_a_tab_stop_and_each_handle_is_a_slider_with_its_own_reach(tmp_path):
    view, _ = opened(tmp_path, ", label: Price")
    c = control(view)
    assert c.node.get("role") == "group" and not c.node.get("focusable")
    low, high = c.thumbs[0].node, c.thumbs[1].node
    assert low.get("role") == high.get("role") == "slider" and low.get("focusable") and high.get("focusable")
    assert (low.get("value"), low.get("value_min"), low.get("value_max")) == (20.0, 0.0, 70.0)  # up to the other handle
    assert (high.get("value"), high.get("value_min"), high.get("value_max")) == (70.0, 20.0, 100.0)
    assert low.get("label") == "Price, minimum" and high.get("label") == "Price, maximum"


def test_without_a_label_the_handles_are_the_minimum_and_the_maximum(tmp_path):
    view, _ = opened(tmp_path)
    assert [t.node.get("label") for t in control(view).thumbs] == ["Minimum", "Maximum"]


def test_a_press_on_the_track_moves_the_nearer_handle(tmp_path):
    view, vm = opened(tmp_path)
    press(view, at(view, 0.30))  # nearer the low one (at 20) than the high one (at 70)
    assert vm.lo.get() == pytest.approx(30.0, abs=0.5) and vm.hi.get() == 70.0
    press(view, at(view, 0.60))  # nearer the high one now
    assert vm.hi.get() == pytest.approx(60.0, abs=0.5) and vm.lo.get() == pytest.approx(30.0, abs=0.5)


def test_a_drag_keeps_hold_of_the_handle_it_began_on_and_never_crosses_the_other(tmp_path):
    view, vm = opened(tmp_path)
    drag(view, at(view, 0.2), at(view, 0.5), at(view, 0.95))  # the low handle, taken past the high one
    assert vm.lo.get() == 70.0 and vm.hi.get() == 70.0  # it stops at the high one
    drag(view, at(view, 0.7), at(view, 0.9))  # now both are at 70: the press on the high side takes the high one
    assert vm.lo.get() == 70.0 and vm.hi.get() == pytest.approx(90.0, abs=0.5)


def test_input_is_heard_through_the_drag_and_change_at_its_end_with_both_values(tmp_path):
    view, vm = opened(tmp_path)
    seen = []
    control(view).on_input(lambda pair: seen.append(("input", pair)))
    control(view).on_change(lambda pair: seen.append(("change", pair)))
    drag(view, at(view, 0.7), at(view, 0.8), at(view, 0.9))
    assert [kind for kind, _ in seen].count("input") >= 2 and seen[-1][0] == "change" and seen[-1][1] == (20.0, pytest.approx(90.0, abs=0.5))


def test_the_keys_move_the_handle_that_has_the_focus_only(tmp_path):
    view, vm = opened(tmp_path, ", step: 10")
    low, high = (t.node for t in control(view).thumbs)
    view.window.simulate("focus", low)
    view.window.simulate("key_down", low, key="arrow_right")
    assert (vm.lo.get(), vm.hi.get()) == (30.0, 70.0)
    view.window.simulate("focus", high)
    view.window.simulate("key_down", high, key="arrow_left")
    view.window.simulate("key_down", high, key="page_down")
    assert (vm.lo.get(), vm.hi.get()) == (30.0, 30.0)  # ten steps down from 60 would be -40: it stops at the low handle
    view.window.simulate("key_down", high, key="end")
    assert vm.hi.get() == 100.0
    view.window.simulate("focus", low)  # a key goes to the handle that has the focus
    view.window.simulate("key_down", low, key="end")
    assert vm.lo.get() == 100.0  # up to the high one
    view.window.simulate("key_down", low, key="home")
    assert vm.lo.get() == 0.0


def test_a_screen_reader_can_increment_decrement_and_set_each_handle(tmp_path):
    view, vm = opened(tmp_path, ", step: 5")
    low, high = (t.node for t in control(view).thumbs)
    view.window.simulate("a11y_action", low, action="increment")
    view.window.simulate("a11y_action", high, action="decrement")
    assert (vm.lo.get(), vm.hi.get()) == (25.0, 65.0)
    view.window.simulate("a11y_action", high, action="set_value", value=80.0)
    assert vm.hi.get() == 80.0


def test_a_bound_value_the_view_model_changes_moves_its_handle(tmp_path):
    view, vm = opened(tmp_path)
    vm.lo.set(40.0)
    vm.hi.set(90.0)
    view.window.advance(16)
    c = control(view)
    assert c.thumbs[0].handle.get("translate_x") == pytest.approx(0.4 * c._span) and c.thumbs[1].handle.get("translate_x") == pytest.approx(0.9 * c._span)


def test_a_view_model_that_gives_a_low_above_the_high_is_read_in_order(tmp_path):
    view, vm = opened(tmp_path)
    vm.lo.set(95.0)
    view.window.advance(16)
    c = control(view)
    assert c._pair() == (95.0, 95.0) and c.thumbs[1].node.get("value") == 95.0


def test_ticks_between_the_handles_are_the_on_colour(tmp_path):
    view, _ = opened(tmp_path, ", step: 25, ticks: true")
    c = control(view)
    assert len(c.tick_marks) == 5
    colours = [m.get("fill") == role(view, "on_primary") for m in c.tick_marks]
    assert c._pair() == (25.0, 75.0)  # 20 and 70 snap to the step
    assert colours == [False, True, True, True, False]  # the marks at 25, 50 and 75 are between the handles


def test_the_value_bubble_of_a_handle_shows_while_it_is_dragged_or_has_the_keyboard(tmp_path):
    view, vm = opened(tmp_path, ", value_indicator: true")
    c = control(view)
    low, high = c.thumbs
    assert not low.bubble.get("visible") and not high.bubble.get("visible")
    view.window.simulate("pointer_down", view.node("root.s"), x=at(view, 0.7), y=24)
    assert high.bubble.get("visible") and not low.bubble.get("visible")
    assert high.bubble_text.get("text") == "70"
    view.window.simulate("pointer_up", x=view.node("root.s").get("layout_x") + at(view, 0.7), y=view.node("root.s").get("layout_y") + 24)
    view.window.advance(16)
    assert not high.bubble.get("visible")


def test_a_disabled_range_slider_has_no_tab_stops_and_does_not_move(tmp_path):
    view, vm = opened(tmp_path, ", disabled: true")
    c = control(view)
    assert not c.thumbs[0].node.get("focusable") and not c.thumbs[1].node.get("focusable")
    press(view, at(view, 0.3))
    assert (vm.lo.get(), vm.hi.get()) == (20.0, 70.0)
    assert c.thumbs[0].handle.get("fill") != role(view, "primary")


def test_the_handlers_hear_input_and_change(tmp_path):
    view, vm = opened(tmp_path, ", handlers: {on_input: moving, on_change: committed}")
    drag(view, at(view, 0.7), at(view, 0.8), at(view, 0.9))
    assert len(vm.live) >= 2 and vm.ends == [(20.0, pytest.approx(90.0, abs=0.5))]


def test_an_expressive_range_slider_is_three_pieces_with_a_gap_at_each_handle(tmp_path):
    view, _ = opened(tmp_path, ", size: m")
    c = control(view)
    centres = [c._edge + 0.2 * c._span, c._edge + 0.7 * c._span]
    assert c.inactive.get("layout_width") == pytest.approx(centres[0] - 2.0 - c.GAP, abs=0.5)
    assert c.active.get("layout_x") == pytest.approx(centres[0] + 2.0 + c.GAP, abs=0.5)
    assert c.active.get("layout_x") + c.active.get("layout_width") == pytest.approx(centres[1] - 2.0 - c.GAP, abs=0.5)
    assert c.inactive_high.get("layout_x") == pytest.approx(centres[1] + 2.0 + c.GAP, abs=0.5)
    assert c.inactive_high.get("layout_x") + c.inactive_high.get("layout_width") == pytest.approx(220.0, abs=0.5)
    assert (c.thumbs[0].handle.get("layout_width"), c.thumbs[0].handle.get("layout_height")) == (4.0, 52.0)


def test_a_vertical_range_slider_has_the_low_handle_below(tmp_path):
    view, vm = opened(tmp_path, ", vertical: true", style="height: 200")
    c = control(view)
    assert c.thumbs[0].handle.get("translate_y") == pytest.approx(-0.2 * c._span) and c.thumbs[1].handle.get("translate_y") == pytest.approx(-0.7 * c._span)
    assert c.active.get("layout_y") + c.active.get("layout_height") == pytest.approx(200 - c._edge - 0.2 * c._span)
    y = 200 - at(view, 0.9)  # a press near the top moves the high handle
    node = view.node("root.s")
    view.window.simulate("pointer_down", node, x=24, y=y)
    view.window.simulate("pointer_up", x=node.get("layout_x") + 24, y=node.get("layout_y") + y)
    assert vm.hi.get() == pytest.approx(90.0, abs=0.5) and vm.lo.get() == 20.0


def test_a_flex_expanded_range_slider_takes_its_laid_out_length(tmp_path):
    view, vm = opened(tmp_path, body='  - widget: Container\n    name: row\n    style: {flex_direction: horizontal, width: 300, height: 48}\n    children:\n'
                      '      - {widget: RangeSlider, name: s, min: 0, max: 100, low: "{{ lo }}", high: "{{ hi }}", style: {width: 120, flex: expand_horizontal}}\n')
    c = view._built.controls["root.row.s"]
    laid = view.node("root.row.s").get("layout_width")
    view.window.simulate("resize", width=300, height=300)
    assert laid > 250 and c.length == pytest.approx(laid, abs=0.5)
    assert c.thumbs[1].handle.get("translate_x") == pytest.approx(0.7 * c._span)


def test_the_constructor_refuses_what_a_slider_refuses_and_raises_a_high_below_low():
    from tesserae import App

    app = App()
    window = app._window if hasattr(app, "_window") else None
    assert window is not None
    with pytest.raises(ValueError, match="max > min"):
        RangeSlider(window, min=1.0, max=1.0)
    with pytest.raises(ValueError, match="inset icon needs a size"):
        RangeSlider(window, icon="volume_high")
    c = RangeSlider(window, low=0.8, high=0.2)
    assert c._pair() == (0.8, 0.8)
    c.destroy()


def test_a_press_that_began_on_a_handle_is_let_go_when_the_drag_ends(tmp_path):
    view, vm = opened(tmp_path)
    c = control(view)
    node, thumb = view.node("root.s"), c.thumbs[1]
    view.window.simulate("pointer_down", thumb.node, x=24, y=24)  # the handle's own node gets the press, then the group
    assert thumb.interaction.dragged and len(thumb.interaction.ripples) == 1
    view.window.simulate("pointer_move", x=node.get("layout_x") + at(view, 0.9), y=node.get("layout_y") + 24)
    view.window.simulate("pointer_up", x=node.get("layout_x") + at(view, 0.9), y=node.get("layout_y") + 24)
    for _ in range(60):
        view.window.advance(16)
    assert not thumb.interaction.dragged and thumb.interaction.ripples == [] and vm.hi.get() == pytest.approx(90.0, abs=0.5)
