"""#151: the Material 3 basic dialog -- a modal panel, a headline, text, an icon, actions that report a result, an alert form."""

import pytest

from tesserae import App, Signal, ViewModel, tokens
from tesserae.shipped import shipped_views


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.shown = Signal(False)
        self.result = Signal("")


def opened(tmp_path, props="", children="", actions="[{label: Cancel, value: cancel}, {label: Discard, value: discard}]"):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(f"""name: main
widget: Container
style: {{flex_direction: vertical, width: 600, height: 500}}
children:
  - widget: Dialog
    name: d
    open: "{{{{ shown }}}}"
    result: "{{{{ result }}}}"
    headline: Discard draft?
    text: This cannot be undone.
    actions: {actions}
    {props}
{children}""")
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    for _ in range(4):
        view.window.advance(16)
    return view, app.bindings.viewmodel_for("main")


def role(view, name):
    return (view._scheme or tokens.BASELINE)[name]


def show(view, vm):
    vm.shown.set(True)
    for _ in range(4):
        view.window.advance(16)


def test_it_is_shipped():
    assert "Dialog" in shipped_views()


def node(view, part=""):
    return view.node("root.d" + (f".{part}" if part else ""))


def test_it_is_closed_until_open_and_then_a_scrim_with_a_panel_on_it(tmp_path):
    view, vm = opened(tmp_path)
    assert not view._shown_layers
    show(view, vm)
    assert view._shown_layers
    scrim = view._built.nodes["root.d"]
    assert scrim.get("fill")[3] == round(0.32 * 255)


def test_the_panel_is_a_raised_surface_with_28_pixel_corners_and_24_of_padding(tmp_path):
    view, vm = opened(tmp_path)
    show(view, vm)
    panel = node(view, "panel")
    assert panel.get("fill") == role(view, "surface_container_high") and panel.get("corner_radius") == 28.0
    assert panel.get("layout_width") == 312.0 and panel.get("padding_left") == 24.0 and panel.get("shadows")
    assert node(view, "panel.headline").get("font_size") == 24.0
    assert node(view, "panel.content.body").get("fill") == role(view, "on_surface_variant")


def test_the_panel_is_a_dialog_named_by_its_headline(tmp_path):
    view, vm = opened(tmp_path)
    show(view, vm)
    panel = node(view, "panel")
    assert panel.get("role") == "dialog" and panel.get("label") == "Discard draft?"
    assert node(view, "panel.headline").get("level") == 2


def test_the_width_stays_between_280_and_560(tmp_path):
    view, vm = opened(tmp_path, "width: 900")
    show(view, vm)
    assert node(view, "panel").get("layout_width") == 560.0
    (tmp_path / "b").mkdir()
    view2, vm2 = opened(tmp_path / "b", "width: 100")
    show(view2, vm2)
    assert node(view2, "panel").get("layout_width") == 280.0


def test_the_actions_are_text_buttons_on_the_right(tmp_path):
    view, vm = opened(tmp_path)
    show(view, vm)
    cancel, discard = node(view, "panel.actions.action[cancel]"), node(view, "panel.actions.action[discard]")
    assert cancel.get("layout_x") < discard.get("layout_x") and cancel.get("layout_y") == discard.get("layout_y")
    panel = node(view, "panel")
    assert discard.get("layout_x") + discard.get("layout_width") == panel.get("layout_x") + panel.get("layout_width") - 24
    assert node(view, "panel.actions.action[cancel].label").get("fill") == role(view, "primary")


def test_pressing_an_action_reports_it_and_closes_the_dialog(tmp_path):
    view, vm = opened(tmp_path)
    show(view, vm)
    view.window.simulate("click", node=node(view, "panel.actions.action[discard]"))
    view.window.advance(16)
    assert vm.result.get() == "discard" and vm.shown.get() is False and not view._shown_layers


def test_escape_and_a_press_on_the_scrim_dismiss_it_with_no_result(tmp_path):
    view, vm = opened(tmp_path)
    show(view, vm)
    view.window.simulate("key_down", key="escape")
    view.window.advance(16)
    assert vm.shown.get() is False and vm.result.get() == ""
    show(view, vm)
    view.window.simulate("pointer_down", x=5, y=5)
    view.window.advance(16)
    assert vm.shown.get() is False


def test_a_dialog_that_is_not_dismissible_only_closes_with_an_action(tmp_path):
    view, vm = opened(tmp_path, "dismissible: false")
    show(view, vm)
    assert node(view, "panel").get("role") == "dialog"
    view.window.simulate("key_down", key="escape")
    view.window.simulate("pointer_down", x=5, y=5)
    view.window.advance(16)
    assert vm.shown.get() is True
    view.window.simulate("click", node=node(view, "panel.actions.action[cancel]"))
    view.window.advance(16)
    assert vm.shown.get() is False and vm.result.get() == "cancel"


def test_an_icon_sits_above_the_headline_in_secondary(tmp_path):
    view, vm = opened(tmp_path, "icon: home")
    show(view, vm)
    icon = node(view, "panel.icon")
    assert icon.get("fill") == role(view, "secondary") and (icon.get("layout_width"), icon.get("layout_height")) == (24.0, 24.0)
    assert icon.get("layout_y") < node(view, "panel.headline").get("layout_y")


def test_children_are_the_content_after_the_text(tmp_path):
    view, vm = opened(tmp_path, children="    children:\n      - {widget: Switch, name: remember, label: Remember}\n")
    show(view, vm)
    assert node(view, "remember").get("layout_y") > node(view, "panel.content.body").get("layout_y")


def test_a_tall_content_scrolls_and_a_line_shows_above_the_actions_once_it_has(tmp_path):
    view, vm = opened(tmp_path, "max_height: 60", children="    children:\n      - {widget: Container, name: tall, style: {width: 100, height: 400}}\n")
    show(view, vm)
    content = view._built.outer["root.d.panel.content"]
    assert content.get("layout_height") == 60.0 and "root.d.panel.line" not in view._built.specs
    view.window.simulate("wheel", node=content, delta_x=0.0, delta_y=50.0)
    for _ in range(4):
        view.window.advance(16)
    assert "root.d.panel.line" in view._built.specs


def test_actions_stack_when_they_do_not_fit_on_one_row(tmp_path):
    view, vm = opened(tmp_path, actions='[{label: "Keep editing the draft", value: a}, {label: "Discard the draft completely", value: b}]')
    show(view, vm)
    a, b = node(view, "panel.actions.action[a]"), node(view, "panel.actions.action[b]")
    assert a.get("layout_y") < b.get("layout_y") and a.get("layout_x") >= node(view, "panel").get("layout_x")
