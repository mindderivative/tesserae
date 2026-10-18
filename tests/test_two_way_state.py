"""#277: what a view may write back, and what it keeps. The four questions of the issue, each answered by running the code:

1. which names a handler may assign (`state:` and a `model: true` param, never a plain param, a loop variable or a ViewModel's Computed or attribute);
2. what a model property does when it is not given one bare reference to a writable Signal (one-way: the user's edit stays on screen until the value next changes);
3. what a `state:` keeps across a recomposition (the user's value, over an edited starting value), against a ViewModel Signal (untouched);
4. which of these the pages say (`tests/test_docs_two_way.py` is not needed: the pages are read by `test_docs_no_history` and the build).
"""

import pytest

from tesserae import Computed, Signal, ViewModel
from tesserae.spec.compose import Composer
from tesserae.spec.nodes import LoadError, parse_view

from test_compose import VM, make
from test_composed import BASE, render

STYLE = "    style: {width: 24, height: 24, background: '#6750A4'}\n"
CALL = "params:\n  m: {type: int, default: 0, model: true}\n  p: {type: int, default: 0}\nwidget: Container\nchildren:\n  - {widget: Text, name: t, text: '{{ m }}', handlers: {on_click: '%s'}}\n"


class Flags(ViewModel):
    views = "demo"

    def __init__(self):
        super().__init__()
        self.done = Signal(False)
        self.inverse = Computed(lambda: not self.done.get())
        self.plain = False
        self.rows = Signal([1, 2])


# -- 1. what a handler may assign -------------------------------------------------------------------------------------------------------


def test_a_handler_writes_a_state_name():
    comp, _, _ = make(None, "widget: Container\nstate: {s: 1}\nchildren:\n  - {widget: Text, name: t, text: x, handlers: {on_click: 's = 2'}}")
    comp.find("root.t").fire("on_click")
    assert comp.root.state["s"].get() == 2


@pytest.mark.parametrize("setup", ["p: 3", "p: '{{ count }}'"])
def test_a_handler_cannot_write_a_plain_param_and_is_told_where_at_load(setup):
    with pytest.raises(LoadError, match="V_View.yaml:6:\\d+: error: 'p' is not writable here"):
        make({"V": CALL % "p = 9"}, f"widget: Container\nchildren:\n  - {{widget: V, name: v, {setup}}}")


def test_a_handler_cannot_write_a_loop_variable():
    with pytest.raises(LoadError, match="Main_View.yaml:3:\\d+: error: 'r' is not writable here"):
        make(None, "widget: Container\nchildren:\n  - {for: r in rows, key: r.id, widget: Text, name: t, text: x, handlers: {on_click: 'r = 1'}}")


def test_a_handler_cannot_write_a_viewmodel_attribute_that_is_not_a_signal():
    vm = VM()
    vm.plain = 3
    with pytest.raises(LoadError, match="'plain' is not writable here"):
        make(None, "widget: Container\nchildren:\n  - {widget: Text, name: t, text: x, handlers: {on_click: 'plain = 4'}}", viewmodel=vm)


def test_a_handler_cannot_write_a_computed():
    vm = VM()
    vm.shown = Computed(lambda: vm.count.get() + 1)
    with pytest.raises(LoadError, match="'shown' is not writable here"):
        make(None, "widget: Container\nchildren:\n  - {widget: Text, name: t, text: x, handlers: {on_click: 'shown = 4'}}", viewmodel=vm)


def test_a_misspelt_name_is_found_at_load_and_the_writable_names_are_offered():
    with pytest.raises(LoadError, match="'cuont' is not writable here.*count"):
        make(None, "widget: Container\nchildren:\n  - {widget: Text, name: t, text: x, handlers: {on_click: 'cuont += 1'}}")


def test_an_augmented_assignment_is_checked_too():
    with pytest.raises(LoadError, match="'r' is not writable here"):
        make(None, "widget: Container\nchildren:\n  - {for: r in rows, key: r.id, widget: Text, name: t, text: x, handlers: {on_click: 'r += 1'}}")


def test_a_model_param_is_writable_by_the_view_that_declares_it():
    comp, vm, _ = make({"V": CALL % "m = 9"}, "widget: Container\nchildren:\n  - {widget: V, name: v, m: 3}")
    comp.find("root.v.t").fire("on_click")
    assert comp.find("root.v.t").value("text") == "9"


# -- 2. a model param, by what the caller gives it -----------------------------------------------------------------------------------------


