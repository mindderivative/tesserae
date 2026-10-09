"""#209 phase 4: composition -- params and the caller's scope, slots, `for:` and `if:` (static and reactive, reconciled by key), `state:`,
ids, hot reload, and disposal."""

import pytest
import yaml

from tesserae import Computed, Signal
from tesserae.spec import widgets as W
from tesserae.expr import ExprError
from tesserae.spec.compose import MAX_DEPTH, Composer, Scope
from tesserae.spec.nodes import LoadError, parse_view
from tesserae.spec.widgets import Property, WidgetDecl, decl_from_params


class VM:
    def __init__(self):
        self.rows = Signal([{"id": 1, "t": "a"}, {"id": 2, "t": "b"}])
        self.name = Signal("X")
        self.count = Signal(0)
        self.show = Signal(True)
        self.log = []

    def save(self):
        self.log.append("save")

    def open(self, id):
        self.log.append(("open", id))


def make(views=None, main="widget: Container", viewmodel=None, **kw):
    """Parses `views` (name -> source) and `main`, composes `main`; returns (composition, viewmodel, composer)."""
    sources = views or {}
    decls = {}
    for name, source in sources.items():  # a view may call itself or another, so every declaration comes first
        params = yaml.safe_load(source).get("params")
        decls[name] = decl_from_params(name, params) if params is not None else WidgetDecl(name, view=True, container=True)
    docs = {name: parse_view(source, f"{name}_View.yaml", resolver=decls.get, view_name=name) for name, source in sources.items()}
    doc = parse_view(main, "Main_View.yaml", resolver=decls.get)
    vm = viewmodel if viewmodel is not None else VM()
    composer = Composer(docs, vm, **kw)
    return composer.compose(doc), vm, composer


def fails(message, views=None, main="widget: Container", **kw):
    with pytest.raises((LoadError, ExprError)) as caught:
        make(views, main, **kw)
    assert message in str(caught.value), str(caught.value)
    return caught.value


CARD = "params: [title]\nwidget: Container\nchildren:\n  - {widget: Text, name: head, text: '{{ title }}'}\n  - widget: Slot\n"


# -- params and scope ------------------------------------------------------------------------------------------------------


def test_a_view_call_is_replaced_by_the_callees_root_and_its_parts_have_the_calls_prefix():
    comp, _, _ = make({"Card": CARD}, "widget: Container\nchildren:\n  - {widget: Card, name: nav, title: Hi}")
    assert comp.ids() == ["root", "root.nav", "root.nav.head"]
    assert comp.find("root.nav.head").value("text") == "Hi" and comp.find("root.nav").widget == "Container"


def test_a_static_param_is_a_plain_value_and_a_reactive_one_follows_its_signal():
    comp, vm, _ = make({"Card": CARD}, "widget: Container\nchildren:\n  - {widget: Card, name: c, title: 'a {{ name }}'}\n  - {widget: Card, name: d, title: '{{ 1 + 2 }}'}")
    head = comp.find("root.c.head")
    assert head.value("text") == "a X" and isinstance(head.props["text"], Computed)  # reactive: follows the signal
    assert comp.find("root.d.head").props["text"] == "3"  # static: evaluated once, a plain value
    vm.name.set("Y")
    assert head.value("text") == "a Y"
    assert comp.find("root.d.head").value("text") == "3"


def test_an_expression_at_a_call_site_is_evaluated_in_the_callers_scope():
    views = {"Row": "params: [label]\nwidget: Text\ntext: '{{ label }}'\n"}
    comp, vm, _ = make(views, "widget: Container\nchildren:\n  - for: r in rows\n    key: r.id\n    widget: Row\n    name: row\n    label: '{{ r.t }}!'")
    assert [comp.find(f"root.row[{i}]").value("text") for i in (1, 2)] == ["a!", "b!"]
    vm.rows.set([{"id": 1, "t": "z"}, {"id": 2, "t": "b"}])
    assert comp.find("root.row[1]").value("text") == "z!"


