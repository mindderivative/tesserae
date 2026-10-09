"""#237: the whole accessibility vocabulary as `a11y:` fields -- the states tre has no property for yet are accepted, checked, and sent as far as tre takes them."""

import pytest

from tesserae import App, Signal, View, ViewModel, a11y
from tesserae.spec.build import SpecBuildError
from tesserae.spec.nodes import LoadError, parse_view

SEED = (103, 80, 164, 255)


class Recorder:
    """A node that takes only the properties it was told to, like a tre that has them."""

    def __init__(self, accepts):
        self.accepts, self.set_calls = set(accepts), []

    def set(self, **props):
        for name in props:
            if name not in self.accepts:
                raise ValueError(f'unknown node property "{name}" -- `get` reads any property `set` takes')
        self.set_calls.append(props)


@pytest.mark.parametrize("fields", [
    {"pressed": True}, {"pressed": False}, {"pressed": "mixed"}, {"pressed": None}, {"invalid": True}, {"busy": False}, {"description": "Required"},
    {"current": "page"}, {"current": True}, {"current": False}, {"value_now": 3}, {"value_text": "three of ten"},
])
def test_these_values_are_accepted(fields):
    assert a11y.check(fields)


@pytest.mark.parametrize("fields, message", [
    ({"pressed": "yes"}, "pressed must be true, false or mixed"), ({"pressed": 1}, "pressed must be true, false or mixed"),
    ({"invalid": "no"}, "invalid must be true or false"), ({"busy": 1}, "busy must be true or false"),
    ({"description": 3}, "description must be a string"), ({"value_text": True}, "value_text must be a string"),
    ({"current": "now"}, "current must be true, false or one of"), ({"value_now": "3"}, "value_now must be a number"),
    ({"controls": ""}, "controls is the name of a node"), ({"describedby": [3]}, "describedby is the name of a node"),
])
def test_these_are_refused_naming_the_field(fields, message):
    with pytest.raises(ValueError, match=message):
        a11y.check(fields)


def test_describe_sends_what_the_node_takes_and_skips_the_rest_once(caplog):
    a11y._WARNED.clear()
    node = Recorder({"label", "a11y_hidden", "invalid"})
    a11y.describe(node, label="Email", invalid=True, pressed=True, busy=False)
    assert node.set_calls == [{"label": "Email"}, {"invalid": True}]
    a11y.describe(node, pressed=False)  # said once, not again
    assert a11y._WARNED == {"pressed", "busy"}


def test_describe_refuses_relations_in_python():
    with pytest.raises(ValueError, match="name nodes of a view"):
        a11y.describe(Recorder(()), controls="panel")


def test_a_property_error_that_is_not_about_a_missing_property_is_not_swallowed():
    class Strict:
        def set(self, **props):
            raise ValueError("node property `invalid` must be a boolean")

    with pytest.raises(ValueError, match="must be a boolean"):
        a11y.apply_extras(Strict(), {"invalid": True})


def test_the_extras_are_bindable():
    for name in a11y.EXTRAS:
        assert name in a11y.BINDABLE


def test_bind_follows_a_signal_for_an_extra():
    node, busy = Recorder({"busy"}), Signal(False)
    stop = a11y.bind(node, busy=busy)
    busy.set(True)
    assert node.set_calls == [{"busy": False}, {"busy": True}]
    stop()


# -- in a view --------------------------------------------------------------------------------------------------------------


def page(a11y_fields, extra_children=()):
    return {"id": "root", "kind": "Container", "style": {"width": 200, "height": 100},
            "children": [{"id": "b", "kind": "Rect", "style": {"width": 40, "height": 40, "background": "primary"}, "a11y": a11y_fields},
                         {"id": "panel", "kind": "Rect", "style": {"width": 40, "height": 40, "background": "secondary"}}, *extra_children]}


