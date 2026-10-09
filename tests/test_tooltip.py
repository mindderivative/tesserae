"""#238: `tooltip:` on any node -- plain and rich, after a hover delay or at once on keyboard focus."""

import pytest

from tesserae import App, Signal, ViewModel, a11y, tokens
from tesserae.spec.nodes import LoadError, parse_view


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.hint = Signal("Delete")
        self.clicks = Signal(0)


def view_text(tooltip="Delete", extra=""):
    return f"""name: main
widget: Container
style: {{flex_direction: vertical, width: 300, height: 200}}
children:
  - widget: Container
    name: b
    style: {{width: 80, height: 40, background: primary}}
    handlers: {{on_click: "clicks += 1"}}
    tooltip: {tooltip}
{extra}  - {{widget: Container, name: other, style: {{width: 80, height: 40, background: secondary}}, handlers: {{on_click: "clicks += 1"}}}}
"""


def opened(tmp_path, tooltip='"Delete"', extra=""):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(view_text(tooltip, extra))
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    view.window.advance(16)
    return view, app.bindings.viewmodel_for("main")


def centre(view, name="b"):
    node = view.node(f"root.{name}")
    return node.get("layout_x") + 10, node.get("layout_y") + 10


def hover(view, name="b"):
    x, y = centre(view, name)
    view.window.simulate("pointer_move", x=x, y=y)


