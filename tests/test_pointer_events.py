"""#258 (part of #257): `style.pointer_events` -- `none` lets the pointer through a node (the engine's `hit_testable`), `auto` is the usual."""

import pytest

from tesserae import App, Signal, ViewModel


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.through = Signal("none")
        self.clicks = []

    def on_under(self):
        self.clicks.append("under")

    def on_over(self):
        self.clicks.append("over")

    def on_kid(self):
        self.clicks.append("kid")


STACK = """name: main
widget: Container
style: {width: 300, height: 200, position: relative}
children:
  - widget: Container
    name: under
    interaction: true
    handlers: {on_click: on_under}
    style: {position: absolute, x: 0, y: 0, width: 200, height: 100, background: surface_container}
  - widget: Container
    name: over
    interaction: true
    handlers: {on_click: on_over}
    style: {position: absolute, x: 0, y: 0, width: 200, height: 100, pointer_events: "{{ through }}"}
    children:
      - widget: Container
        name: kid
        interaction: true
        handlers: {on_click: on_kid}
        style: {position: absolute, x: 10, y: 10, width: 50, height: 50, background: primary}
"""


def opened(tmp_path, text=STACK):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(text)
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    view.window.advance(16)
    return app, view, app.bindings.viewmodel_for("main")


def click(view, vm, x, y):
    vm.clicks.clear()
    view.window.simulate("click", x=x, y=y)
    return list(vm.clicks)


def test_a_click_on_a_pointer_events_none_node_goes_to_what_is_under_it(tmp_path):
    app, view, vm = opened(tmp_path)
    assert view.node("root.over").get("hit_testable") is False
    assert click(view, vm, 150.0, 80.0) == ["under"]


def test_without_it_or_with_auto_the_node_takes_the_click(tmp_path):
    app, view, vm = opened(tmp_path)
    vm.through.set("auto")
    view.window.advance(16)
    assert view.node("root.over").get("hit_testable") is True
    assert click(view, vm, 150.0, 80.0) == ["over"]


def test_what_is_inside_a_pointer_events_none_node_still_takes_the_pointer(tmp_path):
    app, view, vm = opened(tmp_path)
    assert click(view, vm, 30.0, 30.0) == ["kid"]  # the child is hit (and, as for any clickable in a clickable, the click stops there)


def test_a_signal_turns_it_on_and_off_and_dropping_it_puts_the_node_back(tmp_path):
    app, view, vm = opened(tmp_path)
    assert click(view, vm, 150.0, 80.0) == ["under"]
    vm.through.set("auto")
    view.window.advance(16)
    assert click(view, vm, 150.0, 80.0) == ["over"]
    vm.through.set("none")
    view.window.advance(16)
    assert click(view, vm, 150.0, 80.0) == ["under"]


def test_a_patch_that_no_longer_gives_it_puts_the_property_back():
    from tesserae.spec.build import _resets, layout_keys
    from tesserae.spec.layout import engine_style

    engine = engine_style("n", {"pointer_events": "none"})
    assert engine["hit_testable"] is False and "pointer_events" not in engine  # the engine's name for it, not ours
    assert "hit_testable" in layout_keys(engine)
    assert "hit_testable" not in layout_keys(engine_style("n", {}))  # a style that does not say it leaves the property alone
    assert _resets({}, frozenset({"hit_testable"})) == {"hit_testable": True}  # dropped: hit-testable again


@pytest.mark.parametrize("value", ["hidden", "True", "", "ignore"])
def test_a_value_that_is_not_auto_or_none_is_refused_naming_the_node(tmp_path, value):
    text = STACK.replace('pointer_events: "{{ through }}"', f"pointer_events: '{value}'")
    with pytest.raises(Exception, match="pointer_events must be one of auto, none"):
        opened(tmp_path, text)


def test_only_a_style_that_gives_it_touches_the_property(tmp_path):
    """The builder sets `hit_testable=False` on its own decoration nodes; a node that does not say `pointer_events` keeps what it was built with."""
    app, view, vm = opened(tmp_path)
    assert view.node("root.under").get("hit_testable") is True and view.node("root.over.kid").get("hit_testable") is True