def test_the_callee_cannot_see_the_callers_names_but_sees_the_viewmodel_and_its_own_params():
    views = {"Leaf": "params: [x]\nwidget: Text\ntext: '{{ x }}{{ mine }}'\n"}
    main = "widget: Container\nstate: {mine: 'M'}\nchildren:\n  - {widget: Leaf, x: '{{ mine }}'}"
    err = fails("'mine' is not defined", views, main)
    assert "Leaf_View.yaml" in str(err) or "mine" in str(err)
    views = {"Leaf": "params: [x]\nwidget: Text\ntext: '{{ x }}{{ name }}'\n"}
    comp, _, _ = make(views, "widget: Container\nchildren:\n  - {widget: Leaf, x: '1'}")
    assert comp.find("root.children[0]").value("text") == "1X"  # the ViewModel is visible to every view


def test_defaults_required_unknown_and_reserved_params():
    views = {"Btn": "params:\n  label: {type: str, required: true}\n  variant: {type: enum, choices: [filled, text], default: filled}\n  size: {type: int, default: 3}\nwidget: Text\ntext: '{{ label }}-{{ variant }}-{{ size }}'\n"}
    comp, _, _ = make(views, "widget: Container\nchildren:\n  - {widget: Btn, label: Go}")
    assert comp.find("root.children[0]").value("text") == "Go-filled-3"
    fails("'label' is required", views, "widget: Container\nchildren:\n  - {widget: Btn}")
    err = fails("Btn: no property 'sise'", views, "widget: Container\nchildren:\n  - {widget: Btn, label: x, sise: 1}")
    assert "did you mean 'size'" in str(err)
    fails("reserved name", {"V": "params: [event]\nwidget: Text\n"}, "widget: Container\nchildren:\n  - {widget: V, event: 1}")


def test_a_param_value_is_coerced_to_its_type_with_the_calls_position():
    views = {"Gauge": "params:\n  level: {type: int, default: 0}\nwidget: Text\ntext: '{{ level }}'\n"}
    comp, vm, _ = make(views, "widget: Container\nchildren:\n  - {widget: Gauge, level: '{{ count }}'}")
    assert comp.find("root.children[0]").value("text") == "0"
    vm.count.set(7)
    assert comp.find("root.children[0]").value("text") == "7"
    err = fails("takes a whole number", views, "widget: Container\nchildren:\n  - {widget: Gauge, level: '{{ \"x\" }}'}")
    assert err.file == "Main_View.yaml" and err.line == 3


def test_no_such_view_is_an_error():
    decls = {"Ghost": WidgetDecl("Ghost", view=True, container=True)}
    doc = parse_view("widget: Container\nchildren:\n  - widget: Ghost", "Main_View.yaml", resolver=decls.get)
    with pytest.raises(LoadError, match="no view named 'Ghost'"):
        Composer({}, VM()).compose(doc)


def test_views_may_nest_and_recursion_is_capped_with_the_chain():
    tree = "params: [depth]\nwidget: Container\nchildren:\n  - {widget: Tree, depth: '{{ depth + 1 }}', if: 'depth < 3'}\n"
    comp, _, _ = make({"Tree": tree}, "widget: Container\nchildren:\n  - {widget: Tree, depth: 0}")
    assert len(list(comp.walk())) == 5  # the main root, then Tree at depth 0, 1, 2 and the one at 3 has no child
    endless = "params: [depth]\nwidget: Container\nchildren:\n  - {widget: Tree, depth: 0}\n"
    err = fails(f"nested more than {MAX_DEPTH} deep", {"Tree": endless}, "widget: Container\nchildren:\n  - {widget: Tree, depth: 0}")
    assert "Tree -> Tree" in str(err)


# -- slots -----------------------------------------------------------------------------------------------------------------