def run(view, ms):
    for _ in range(max(1, ms // 16)):
        view.window.advance(16)


def texts(view):
    return [t.get("text") for layer in view._tips.values() for t in layer[0].children()]


def test_a_tooltip_waits_half_a_second_after_the_pointer_arrives(tmp_path):
    view, _ = opened(tmp_path)
    hover(view)
    run(view, 300)
    assert not view._tips
    run(view, 300)
    assert texts(view) == ["Delete"]


def test_it_goes_when_the_pointer_leaves_and_is_cancelled_if_it_leaves_first(tmp_path):
    view, _ = opened(tmp_path)
    hover(view)
    run(view, 100)
    hover(view, "other")
    run(view, 800)
    assert not view._tips  # left before it showed
    hover(view)
    run(view, 800)
    assert view._tips
    hover(view, "other")
    run(view, 32)
    assert not view._tips


def test_a_press_on_the_node_hides_it_and_still_clicks(tmp_path):
    view, vm = opened(tmp_path)
    hover(view)
    run(view, 800)
    assert view._tips
    x, y = centre(view)
    view.window.simulate("pointer_down", x=x, y=y)
    view.window.simulate("pointer_up", x=x, y=y)
    view.window.simulate("click", node=view.node("root.b"))
    assert not view._tips and vm.clicks.get() >= 1


def test_keyboard_focus_shows_it_at_once_and_leaving_hides_it(tmp_path):
    view, _ = opened(tmp_path)
    view.window.simulate("key_down", key="tab")  # focus arrives from the keyboard, on the first Tab stop
    view.window.advance(16)
    assert texts(view) == ["Delete"]
    view.window.simulate("key_down", key="tab")
    view.window.advance(16)
    assert not view._tips


def test_focus_that_a_mouse_gave_is_not_a_reason_to_show_it(tmp_path):
    view, _ = opened(tmp_path)
    x, y = centre(view)
    view.window.simulate("pointer_down", x=x, y=y)
    view.window.simulate("pointer_up", x=x, y=y)
    view.window.advance(16)
    assert not view._tips


def test_escape_hides_it(tmp_path):
    view, _ = opened(tmp_path)
    hover(view)
    run(view, 800)
    assert view._tips
    view.window.simulate("key_down", key="escape")
    assert not view._tips


def test_a_rich_tooltip_has_a_title_and_a_surface(tmp_path):
    view, _ = opened(tmp_path, "{text: Removes the file for good, title: Delete}")
    hover(view)
    run(view, 800)
    layer = next(iter(view._tips.values()))[0]
    assert texts(view) == ["Delete", "Removes the file for good"]
    assert layer.get("corner_radius") == 12.0 and layer.get("fill") == (view._scheme or tokens.BASELINE)["surface_container"]


def test_a_plain_one_is_the_inverse_surface(tmp_path):
    view, _ = opened(tmp_path)
    hover(view)
    run(view, 800)
    layer = next(iter(view._tips.values()))[0]
    assert layer.get("fill") == (view._scheme or tokens.BASELINE)["inverse_surface"] and layer.get("corner_radius") == 4.0


def test_the_delay_is_a_property(tmp_path):
    view, _ = opened(tmp_path, "{text: Quick, delay: 100}")
    hover(view)
    run(view, 160)
    assert texts(view) == ["Quick"]


def test_the_text_can_be_an_expression_read_when_it_shows(tmp_path):
    view, vm = opened(tmp_path, '"{{ hint }}"')
    vm.hint.set("Remove")
    hover(view)
    run(view, 800)
    assert texts(view) == ["Remove"]


def test_the_layer_does_not_take_the_pointer(tmp_path):
    view, _ = opened(tmp_path)
    hover(view)
    run(view, 800)
    assert next(iter(view._tips.values()))[0].get("hit_testable") is False


def test_the_text_is_the_nodes_description_where_it_has_none(tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr(a11y, "apply_extras", lambda node, props: seen.append(props))
    opened(tmp_path)
    assert {"description": "Delete"} in seen


def test_an_a11y_description_of_its_own_is_kept(tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr(a11y, "apply_extras", lambda node, props: seen.append(props))
    opened(tmp_path, '"Delete"', '    a11y: {description: Mine}\n'.replace("    a11y", "    a11y"))
    assert {"description": "Delete"} not in seen


def test_closing_the_view_takes_a_showing_tooltip_with_it(tmp_path):
    view, _ = opened(tmp_path)
    hover(view)
    run(view, 800)
    view.close()
    assert not view._tips


@pytest.mark.parametrize("value, message", [
    ("3", "takes text, or a mapping"), ("{title: Hi}", "needs text"), ("{text: Hi, size: 3}", "no tooltip field 'size'"),
    ("{text: 3}", "tooltip text is text"), ("{text: Hi, delay: -1}", "delay is milliseconds"), ("{text: Hi, delay: soon}", "delay is milliseconds"),
])
def test_a_wrong_tooltip_is_a_load_error(value, message):
    with pytest.raises(LoadError, match=message):
        parse_view(f"widget: Container\ntooltip: {value}\n", "T_View.yaml")


def test_a_view_call_can_carry_a_tooltip_to_the_root_of_the_view(tmp_path):
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Chip_View.yaml").write_text("widget: Container\nstyle: {width: 60, height: 30, background: primary}\n")
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        "name: main\nwidget: Container\nstyle: {width: 300, height: 200}\nchildren:\n  - {widget: Chip, name: c, tooltip: Hello}\n")
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    view.window.advance(16)
    hover(view, "c")
    run(view, 800)
    assert texts(view) == ["Hello"]


def test_only_escape_hides_it(tmp_path):
    view, _ = opened(tmp_path)
    hover(view)
    run(view, 800)
    view.window.simulate("key_down", key="a")
    assert view._tips


def test_asking_to_show_it_twice_makes_one_layer(tmp_path):
    view, _ = opened(tmp_path)
    inst = next(i for i in view.handle.composition.walk() if i.id == "root.b")
    view._show_tip(inst)
    first = view._tips["root.b"][0]
    view._show_tip(inst)
    assert view._tips["root.b"][0] == first and len(view._tips) == 1


def test_a_click_elsewhere_while_it_shows_still_lands(tmp_path):
    view, vm = opened(tmp_path)
    hover(view)
    run(view, 800)
    assert view._tips
    view.window.simulate("click", node=view.node("root.other"))
    assert vm.clicks.get() == 1  # a tooltip is not a layer that eats the next press


def test_a_node_that_leaves_the_view_takes_its_tooltip_with_it(tmp_path):
    class Gone(ViewModel):
        views = "main"

        def __init__(self):
            super().__init__()
            self.here = Signal(True)

    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        "name: main\nwidget: Container\nstyle: {width: 300, height: 200}\nchildren:\n"
        "  - {widget: Container, name: b, if: here, style: {width: 80, height: 40, background: primary}, tooltip: Hi}\n")
    app = App(root=tmp_path)
    app.bind(Gone)
    view = app.open_view("Main")
    app.show("main")
    view.window.advance(16)
    hover(view)
    run(view, 800)
    assert view._tips
    app.bindings.viewmodel_for("main").here.set(False)
    view.window.advance(16)
    assert not view._tips


# -- rich tooltips (#147): actions, placement, a card the pointer can enter ---------------------------------------------------

RICH = '{text: "Removes it for good", title: Delete, actions: [{label: Undo, on_click: "clicks += 10"}, {label: Close, on_click: "hint = \'closed\'"}]}'


def layer_of(view):
    return next(iter(view._tips.values()))[0]


def action_nodes(view):
    row = layer_of(view).children()[-1]
    return row.children()


def far(view):
    view.window.simulate("pointer_move", x=290, y=190)  # off the node and off the card


def move_to(view, node):
    view.window.simulate("pointer_move", x=node.get("layout_x") + 4, y=node.get("layout_y") + 4)


def test_a_rich_tooltip_shows_a_subhead_text_and_its_actions(tmp_path):
    view, _ = opened(tmp_path, RICH)
    hover(view)
    run(view, 800)
    layer = layer_of(view)
    assert [c.get("text") for c in layer.children()[:2]] == ["Delete", "Removes it for good"]
    assert [a.children()[0].get("text") for a in action_nodes(view)] == ["Undo", "Close"]
    assert layer.get("hit_testable") is True and layer.get("shadows")


def test_a_plain_tooltip_cannot_be_entered(tmp_path):
    view, _ = opened(tmp_path)
    hover(view)
    run(view, 800)
    assert layer_of(view).get("hit_testable") is False


def test_pressing_an_action_runs_its_handler_and_closes_the_tooltip(tmp_path):
    view, vm = opened(tmp_path, RICH)
    hover(view)
    run(view, 800)
    view.window.simulate("click", node=action_nodes(view)[0])
    assert vm.clicks.get() == 10 and not view._tips
    far(view)
    run(view, 32)
    hover(view)
    run(view, 800)
    view.window.simulate("click", node=action_nodes(view)[1])
    assert vm.hint.get() == "closed" and not view._tips


def test_a_rich_tooltip_stays_while_the_pointer_moves_onto_it_and_goes_when_it_leaves_both(tmp_path):
    view, _ = opened(tmp_path, RICH)
    hover(view)
    run(view, 800)
    move_to(view, layer_of(view))  # off the node, onto the card
    run(view, 400)
    assert view._tips
    far(view)
    run(view, 400)
    assert not view._tips


def test_a_rich_tooltip_goes_if_the_pointer_neither_returns_nor_arrives(tmp_path):
    view, _ = opened(tmp_path, RICH)
    hover(view)
    run(view, 800)
    far(view)
    run(view, 32)
    assert view._tips  # a moment's grace
    run(view, 400)
    assert not view._tips


def test_it_can_sit_above_the_node(tmp_path):
    view, _ = opened(tmp_path, '{text: Hi, placement: above}', extra="")
    view.node("root.b").set(position="absolute", x=100.0, y=100.0)
    view.window.advance(16)
    hover(view)
    run(view, 800)
    assert layer_of(view).get("layout_y") < view.node("root.b").get("layout_y")


@pytest.mark.parametrize("tooltip, message", [
    ('{text: x, placement: left}', "placement is one of below, above, start, end"),
    ('{text: x, actions: []}', "one or two"),
    ('{text: x, actions: [{label: A, on_click: a}, {label: B, on_click: b}, {label: C, on_click: c}]}', "one or two"),
    ('{text: x, actions: [{label: A}]}', "{label: ..., on_click: ...}"),
    ('{text: x, action: []}', "no tooltip field 'action'"),
])
def test_these_are_refused_at_load(tooltip, message):
    with pytest.raises(LoadError, match=message.replace("{", r"\{").replace("}", r"\}").replace(".", r"\.")):
        parse_view(view_text(tooltip), "Main_View.yaml")

