"""#185: the spin box -- hold a button to repeat, Page keys, wrap, decimals and affixes, in a view."""

import pytest

from tesserae import App, Signal, ViewModel


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.n = Signal(5)


def opened(tmp_path, props="", value="{{ n }}", bounds="min: 0\n    max: 10"):
    (tmp_path / "Views").mkdir(exist_ok=True)
    lines = "\n    ".join(props.split(", ")) if props else ""
    (tmp_path / "Views" / "Main_View.yaml").write_text(f"""name: main
widget: Container
style: {{width: 300, height: 100, align_content: top_left}}
children:
  - widget: SpinBox
    name: sp
    value: "{value}"
    {bounds}
    {lines}
""")
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    for _ in range(4):
        view.window.advance(16)
    return view, app.bindings.viewmodel_for("main")


def control(view):
    return view._built.controls["root.sp"]


def inc(view):
    return control(view).increment


def dec(view):
    return control(view).decrement


def field(view):
    return control(view).input


def run(view, ms):
    for _ in range(max(1, int(ms // 16))):
        view.window.advance(16)


def test_a_click_steps_once(tmp_path):
    view, vm = opened(tmp_path)
    view.window.simulate("click", node=inc(view))
    assert vm.n.get() == 6


def test_holding_a_button_waits_then_repeats_until_it_is_let_go(tmp_path):
    view, vm = opened(tmp_path, value="{{ n }}")
    view.window.simulate("pointer_down", node=dec(view))
    run(view, 300)
    assert vm.n.get() == 5  # not yet
    run(view, 200)
    assert vm.n.get() < 5
    held = vm.n.get()
    run(view, 160)
    assert vm.n.get() < held
    view.window.simulate("pointer_up", node=dec(view))
    stopped = vm.n.get()
    run(view, 400)
    assert vm.n.get() == stopped


def test_letting_go_after_a_hold_is_not_another_step(tmp_path):
    view, vm = opened(tmp_path)
    view.window.simulate("pointer_down", node=inc(view))
    run(view, 600)
    reached = vm.n.get()
    assert reached > 6
    view.window.simulate("pointer_up", node=inc(view))  # the engine follows it with the click
    assert vm.n.get() == reached
    view.window.simulate("click", node=inc(view))  # a fresh press and release is one step
    assert vm.n.get() == min(10, reached + 1)


def test_a_hold_stops_at_the_bound(tmp_path):
    view, vm = opened(tmp_path)
    view.window.simulate("pointer_down", node=inc(view))
    run(view, 3000)
    assert vm.n.get() == 10
    view.window.simulate("pointer_up", node=inc(view))


def test_a_short_press_is_only_one_step(tmp_path):
    view, vm = opened(tmp_path)
    view.window.simulate("pointer_down", node=inc(view))
    run(view, 100)
    view.window.simulate("pointer_up", node=inc(view))
    run(view, 600)
    assert vm.n.get() == 6


def test_page_up_and_page_down_step_by_ten_steps(tmp_path):
    view, vm = opened(tmp_path, "step: 0.5", bounds="min: -50\n    max: 50")
    vm.n.set(0)
    run(view, 32)
    field(view).focus()
    view.window.simulate("key_down", key="page_up")
    assert vm.n.get() == 5
    view.window.simulate("key_down", key="page_down")
    view.window.simulate("key_down", key="page_down")
    assert vm.n.get() == -5


def test_wrap_goes_round_the_ends(tmp_path):
    view, vm = opened(tmp_path, "wrap: true")
    vm.n.set(10)
    run(view, 32)
    view.window.simulate("click", node=inc(view))
    assert vm.n.get() == 0
    view.window.simulate("click", node=dec(view))
    assert vm.n.get() == 10


def test_without_wrap_the_button_at_a_bound_is_disabled(tmp_path):
    view, vm = opened(tmp_path)
    vm.n.set(10)
    run(view, 32)
    assert inc(view).get("disabled") is True
    (tmp_path / "w").mkdir()
    wrapped, vm2 = opened(tmp_path / "w", "wrap: true")
    vm2.n.set(10)
    run(wrapped, 32)
    assert inc(wrapped).get("disabled") is False


def test_decimals_prefix_and_suffix_show_with_the_number(tmp_path):
    view, vm = opened(tmp_path, "decimals: 1, prefix: '$', suffix: ' kg'")
    assert field(view).get("text") == "$5.0 kg"
    view.window.simulate("click", node=inc(view))
    assert vm.n.get() == 6 and field(view).get("text") == "$6.0 kg"


def test_what_is_typed_may_leave_the_affixes_out_or_put_them_in(tmp_path):
    view, vm = opened(tmp_path, "decimals: 1, suffix: ' kg'")
    field(view).focus()
    field(view).set(text="")
    view.window.simulate("input", text="7.5")
    run(view, 32)
    assert vm.n.get() == 7.5
    field(view).set(text="")
    view.window.simulate("input", text="8 kg")
    run(view, 32)
    assert vm.n.get() == 8


def test_it_is_named_for_a_screen_reader(tmp_path):
    view, _ = opened(tmp_path, "label: Quantity")
    assert field(view).get("label") == "Quantity"


# -- the field with a label and a line of help --------------------------------------------------------------------------------


def field_app(tmp_path, props=""):
    (tmp_path / "Views").mkdir(exist_ok=True)
    lines = "\n    ".join(props.split(", ")) if props else ""
    (tmp_path / "Views" / "Main_View.yaml").write_text(f"""name: main
widget: Container
style: {{width: 300, height: 200, align_content: top_left}}
children:
  - widget: SpinBoxField
    name: f
    value: "{{{{ n }}}}"
    least: 0
    most: 10
    {lines}
""")
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    run(view, 64)
    return view, app.bindings.viewmodel_for("main")


def test_the_field_has_a_label_above_the_spin_box_and_names_it(tmp_path):
    from tesserae import tokens
    view, _ = field_app(tmp_path, "label: Quantity")
    label, box = view.node("root.f.label"), view._built.controls["root.f.box"]
    assert label.get("text") == "Quantity" and label.get("fill") == (view._scheme or tokens.BASELINE)["on_surface_variant"]
    assert label.get("layout_y") < box.node.get("layout_y") and box.input.get("label") == "Quantity"


def test_the_supporting_text_is_under_it_and_an_error_replaces_it_in_the_error_colour(tmp_path):
    from tesserae import tokens
    view, _ = field_app(tmp_path, "label: Quantity, supporting: Between 0 and 10")
    help_ = view.node("root.f.help")
    assert help_.get("text") == "Between 0 and 10" and help_.get("layout_y") > view._built.controls["root.f.box"].node.get("layout_y")
    (tmp_path / "e").mkdir()
    bad, _ = field_app(tmp_path / "e", "label: Quantity, supporting: Between 0 and 10, error: Too many")
    assert bad.node("root.f.help").get("text") == "Too many" and bad.node("root.f.help").get("fill") == (bad._scheme or tokens.BASELINE)["error"]


def test_the_field_passes_everything_to_the_spin_box_and_writes_the_value_back(tmp_path):
    view, vm = field_app(tmp_path, "wrap: true, decimals: 1, suffix: ' kg'")
    box = view._built.controls["root.f.box"]
    assert box.wrap is True and box.decimals == 1 and box.suffix == " kg" and box.input.get("text") == "5.0 kg"
    view.window.simulate("click", node=box.increment)
    assert vm.n.get() == 6