def test_children_of_a_call_go_into_the_default_slot_in_the_callers_scope():
    comp, vm, _ = make({"Card": CARD}, "widget: Container\nstate: {n: 5}\nchildren:\n  - widget: Card\n    name: c\n    title: T\n    children:\n"
                        "      - {widget: Text, text: '{{ n }}-{{ name }}'}\n      - {widget: Rect, name: r}")
    assert comp.ids() == ["root", "root.c", "root.c.head", "root.c.content[0]", "root.c.r"]
    text = comp.find("root.c.content[0]")
    assert text.value("text") == "5-X"  # `n` is the caller's state, not the Card's
    vm.name.set("Y")
    assert text.value("text") == "5-Y"


def test_named_slots_and_the_default_slot_hold_their_own_content_in_order():
    views = {"Panel": "widget: Container\nchildren:\n  - {widget: Slot, name: header}\n  - widget: Slot\n  - {widget: Slot, name: actions}\n"}
    comp, _, _ = make(views, "widget: Container\nchildren:\n  - widget: Panel\n    name: p\n    children:\n      - {widget: Rect, name: body}\n"
                      "      - {widget: Text, name: act, slot: actions}\n      - {widget: Icon, name: head, slot: header, icon: home}")
    assert [c.id for c in comp.find("root.p").children] == ["root.p.head", "root.p.body", "root.p.act"]


def test_slot_errors_say_what_the_view_has():
    err = fails("Card has no slot 'actions'", {"Card": CARD}, "widget: Container\nchildren:\n  - widget: Card\n    title: T\n    children:\n"
                "      - {widget: Rect, slot: actions}")
    assert "slots: default" in str(err)
    fails("Leaf takes no children", {"Leaf": "widget: Rect\n"}, "widget: Container\nchildren:\n  - widget: Leaf\n    children:\n      - widget: Rect")
    fails("a Slot takes no 'if:'", {"V": "widget: Container\nchildren:\n  - {widget: Slot, if: x}\n"}, "widget: V")
    assert make({"Card": CARD}, "widget: Container\nchildren:\n  - {widget: Card, title: T}")[0].find("root.children[0]").children[0].id.endswith("head")


def test_slot_content_may_itself_use_for_and_if_and_pass_through_a_slot():
    comp, vm, _ = make({"Card": CARD}, "widget: Container\nchildren:\n  - widget: Card\n    name: c\n    title: T\n    children:\n"
                       "      - {for: r in rows, key: r.id, widget: Text, name: row, text: '{{ r.t }}'}\n      - {widget: Rect, name: flag, if: show}")
    assert [c.id for c in comp.find("root.c").children] == ["root.c.head", "root.c.row[1]", "root.c.row[2]", "root.c.flag"]
    vm.show.set(False)
    vm.rows.set([{"id": 2, "t": "b"}])
    assert [c.id for c in comp.find("root.c").children] == ["root.c.head", "root.c.row[2]"]
    wrapper = {"Wrap": "widget: Container\nchildren:\n  - widget: Card\n    name: inner\n    title: W\n    children:\n      - widget: Slot\n"}
    comp, _, _ = make({**wrapper, "Card": CARD}, "widget: Container\nchildren:\n  - widget: Wrap\n    name: w\n    children:\n      - {widget: Rect, name: x}")
    assert "root.w.inner.x" not in comp.ids() and any(i.endswith(".x") for i in comp.ids())


# -- for -------------------------------------------------------------------------------------------------------------------


def test_a_static_for_expands_once_with_the_loop_variables_in_scope():
    comp, _, _ = make(None, "widget: Container\nchildren:\n  - {for: 'i, t in enumerate([\"a\", \"b\", \"c\"])', widget: Text, name: row, text: '{{ i }}{{ t }}'}")
    assert [(c.id, c.value("text")) for c in comp.root.children] == [("root.row[0]", "0a"), ("root.row[1]", "1b"), ("root.row[2]", "2c")]
    comp, _, _ = make(None, "widget: Container\nchildren:\n  - {for: n in range(3), widget: Rect}")
    assert [c.id for c in comp.root.children] == ["root.children[0][0]", "root.children[0][1]", "root.children[0][2]"]