def test_a_bare_viewmodel_signal_is_shared_so_the_views_write_reaches_the_caller():
    comp, vm, _ = make({"V": CALL % "m = 9"}, "widget: Container\nchildren:\n  - {widget: V, name: v, m: '{{ count }}'}")
    comp.find("root.v.t").fire("on_click")
    assert vm.count.get() == 9


def test_a_bare_state_name_is_shared_the_same_way():
    comp, vm, _ = make({"V": CALL % "m = 9"}, "widget: Container\nstate: {s: 5}\nchildren:\n  - {widget: V, name: v, m: '{{ s }}'}")
    comp.find("root.v.t").fire("on_click")
    assert comp.root.state["s"].get() == 9


def test_the_signal_passes_through_a_view_that_passes_it_on():
    out = "params:\n  q: {type: int, default: 0, model: true}\nwidget: Container\nchildren:\n  - {widget: V, name: inner, m: '{{ q }}'}\n"
    comp, vm, _ = make({"V": CALL % "m = 9", "Out": out}, "widget: Container\nchildren:\n  - {widget: Out, name: o, q: '{{ count }}'}")
    comp.find("root.o.inner.t").fire("on_click")
    assert vm.count.get() == 9


def test_an_expression_gives_the_view_a_copy_that_holds_its_write_until_the_expression_changes():
    comp, vm, _ = make({"V": CALL % "m = 9"}, "widget: Container\nchildren:\n  - {widget: V, name: v, m: '{{ count + 1 }}'}")
    text = lambda: comp.find("root.v.t").value("text")  # noqa: E731
    assert text() == "1"
    comp.find("root.v.t").fire("on_click")
    assert text() == "9" and vm.count.get() == 0  # the caller's value was not written
    vm.count.set(5)
    assert text() == "6"  # the expression changed, so the copy follows it again


def test_a_write_stays_when_the_expression_is_set_to_the_value_it_has():
    comp, vm, _ = make({"V": CALL % "m = 9"}, "widget: Container\nchildren:\n  - {widget: V, name: v, m: '{{ count + 1 }}'}")
    comp.find("root.v.t").fire("on_click")
    vm.count.set(0)  # no change
    assert comp.find("root.v.t").value("text") == "9"


def test_a_literal_or_nothing_gives_the_view_its_own_value():
    for call in ("m: 3", "name: v"):
        comp, vm, _ = make({"V": CALL % "m = 9"}, f"widget: Container\nchildren:\n  - {{widget: V, name: v, {call}}}") if "name" not in call else \
            make({"V": CALL % "m = 9"}, "widget: Container\nchildren:\n  - {widget: V, name: v}")
        comp.find("root.v.t").fire("on_click")
        assert comp.find("root.v.t").value("text") == "9" and vm.count.get() == 0


def test_a_param_that_is_not_a_model_follows_its_expression_and_is_not_written():
    view = "params:\n  p: {type: int, default: 0}\nwidget: Text\ntext: '{{ p }}'\n"
    comp, vm, _ = make({"V": view}, "widget: Container\nchildren:\n  - {widget: V, name: v, p: '{{ count }}'}")
    vm.count.set(4)
    assert comp.find("root.v").value("text") == "4"


# -- 2b. a built-in model property, by what it is given ---------------------------------------------------------------------------------


def _checkbox(expr, vmcls=Flags, wrap=""):
    view, vm, _ = render(BASE + wrap + f"  - widget: Checkbox\n    name: c\n    checked: '{expr}'\n" + STYLE, vmcls=vmcls)
    return view, vm, view.control("root.c")


def _click(view):
    view.window.advance(16)
    view.window.simulate("click", node=view.node("root.c"))


def test_a_bare_signal_is_two_way():
    view, vm, control = _checkbox("{{ done }}")
    assert view.handle.node("c").models.keys() == {"checked"}
    _click(view)
    assert vm.done.get() is True and control.checked.get() is True


@pytest.mark.parametrize("expr", ["{{ not done }}", "{{ inverse }}", "{{ plain }}"])
def test_anything_else_is_one_way_and_the_users_edit_is_not_written_back(expr):
    view, vm, control = _checkbox(expr)
    assert view.handle.node("c").models == {}
    _click(view)
    assert vm.done.get() is False  # nothing written


