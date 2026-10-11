"""#259 (part of #257): a node's `visible:` -- hidden and out of layout while false, kept in the tree with its state and listeners (unlike `if:`)."""

import pytest

from tesserae import App, Signal, ViewModel


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.show = Signal(False)
        self.flag = Signal(True)
        self.clicks = []

    def on_under(self):
        self.clicks.append("under")

    def on_over(self):
        self.clicks.append("over")


HEAD = "name: main\nwidget: Container\nstyle: {width: 300, height: 200, flex_direction: vertical}\nchildren:\n"
BOX = "style: {width: 40, height: 40, background: primary}"


def opened(tmp_path, body, files=None, head=HEAD):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(head + body)
    for name, text in (files or {}).items():
        (tmp_path / "Views" / name).write_text(text)
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    view.window.advance(16)
    return app, view, app.bindings.viewmodel_for("main")


def test_a_node_with_visible_false_is_hidden_and_takes_no_room(tmp_path):
    app, view, vm = opened(tmp_path, f"  - {{widget: Rect, name: a, visible: false, {BOX}}}\n  - {{widget: Rect, name: b, {BOX}}}\n")
    a, b = view.node("root.a"), view.node("root.b")
    assert a.get("visible") is False and (a.get("layout_width"), a.get("layout_height")) == (0.0, 0.0)
    assert b.get("layout_y") == 0.0  # it moved up into the room the hidden one would have taken


def test_visible_true_or_absent_shows_the_node(tmp_path):
    app, view, vm = opened(tmp_path, f"  - {{widget: Rect, name: a, visible: true, {BOX}}}\n  - {{widget: Rect, name: b, {BOX}}}\n")
    assert view.node("root.a").get("visible") is True and view.node("root.b").get("visible") is True
    assert view.node("root.b").get("layout_y") == 40.0


def test_a_signal_hides_and_shows_it(tmp_path):
    app, view, vm = opened(tmp_path, f"  - {{widget: Rect, name: a, visible: '{{{{ show }}}}', {BOX}}}\n")
    a = view.node("root.a")
    assert a.get("visible") is False
    vm.show.set(True)
    view.window.advance(16)
    assert a.get("visible") is True and a.get("layout_width") == 40.0
    vm.show.set(False)
    view.window.advance(16)
    assert a.get("visible") is False


def test_a_hidden_node_keeps_its_state_which_an_if_would_lose(tmp_path):
    body = """  - widget: Container
    name: counter
    state: {n: 0}
    visible: '{{ show }}'
    interaction: true
    handlers: {on_click: "n += 1"}
    style: {width: 100, height: 40}
    children:
      - {widget: Text, name: label, text: "{{ n }}", typography_role: body_medium, style: {foreground: on_surface}}
  - widget: Container
    name: rebuilt
    state: {n: 0}
    if: show
    interaction: true
    handlers: {on_click: "n += 1"}
    style: {width: 100, height: 40}
    children:
      - {widget: Text, name: label2, text: "{{ n }}", typography_role: body_medium, style: {foreground: on_surface}}
"""
    app, view, vm = opened(tmp_path, body)
    vm.show.set(True)
    view.window.advance(16)
    for name in ("counter", "rebuilt"):
        node = view.node(f"root.{name}")
        view.window.simulate("click", x=50.0, y=node.get("layout_y") + 20)
    assert view.node("root.counter.label").get("text") == "1" and view.node("root.rebuilt.label2").get("text") == "1"
    vm.show.set(False)
    view.window.advance(16)
    vm.show.set(True)
    view.window.advance(16)
    assert view.node("root.counter.label").get("text") == "1"   # it was only hidden
    assert view.node("root.rebuilt.label2").get("text") == "0"  # it was taken out and built again


def test_a_hidden_node_does_not_take_the_pointer(tmp_path):
    body = """  - widget: Container
    name: under
    interaction: true
    handlers: {on_click: on_under}
    style: {position: absolute, x: 0, y: 0, width: 200, height: 100, background: surface_container}
  - widget: Container
    name: over
    visible: '{{ show }}'
    interaction: true
    handlers: {on_click: on_over}
    style: {position: absolute, x: 0, y: 0, width: 200, height: 100}
"""
    app, view, vm = opened(tmp_path, body)
    view.window.simulate("click", x=100.0, y=50.0)
    assert vm.clicks == ["under"]
    vm.show.set(True)
    view.window.advance(16)
    vm.clicks.clear()
    view.window.simulate("click", x=100.0, y=50.0)
    assert vm.clicks == ["over"]


