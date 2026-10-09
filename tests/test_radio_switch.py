"""#176, #177: the Material 3 radio button and switch in the view language -- groups, a chosen value, labels, errors, icons on the handle."""

import pytest

from tesserae import App, Signal, ViewModel, tokens


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.size = Signal("m")
        self.on = Signal(False)
        self.bad = Signal(False)


def opened(tmp_path, body, **kwargs):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        "name: main\nwidget: Container\nstyle: {flex_direction: vertical, align_content: top_left, width: 300, height: 300, gap: 4}\nchildren:\n" + body)
    app = App(root=tmp_path, **kwargs)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    for _ in range(3):
        view.window.advance(16)
    return view, app.bindings.viewmodel_for("main")


def control(view, name):
    return view._built.controls[f"root.{name}"]


def role(view, name):
    return (view._scheme or tokens.BASELINE)[name]


def settle(view):
    for _ in range(40):
        view.window.advance(16)


def click(view, node):
    view.window.simulate("click", node=node)
    settle(view)


SIZES = """  - {widget: RadioButton, name: s, group: size, selected: "{{ size == 's' }}", handlers: {on_change: "size = 's'"}, label: Small}
  - {widget: RadioButton, name: m, group: size, selected: "{{ size == 'm' }}", handlers: {on_change: "size = 'm'"}, label: Medium}
  - {widget: RadioButton, name: l, group: size, selected: "{{ size == 'l' }}", handlers: {on_change: "size = 'l'"}, label: Large}
"""


def test_a_radio_button_is_a_ring_that_fills_with_a_dot_when_chosen(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: RadioButton, name: r, selected: true}\n  - {widget: RadioButton, name: q}\n")
    r, q = control(view, "r"), control(view, "q")
    assert r.ring.get("layout_width") == 20.0 and r.ring.get("stroke_color") == role(view, "primary") and r.dot.get("scale") == 1.0
    assert q.ring.get("stroke_color") == role(view, "on_surface_variant") and q.dot.get("scale") == 0.0 and r.node.get("role") == "radio"


def test_a_group_has_one_chosen_and_a_bound_value_follows_the_choice(tmp_path):
    view, vm = opened(tmp_path, SIZES)
    assert control(view, "m").selected.get() and not control(view, "s").selected.get()
    click(view, view.node("root.l"))
    assert vm.size.get() == "l" and control(view, "l").selected.get() and not control(view, "m").selected.get()


def test_setting_the_value_moves_the_choice(tmp_path):
    view, vm = opened(tmp_path, SIZES)
    vm.size.set("s")
    settle(view)
    assert control(view, "s").selected.get() and not control(view, "m").selected.get()


def test_pressing_a_chosen_one_does_not_unchoose_it(tmp_path):
    view, vm = opened(tmp_path, SIZES)
    click(view, view.node("root.m"))
    assert vm.size.get() == "m" and control(view, "m").selected.get()


def test_the_group_is_one_tab_stop_and_the_arrows_move_the_choice(tmp_path):
    view, vm = opened(tmp_path, SIZES)
    assert [bool(view.node(f"root.{n}").get("focusable")) for n in "sml"] == [False, True, False]
    view.node("root.m").focus()
    view.window.simulate("key_down", key="arrow_down")
    settle(view)
    assert vm.size.get() == "l"
    view.window.simulate("key_down", key="arrow_up")
    view.window.simulate("key_down", key="arrow_up")
    settle(view)
    assert vm.size.get() == "s"


def test_pressing_a_radios_label_chooses_it(tmp_path):
    view, vm = opened(tmp_path, SIZES)
    click(view, view.node("root.s.label"))
    assert vm.size.get() == "s"


def test_a_radio_in_error_is_drawn_in_the_error_colours(tmp_path):
    view, _ = opened(tmp_path, '  - {widget: RadioButton, name: a, error: true}\n  - {widget: RadioButton, name: b, selected: true, error: true}\n')
    assert control(view, "a").ring.get("stroke_color") == role(view, "error")
    assert control(view, "b").ring.get("stroke_color") == role(view, "error") and control(view, "b").dot.get("fill") == role(view, "error")


def test_a_disabled_radio_is_dimmed_and_does_nothing(tmp_path):
    view, vm = opened(tmp_path, '  - {widget: RadioButton, name: a, group: g, selected: "{{ on }}", disabled: true, label: "Off"}\n')
    click(view, view.node("root.a"))
    click(view, view.node("root.a.label"))
    assert not control(view, "a").selected.get() and view.node("root.a").get("disabled") is True


# -- the switch -------------------------------------------------------------------------------------------------------------


def test_a_switch_is_a_track_and_a_handle_that_slides(tmp_path):
    view, vm = opened(tmp_path, '  - {widget: Switch, name: w, selected: "{{ on }}"}\n')
    w = control(view, "w")
    assert w.track.get("layout_width") == 52.0 and w.track.get("fill") == role(view, "surface_container_highest") and w.handle.get("translate_x") == 0.0
    click(view, view.node("root.w"))
    assert vm.on.get() is True and w.track.get("fill") == role(view, "primary") and w.handle.get("translate_x") == w.TRAVEL
    assert w.node.get("role") == "switch" and w.node.get("checked") is True


def test_a_switch_toggles_with_space_and_follows_its_signal(tmp_path):
    view, vm = opened(tmp_path, '  - {widget: Switch, name: w, selected: "{{ on }}"}\n')
    view.node("root.w").focus()
    view.window.simulate("key_down", key="space")
    assert vm.on.get() is True
    vm.on.set(False)
    settle(view)
    assert control(view, "w").handle.get("translate_x") == 0.0


def test_a_switch_label_is_part_of_what_you_press(tmp_path):
    view, vm = opened(tmp_path, '  - {widget: Switch, name: w, selected: "{{ on }}", label: Wi-Fi}\n')
    click(view, view.node("root.w.label"))
    assert vm.on.get() is True and view.node("root.w").get("label") == "Wi-Fi"


def test_a_disabled_switch_is_dimmed_and_stays_put(tmp_path):
    view, vm = opened(tmp_path, '  - {widget: Switch, name: w, selected: "{{ on }}", disabled: true}\n')
    click(view, view.node("root.w"))
    assert vm.on.get() is False and not view.node("root.w").get("focusable")


def test_icons_put_a_cross_on_the_off_handle_and_a_check_on_the_on_one(tmp_path):
    view, vm = opened(tmp_path, '  - {widget: Switch, name: w, selected: "{{ on }}", icons: true}\n  - {widget: Switch, name: p}\n')
    w = control(view, "w")
    assert w.icon.get("visible") is True and control(view, "p").icon.get("visible") is False
    off_data = w.icon.get("data")
    assert w.handle.get("scale") == pytest.approx(24.0 / 28.0, abs=0.01)  # the off handle is as big as the on one with icons
    click(view, view.node("root.w"))
    assert w.icon.get("data") != off_data and w.icon.get("fill") == role(view, "on_primary_container")


def test_without_icons_the_off_handle_is_the_small_one(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: Switch, name: w}\n")
    assert control(view, "w").handle.get("scale") == pytest.approx(16.0 / 28.0, abs=0.01)
