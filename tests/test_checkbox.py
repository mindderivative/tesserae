"""#175: the Material 3 checkbox in the view language -- on, off and in between, an error look, a label that is part of what you press."""

import pytest

from tesserae import App, Signal, ViewModel, tokens


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.agree = Signal(False)
        self.some = Signal(None)
        self.bad = Signal(False)


def opened(tmp_path, body, **kwargs):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        "name: main\nwidget: Container\nstyle: {flex_direction: vertical, align_content: top_left, width: 300, height: 200, gap: 8}\nchildren:\n" + body)
    app = App(root=tmp_path, **kwargs)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    for _ in range(3):
        view.window.advance(16)
    return view, app.bindings.viewmodel_for("main")


def control(view, name="c"):
    return view._built.controls[f"root.{name}"]


def role(view, name):
    return (view._scheme or tokens.BASELINE)[name]


def settle(view):
    for _ in range(40):
        view.window.advance(16)


def click(view, node):
    view.window.simulate("click", node=node)
    settle(view)


def test_a_checkbox_is_an_eighteen_pixel_box_in_a_forty_eight_pixel_target(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: Checkbox, name: c}\n")
    c = control(view)
    assert c.box.get("layout_width") == 18.0 and c.node.get("layout_width") == 48.0 and c.checked.get() is False
    assert c.box.get("stroke_color") == role(view, "on_surface_variant") and c.node.get("role") == "checkbox"


def test_clicking_toggles_it_and_writes_a_bound_signal(tmp_path):
    view, vm = opened(tmp_path, '  - {widget: Checkbox, name: c, checked: "{{ agree }}"}\n')
    click(view, view.node("root.c"))
    assert vm.agree.get() is True and control(view).box.get("fill") == role(view, "primary") and control(view).mark.get("trim_end") == 1.0
    click(view, view.node("root.c"))
    assert vm.agree.get() is False and control(view).mark.get("trim_end") == 0.0


def test_space_toggles_it_from_the_keyboard(tmp_path):
    view, vm = opened(tmp_path, '  - {widget: Checkbox, name: c, checked: "{{ agree }}"}\n')
    view.node("root.c").focus()
    view.window.simulate("key_down", key="space")
    assert vm.agree.get() is True


def test_following_a_signal_checks_the_box(tmp_path):
    view, vm = opened(tmp_path, '  - {widget: Checkbox, name: c, checked: "{{ agree }}"}\n')
    vm.agree.set(True)
    settle(view)
    assert control(view).checked.get() is True and view.node("root.c").get("checked") is True


def test_empty_is_in_between_a_dash_in_a_filled_box_and_a_click_turns_it_on(tmp_path):
    view, vm = opened(tmp_path, '  - {widget: Checkbox, name: c, checked: "{{ some }}"}\n')
    settle(view)
    c = control(view)
    assert c.checked.get() is None and view.node("root.c").get("checked") is None
    assert c.box.get("fill") == role(view, "primary") and c.mark.get("data") == c.DASH and c.mark.get("trim_end") == 1.0
    click(view, view.node("root.c"))
    assert vm.some.get() is True and c.mark.get("data") == c.CHECK


def test_a_literal_null_is_in_between_too(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: Checkbox, name: c, checked: null}\n")
    assert control(view).checked.get() is None


def test_error_draws_the_error_colours_off_and_on(tmp_path):
    view, vm = opened(tmp_path, '  - {widget: Checkbox, name: c, error: "{{ bad }}"}\n')
    c = control(view)
    assert c.box.get("stroke_color") == role(view, "on_surface_variant")
    vm.bad.set(True)
    settle(view)
    assert c.box.get("stroke_color") == role(view, "error")
    click(view, view.node("root.c"))
    assert c.box.get("fill") == role(view, "error") and c.mark.get("stroke_color") == role(view, "on_error")


def test_disabled_is_dimmed_and_does_not_toggle(tmp_path):
    view, vm = opened(tmp_path, '  - {widget: Checkbox, name: c, checked: "{{ agree }}", disabled: true}\n')
    click(view, view.node("root.c"))
    assert vm.agree.get() is False and not view.node("root.c").get("focusable") and view.node("root.c").get("disabled") is True


def test_the_colour_is_the_foreground(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: Checkbox, name: c, checked: true, style: {foreground: '#00AA00'}}\n")
    settle(view)
    assert control(view).box.get("fill") == (0, 170, 0, 255)


# -- the label ------------------------------------------------------------------------------------------------------------


def test_a_label_sits_beside_the_box_and_names_it_for_a_screen_reader(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: Checkbox, name: c, label: Remember me}\n")
    box, label = view.node("root.c"), view.node("root.c.label")
    assert label.get("text") == "Remember me" and label.get("layout_x") > box.get("layout_x") + box.get("layout_width") - 1
    assert abs((label.get("layout_y") + label.get("layout_height") / 2) - (box.get("layout_y") + box.get("layout_height") / 2)) <= 1.5
    assert box.get("label") == "Remember me"


def test_pressing_the_label_toggles_the_box_and_focuses_it(tmp_path):
    view, vm = opened(tmp_path, '  - {widget: Checkbox, name: c, checked: "{{ agree }}", label: Remember me}\n')
    click(view, view.node("root.c.label"))
    assert vm.agree.get() is True and view.node("root.c").get("focused") is True


def test_pressing_the_box_of_a_labelled_one_toggles_it_once(tmp_path):
    view, vm = opened(tmp_path, '  - {widget: Checkbox, name: c, checked: "{{ agree }}", label: Remember me}\n')
    click(view, view.node("root.c"))
    assert vm.agree.get() is True


def test_pressing_the_label_of_a_disabled_one_does_nothing(tmp_path):
    view, vm = opened(tmp_path, '  - {widget: Checkbox, name: c, checked: "{{ agree }}", label: Remember me, disabled: true}\n')
    click(view, view.node("root.c.label"))
    assert vm.agree.get() is False and view.node("root.c.label").get("opacity") == 0.38


def test_an_unlabelled_one_has_no_row_around_it(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: Checkbox, name: c}\n")
    assert "root.c.field" not in view._built.specs