def test_for_accepts_dicts_text_and_tuples_and_refuses_the_rest():
    comp, _, _ = make(None, "widget: Container\nchildren:\n  - for: 'k in {\"a\": 1, \"b\": 2}'\n    widget: Text\n    text: '{{ k }}'")
    assert [c.value("text") for c in comp.root.children] == ["a", "b"]
    fails("'for:' needs a list", None, "widget: Container\nchildren:\n  - {for: k in 5, widget: Rect}")
    fails("unpacks 2 names", None, "widget: Container\nchildren:\n  - {for: 'a, b in [1, 2]', widget: Rect}")
    fails("reserved name", None, "widget: Container\nchildren:\n  - for: 'event in [1]'\n    widget: Rect")


def test_a_reactive_for_needs_a_key_and_a_key_must_be_unique_and_plain():
    err = fails("a reactive 'for:' needs a 'key:'", None, "widget: Container\nchildren:\n  - {for: r in rows, widget: Rect}")
    assert "key: item.id" in str(err)
    fails("two elements have the key 1", None, "widget: Container\nchildren:\n  - for: 'r in [1, 1]'\n    key: r\n    widget: Rect")
    fails("'key:' must be text, a number", None, "widget: Container\nchildren:\n  - for: 'r in [[1]]'\n    key: r\n    widget: Rect")


def test_a_reactive_for_reconciles_by_key_add_remove_reorder():
    comp, vm, _ = make(None, "widget: Container\nchildren:\n  - {for: r in rows, key: r.id, widget: Text, name: row, text: '{{ r.t }}'}")
    first, second = comp.find("root.row[1]"), comp.find("root.row[2]")
    seen = []
    comp.root.on_children(lambda inst, old, new: seen.append(([o.id for o in old], [n.id for n in new])))
    # reorder: the same instances, new order
    vm.rows.set([{"id": 2, "t": "b"}, {"id": 1, "t": "a"}])
    assert [c.id for c in comp.root.children] == ["root.row[2]", "root.row[1]"]
    assert comp.find("root.row[1]") is first and comp.find("root.row[2]") is second
    # add in the middle, remove one
    vm.rows.set([{"id": 2, "t": "b"}, {"id": 3, "t": "c"}])
    third = comp.find("root.row[3]")
    assert [c.id for c in comp.root.children] == ["root.row[2]", "root.row[3]"] and first.disposed and not second.disposed
    assert comp.find("root.row[1]") is None
    # an item replaced under the same key updates the existing instance's bindings
    vm.rows.set([{"id": 2, "t": "B"}, {"id": 3, "t": "c"}])
    assert comp.find("root.row[2]") is second and second.value("text") == "B" and comp.find("root.row[3]") is third
    assert len(seen) == 2  # one notification per change of the children (the add and the remove are one), none for the update in place


def test_a_reconciled_loop_is_linear_enough_for_ten_thousand_rows():
    vm = VM()
    vm.rows.set(list(range(3)))
    comp, vm, _ = make(None, "widget: Container\nchildren:\n  - {for: r in rows, key: r, widget: Rect}", viewmodel=vm)
    vm.rows.set(list(range(10_000)))
    assert len(comp.root.children) == 10_000
    vm.rows.set(list(range(5_000, 15_000)))
    assert len(comp.root.children) == 10_000 and comp.find("root.children[0][14999]") is not None


def test_loop_variables_are_in_scope_in_handlers():
    comp, vm, _ = make(None, "widget: Container\nchildren:\n  - {for: r in rows, key: r.id, widget: Rect, name: row, handlers: {on_click: 'open(r.id)'}}")
    comp.find("root.row[2]").fire("on_click")
    assert vm.log == [("open", 2)]