def test_the_users_edit_of_a_one_way_property_stays_until_the_value_next_changes():
    view, vm, control = _checkbox("{{ not done }}")
    assert control.checked.get() is True
    _click(view)
    assert control.checked.get() is False  # the control shows the edit; the expression still says True
    vm.done.set(True)
    assert control.checked.get() is False  # the expression is False now
    vm.done.set(False)
    assert control.checked.get() is True  # and follows it again


def test_a_plain_attribute_is_never_set_again_by_the_view():
    view, vm, control = _checkbox("{{ plain }}")
    _click(view)
    assert control.checked.get() is True and vm.plain is False  # a plain attribute does not notify: the edit stays


def test_a_literal_is_one_way():
    view, vm, _ = render(BASE + "  - widget: Checkbox\n    name: c\n    checked: true\n" + STYLE, vmcls=Flags)
    assert view.handle.node("c").models == {}


def test_a_read_only_param_is_one_way_even_when_it_holds_a_signal():
    view = "params:\n  p: {type: bool, default: true}\nwidget: Checkbox\nchecked: '{{ p }}'\n"
    comp, vm, _ = make({"V": view}, "widget: Container\nchildren:\n  - {widget: V, name: v, p: '{{ show }}'}")
    assert comp.find("root.v").models == {}


# -- 3. what a state keeps -------------------------------------------------------------------------------------------------------------


SOURCE = "widget: Container\nstate: {n: 1}\nchildren:\n  - {widget: Text, name: t, text: '{{ n }} {{ count }}', handlers: {on_click: 'n += 1; count += 1'}}"


def _again(comp, vm, source):
    return Composer({}, vm, previous=comp).compose(parse_view(source, "Main_View.yaml"))


def test_a_state_keeps_the_users_value_over_an_edited_starting_value():
    comp, vm, _ = make(None, SOURCE)
    comp.find("root.t").fire("on_click")
    assert _again(comp, vm, SOURCE.replace("{n: 1}", "{n: 100}")).find("root.t").value("text") == "2 1"


def test_a_state_that_is_renamed_starts_again_and_the_viewmodel_keeps_its_value():
    comp, vm, _ = make(None, SOURCE)
    comp.find("root.t").fire("on_click")
    renamed = SOURCE.replace("n: 1", "k: 7").replace("{{ n }}", "{{ k }}").replace("n += 1", "k += 1")
    assert _again(comp, vm, renamed).find("root.t").value("text") == "7 1"


def test_a_state_of_a_node_that_is_renamed_starts_again():
    source = "widget: Container\nchildren:\n  - widget: Container\n    name: box\n    state: {n: 1}\n    children:\n      - {widget: Text, name: t, text: '{{ n }}', handlers: {on_click: 'n += 1'}}"
    comp, vm, _ = make(None, source)
    comp.find("root.box.t").fire("on_click")
    assert _again(comp, vm, source).find("root.box.t").value("text") == "2"
    assert _again(comp, vm, source.replace("name: box", "name: crate")).find("root.crate.t").value("text") == "1"


def test_the_state_of_a_row_follows_its_key_when_the_rows_are_reordered():
    source = ("widget: Container\nchildren:\n  - for: r in rows\n    key: r.id\n    widget: Container\n    name: row\n    state: {open: false}\n    children:\n"
              "      - {widget: Text, name: t, text: '{{ r.t }} {{ open }}', handlers: {on_click: 'open = True'}}")
    comp, vm, _ = make(None, source)
    comp.find("root.row[1].t").fire("on_click")
    vm.rows.set(list(reversed(vm.rows.get())))
    again = _again(comp, vm, source)
    assert again.find("root.row[1].t").value("text") == "a True" and again.find("root.row[2].t").value("text") == "b False"


# -- #283: the same for the text of an `after(...)` or `every(...)` ---------------------------------------------------------------------------


@pytest.mark.parametrize("timer", ["after", "every"])
def test_a_timer_text_that_assigns_what_cannot_be_written_is_a_load_error(timer):
    with pytest.raises(LoadError, match="'r' is not writable here"):
        make(None, "widget: Container\nchildren:\n  - {for: r in rows, key: r.id, widget: Text, name: t, text: x, handlers: {on_click: '" + timer + "(10, \"r = 1\")'}}")


def test_a_timer_text_that_assigns_state_loads():
    comp, _, _ = make(None, "widget: Container\nstate: {s: 1}\nchildren:\n  - {widget: Text, name: t, text: x, handlers: {on_click: 'after(10, \"s = 2\")'}}")
    assert comp.root.state["s"].get() == 1