def test_a_view_with_the_fields_builds_on_this_tre_and_leaves_the_rest_alone():
    a11y._WARNED.clear()
    view = View(page({"label": "Toggle", "pressed": True, "invalid": False, "description": "Turns it on", "current": "page", "busy": True,
                      "value_text": "on", "value_now": 1, "controls": "panel", "describedby": ["panel"]}), theme_seed=SEED)
    assert view.node("b").get("label") == "Toggle"
    assert {"pressed", "invalid", "description", "current", "busy", "value_text", "value_now", "controls", "describedby"} <= a11y._WARNED


def test_the_view_sends_them_to_a_node_that_takes_them(monkeypatch):
    view = View(page({"label": "x"}), theme_seed=SEED)
    node = Recorder({"pressed", "controls", "describedby", "invalid"})
    monkeypatch.setitem(view._built.nodes, "b", node)
    view._spec = page({"pressed": "mixed", "invalid": True, "controls": "panel", "describedby": ["panel"]})
    view._apply_a11y_extras()
    sent = {k: v for call in node.set_calls for k, v in call.items()}
    assert sent["pressed"] == "mixed" and sent["invalid"] is True
    assert sent["controls"] == [view._built.outer["panel"]] and sent["describedby"] == [view._built.outer["panel"]]


def test_a_field_that_is_dropped_is_cleared(monkeypatch):
    view = View(page({"label": "x"}), theme_seed=SEED)
    node = Recorder({"pressed"})
    monkeypatch.setitem(view._built.nodes, "b", node)
    view._spec = page({"pressed": True})
    view._apply_a11y_extras()
    view._spec = page({"label": "x"})
    view._apply_a11y_extras()
    assert node.set_calls == [{"pressed": True}, {"pressed": None}]


def test_a_relation_must_name_a_node_of_the_view():
    with pytest.raises(ValueError, match="names 'nowhere', which is not a node of this view"):
        View(page({"controls": "nowhere"}), theme_seed=SEED)


def test_a_wrong_value_in_a_view_names_the_widget():
    with pytest.raises(SpecBuildError, match='widget "b": a11y invalid must be true or false'):
        View(page({"invalid": "maybe"}), theme_seed=SEED)


# -- in the view language ---------------------------------------------------------------------------------------------------


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.error = Signal("")


VIEW = """name: main
widget: Container
style: {width: 200, height: 100}
children:
  - {widget: Container, name: toggle, style: {width: 40, height: 40, background: primary},
     a11y: {pressed: true, controls: panel, describedby: hint, description: "{{ error }}", invalid: "{{ error != '' }}"}}
  - {widget: Container, name: panel, style: {width: 40, height: 40, background: secondary}}
  - {widget: Text, name: hint, text: Press to open, typography_role: body_small, style: {foreground: on_surface}}
"""


def opened(tmp_path, text=VIEW):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(text)
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    view.window.advance(16)
    return view, app.bindings.viewmodel_for("main")


def test_the_view_language_takes_the_whole_vocabulary(tmp_path):
    a11y._WARNED.clear()
    view, vm = opened(tmp_path)
    vm.error.set("Required")
    view.window.advance(16)
    assert {"pressed", "controls", "describedby", "description", "invalid"} <= a11y._WARNED


def test_the_view_language_sends_resolved_relations_and_bound_values(tmp_path, monkeypatch):
    view, vm = opened(tmp_path)
    node = Recorder({"pressed", "controls", "describedby", "description", "invalid"})
    monkeypatch.setitem(view._built.nodes, "root.toggle", node)
    view._apply_a11y_extras()
    sent = {k: v for call in node.set_calls for k, v in call.items()}
    assert sent["pressed"] is True and sent["controls"] == [view._built.outer["root.panel"]] and sent["describedby"] == [view._built.outer["root.hint"]]


def test_the_view_language_names_a_missing_relation(tmp_path):
    with pytest.raises(ValueError, match="names 'nowhere', which is no node by that name"):
        opened(tmp_path, VIEW.replace("controls: panel", "controls: nowhere"))


def test_the_view_language_checks_values_at_load():
    with pytest.raises(LoadError, match="pressed"):
        parse_view("widget: Container\na11y: {pressed: maybe}\n", "T_View.yaml")
    parse_view("widget: Container\na11y: {pressed: mixed, current: page, busy: true}\n", "T_View.yaml")