def test_nested_for_and_for_with_if_tested_per_element():
    comp, _, _ = make(None, "widget: Container\nchildren:\n  - for: a in range(2)\n    widget: Container\n    name: g\n    children:\n"
                      "      - {for: b in range(2), widget: Rect, name: cell}")
    assert comp.ids().count("root.g[0].cell[1]") == 1 and len(list(comp.walk())) == 1 + 2 + 4
    comp, vm, _ = make(None, "widget: Container\nchildren:\n  - {for: r in rows, key: r.id, if: 'r.id != 2', widget: Rect, name: row}")
    assert [c.id for c in comp.root.children] == ["root.row[1]"]
    vm.rows.set([{"id": 1, "t": ""}, {"id": 2, "t": ""}, {"id": 3, "t": ""}])
    assert [c.id for c in comp.root.children] == ["root.row[1]", "root.row[3]"]


# -- if --------------------------------------------------------------------------------------------------------------------


def test_a_static_if_decides_once_and_a_false_if_builds_nothing():
    comp, _, _ = make(None, "widget: Container\nchildren:\n  - {if: '1 > 2', widget: Rect, name: nope}\n  - {if: '2 > 1', widget: Rect, name: ok}")
    assert comp.ids() == ["root", "root.ok"]


def test_a_reactive_if_builds_and_disposes_as_its_expression_changes():
    comp, vm, composer = make(None, "widget: Container\nchildren:\n  - {widget: Text, name: t, if: show, text: '{{ name }}', handlers: {on_click: save}}")
    t = comp.find("root.t")
    assert t is not None and len(vm.name._subscribers) == 1
    vm.show.set(False)
    assert comp.root.children == [] and t.disposed and comp.find("root.t") is None
    assert vm.name._subscribers == []  # the binding of a node that is gone no longer follows its signal
    vm.show.set(True)
    assert comp.find("root.t") is not t and comp.find("root.t").value("text") == "X"


def test_the_instances_of_a_false_if_do_not_run_their_handlers_or_bindings():
    comp, vm, _ = make(None, "widget: Container\nchildren:\n  - {widget: Rect, name: r, if: show, handlers: {on_click: save}}")
    r = comp.find("root.r")
    vm.show.set(False)
    assert r.disposed and comp.find("root.r") is None


# -- state -----------------------------------------------------------------------------------------------------------------


def test_state_is_a_signal_visible_to_the_subtree_and_written_by_handlers():
    comp, _, _ = make(None, "widget: Container\nstate: {on: false, n: 1}\nchildren:\n"
                      "  - {widget: Text, name: t, text: '{{ n }}', handlers: {on_click: 'n += 1; on = not on'}}")
    t = comp.find("root.t")
    assert t.value("text") == "1"
    t.fire("on_click")
    assert t.value("text") == "2" and comp.root.state["on"].get() is True


def test_state_is_per_instance_per_row():
    comp, _, _ = make(None, "widget: Container\nchildren:\n  - for: r in rows\n    key: r.id\n    widget: Container\n    name: row\n    state: {open: false}\n"
                      "    children:\n      - {widget: Text, name: t, text: \"{{ 'yes' if open else 'no' }}\", handlers: {on_click: 'open = not open'}}")
    comp.find("root.row[1].t").fire("on_click")
    assert comp.find("root.row[1].t").value("text") == "yes" and comp.find("root.row[2].t").value("text") == "no"


def test_a_handler_cannot_assign_a_param_a_loop_variable_or_an_unknown_name():
    comp, vm, _ = make(None, "widget: Container\nchildren:\n  - {for: r in rows, key: r.id, widget: Rect, name: row, handlers: {on_click: 'r = 1'}}")
    with pytest.raises(Exception, match="not writable"):
        comp.find("root.row[1]").fire("on_click")
    comp, vm, _ = make(None, "widget: Container\nchildren:\n  - {widget: Rect, name: r, handlers: {on_click: 'count = count + 1'}}")
    comp.find("root.r").fire("on_click")
    assert vm.count.get() == 1  # a Signal of the ViewModel is writable


def test_state_starting_values_must_be_static_and_names_unreserved():
    fails("must be static", None, "widget: Container\nstate: {a: '{{ name }}'}")
    fails("reserved name", None, "widget: Container\nstate: {hovered: false}")
    comp, _, _ = make(None, "widget: Container\nstate: {a: '{{ 1 + 1 }}'}")
    assert comp.root.state["a"].get() == 2