def test_a_patch_leaves_a_node_hidden_by_other_code_alone_when_the_style_does_not_say_visible(tmp_path):
    """An overlay, a view's root and a binding hide nodes too; a node with no `visible:` is never set shown by a re-patch."""
    app, view, vm = opened(tmp_path, f"  - {{widget: Rect, name: a, style: {{width: 40, height: 40, background: \"{{{{ 'primary' if flag else 'secondary' }}}}\"}}}}\n")
    a = view.node("root.a")
    a.set(visible=False)  # something else hid it
    vm.flag.set(False)    # the node is patched
    view.window.advance(16)
    assert a.get("visible") is False


def test_dropping_visible_from_a_node_shows_it_again():
    from tesserae.spec.build import _resets, _with_visible

    assert _resets({}, frozenset({"visible"})) == {"visible": True}
    assert _with_visible({"visible": False}, {"width": 1}) == {"width": 1, "visible": False}
    assert _with_visible({"visible": True}, {}) == {"visible": True}
    assert _with_visible({}, {"width": 1}) == {"width": 1} and _with_visible({"visible": None}, {}) == {}


def test_a_widget_that_declares_a_visible_of_its_own_keeps_it(tmp_path):
    files = {"Panel_View.yaml": "params: {visible: {type: bool, default: true}}\nwidget: Container\nstyle: {width: 100, height: 50}\n"
                                "children:\n  - {widget: Text, name: t, text: \"{{ 'on' if visible else 'off' }}\", typography_role: body_medium, style: {foreground: on_surface}}\n"}
    app, view, vm = opened(tmp_path, "  - {widget: Panel, name: p, visible: false}\n", files)
    assert view.node("root.p.t").get("text") == "off" and view.node("root.p").get("visible") is True  # the param, not the key


def test_visible_on_a_view_call_hides_the_whole_view(tmp_path):
    files = {"Panel_View.yaml": f"widget: Container\nstyle: {{width: 100, height: 50, background: surface_container}}\n"}
    body = f"  - {{widget: Panel, name: p, visible: '{{{{ show }}}}'}}\n  - {{widget: Rect, name: after, {BOX}}}\n"
    app, view, vm = opened(tmp_path, body, files)
    assert view.node("root.p").get("visible") is False and view.node("root.after").get("layout_y") == 0.0
    vm.show.set(True)
    view.window.advance(16)
    assert view.node("root.p").get("visible") is True and view.node("root.after").get("layout_y") == 50.0


def test_the_root_of_a_view_takes_no_visible(tmp_path):
    with pytest.raises(Exception, match="the root of a view takes no 'visible:'"):
        opened(tmp_path, f"  - {{widget: Rect, name: a, {BOX}}}\n", head="name: main\nwidget: Container\nvisible: false\nstyle: {width: 300, height: 200}\nchildren:\n")


@pytest.mark.parametrize("value", ["maybe", "3", "[true]"])
def test_a_visible_that_is_not_true_or_false_is_refused_naming_it(tmp_path, value):
    with pytest.raises(Exception, match="'visible' takes true or false"):
        opened(tmp_path, f"  - {{widget: Rect, name: a, visible: {value}, {BOX}}}\n")


def test_a_control_and_a_link_can_be_hidden_too(tmp_path):
    body = (f"  - {{widget: Slider, name: s, visible: false, value: 3, min: 0, max: 10}}\n"
            f"  - {{widget: Link, name: l, visible: false, text: Docs, href: 'https://example.com', style: {{foreground: primary}}}}\n"
            f"  - {{widget: Rect, name: r, {BOX}}}\n")
    app, view, vm = opened(tmp_path, body)
    assert view.node("root.s").get("visible") is False and view.node("root.l").get("visible") is False
    assert view.node("root.r").get("layout_y") == 0.0


def test_the_widget_schema_knows_the_key():
    from tesserae.spec.widgets import json_schema
    assert "visible" in str(json_schema())


def test_a_bound_visible_whose_value_is_not_true_or_false_is_refused_naming_it(tmp_path):
    """A literal is checked when the file is read; what an expression works out is checked when it is worked out."""
    with pytest.raises(Exception, match="'visible' takes true or false"):
        opened(tmp_path, f"  - {{widget: Rect, name: a, visible: \"{{{{ 'maybe' }}}}\", {BOX}}}\n")