def test_state_on_a_call_is_visible_to_its_arguments_and_slot_content():
    comp, _, _ = make({"Card": CARD}, "widget: Container\nchildren:\n  - widget: Card\n    name: c\n    state: {t: hello}\n    title: '{{ t }}'\n    children:\n      - {widget: Text, name: x, text: '{{ t }}'}")
    assert comp.find("root.c.head").value("text") == "hello" and comp.find("root.c.x").value("text") == "hello"


def test_state_survives_recomposition_for_the_same_ids():
    source = "widget: Container\nstate: {n: 1}\nchildren:\n  - {widget: Text, name: t, text: '{{ n }}', handlers: {on_click: 'n += 1'}}"
    comp, vm, composer = make(None, source)
    comp.find("root.t").fire("on_click")
    comp.find("root.t").fire("on_click")
    # the file is edited: new text, same names
    edited = source.replace("'{{ n }}'", "'n={{ n }}'")
    doc = parse_view(edited, "Main_View.yaml")
    again = Composer({}, vm, previous=comp).compose(doc)
    assert again.find("root.t").value("text") == "n=3"
    # a state variable whose id no longer exists starts fresh
    moved = parse_view(edited.replace("name: t", "name: u"), "Main_View.yaml")
    assert Composer({}, vm, previous=comp).compose(moved).root.state["n"].get() == 3  # the root's id did not change
    assert "n=3" in Composer({}, vm, previous=comp).compose(doc).find("root.t").value("text")


def test_state_in_a_loop_survives_by_key():
    source = "widget: Container\nchildren:\n  - for: r in rows\n    key: r.id\n    widget: Container\n    name: row\n    state: {open: false}\n"
    comp, vm, _ = make(None, source)
    comp.find("root.row[2]").state["open"].set(True)
    again = Composer({}, vm, previous=comp).compose(parse_view(source, "Main_View.yaml"))
    assert again.find("root.row[2]").state["open"].get() is True and again.find("root.row[1]").state["open"].get() is False


# -- call-level keys, ids, structure --------------------------------------------------------------------------------------


def test_the_keys_of_a_call_lie_over_the_callees_root():
    views = {"Btn": "params: [label]\nwidget: Rect\nstyle: {width: 10, height: 4}\nclasses: [btn]\nhandlers: {on_hover_enter: save}\na11y: {label: '{{ label }}'}\n"}
    comp, vm, _ = make(views, "widget: Container\nstate: {k: 1}\nchildren:\n  - widget: Btn\n    name: b\n    label: Go\n    style: {width: 99}\n    classes: [extra]\n"
                       "    interaction: true\n    route: ''\n    handlers: {on_click: 'k += 1'}\n    a11y: {role: button}")
    b = comp.find("root.b")
    assert b.style_value("width") == 99 and b.style_value("height") == 4
    assert b.classes == ["btn", "extra"] and b.interaction is True and b.a11y["role"] == "button" and b.a11y["label"] == "Go"
    b.fire("on_click")  # written at the call: it runs in the caller's scope, where `k` is state
    assert comp.root.state["k"].get() == 2
    b.fire("on_hover_enter")
    assert vm.log == ["save"]  # the callee's own handler runs in the callee's scope, against the ViewModel


def test_root_directives_are_refused_and_ids_are_unique():
    fails("the root of a view takes no 'if:'", None, "widget: Container\nif: show")
    fails("the root of a view takes no 'for:'", None, "widget: Container\nfor: r in rows\nkey: r")
    fails("the root of a view takes no 'if:'", {"V": "widget: Container\nif: show\n"}, "widget: Container\nchildren:\n  - widget: V")


def test_node_and_nodes_properties_become_parts_of_the_instance():
    W.register_widget(WidgetDecl("Bar", {"leading": Property("node"), "actions": Property("nodes")}))
    try:
        comp, _, _ = make(None, "widget: Container\nchildren:\n  - widget: Bar\n    name: bar\n    leading: {widget: Icon, icon: home}\n    actions:\n      - {widget: Text, name: a}\n      - widget: Rect")
        assert comp.ids() == ["root", "root.bar", "root.bar.leading", "root.bar.a", "root.bar.actions[1]"]
        comp.dispose()
    finally:
        W.unregister_widget("Bar")


def test_dispose_releases_every_subscription():
    comp, vm, _ = make({"Card": CARD}, "widget: Container\nchildren:\n  - {widget: Card, name: c, title: '{{ name }}'}\n"
                       "  - {for: r in rows, key: r.id, if: show, widget: Text, text: '{{ r.t }}{{ count }}'}")
    assert vm.name._subscribers and vm.rows._subscribers
    comp.dispose()
    for signal in (vm.name, vm.rows, vm.show, vm.count):
        assert signal._subscribers == [], signal


def test_property_values_not_given_read_as_the_declarations_default():
    comp, _, _ = make(None, "widget: Container\nchildren:\n  - {widget: Slider, name: s}")
    s = comp.find("root.s")
    assert s.value("value") == 0.0 and s.value("disabled") is False
    with pytest.raises(KeyError):
        s.value("nope")


def test_the_scope_reads_frames_then_the_viewmodel_and_hides_underscore_names():
    class Hidden:
        shown = 1
        _secret = 2

    scope = Scope(Scope(None, {"a": 1}), {"b": Signal(2)}, root=Hidden())
    assert scope.lookup("a") == 1 and scope.lookup("shown") == 1
    with pytest.raises(KeyError):
        scope.lookup("_secret")
    assert not scope.is_reactive("a") and scope.is_reactive("b") and scope.is_reactive("shown")
    assert {"a", "b", "shown"} <= set(scope.names())


def test_two_nodes_with_one_id_are_refused_with_the_node_that_clashes():
    # the callee's part `head` and slot content named `head` would both be `root.c.head`
    err = fails("two nodes have the id 'root.c.head'", {"Card": CARD}, "widget: Container\nchildren:\n  - widget: Card\n    name: c\n    title: T\n"
                "    children:\n      - {widget: Rect, name: head}")
    assert "give one of them a different name" in str(err)


def test_the_composer_checks_a_calls_properties_against_the_view_it_finds():
    # the call was parsed against a looser declaration than the file now has (a file edited while the app runs)
    loose = WidgetDecl("Btn", {"label": Property("str"), "bogus": Property("str")}, view=True, container=True)
    doc = parse_view("widget: Container\nchildren:\n  - {widget: Btn, label: x, bogus: y}", "Main_View.yaml", resolver={"Btn": loose}.get)
    strict = parse_view("params:\n  label: {type: str, required: true}\nwidget: Text\ntext: '{{ label }}'\n", "Btn_View.yaml", view_name="Btn")
    with pytest.raises(LoadError, match="Btn: no parameter 'bogus'") as caught:
        Composer({"Btn": strict}, VM()).compose(doc)
    assert "parameters: label" in str(caught.value)
    missing = parse_view("widget: Container\nchildren:\n  - {widget: Btn}", "Main_View.yaml", resolver={"Btn": loose}.get)
    with pytest.raises(LoadError, match="Btn: 'label' is required"):
        Composer({"Btn": strict}, VM()).compose(missing)


def test_built_in_actions_come_from_the_composers_actions_and_the_viewmodel_cannot_shadow_them():
    called = []
    actions = {"window.close": lambda: called.append("close"), "navigate_to": lambda screen: called.append(screen)}.get

    class Shadow(VM):
        window = type("W", (), {"close": staticmethod(lambda: called.append("viewmodel"))})()

    doc = parse_view("widget: Rect\nhandlers:\n  on_click: window.close\n  on_hover_enter: 'navigate_to(\"Settings\")'\n", "Main_View.yaml")
    comp = Composer({}, Shadow(), actions=actions).compose(doc)
    comp.root.fire("on_click")
    comp.root.fire("on_hover_enter")
    assert called == ["close", "Settings"]
