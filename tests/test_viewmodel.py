"""#209 phase 5: ViewModels bound to named views -- one instance serving many views at once, the three ways to bind, handles, the contract."""

import pytest

from tesserae import Signal, ViewModel
from tesserae.spec.nodes import parse_view
from tesserae.viewmodel import BindingError, Bindings, check_view, declared_views, open_view

PIE = "name: data_pie\nwidget: Container\nchildren:\n  - {widget: Text, name: total, text: '{{ len(rows) }} slices'}\n"
LIST = ("name: data_list\nwidget: Container\nstate: {open: false}\nchildren:\n  - for: r in rows\n    key: r.id\n    widget: Text\n    name: row\n"
        "    text: '{{ r.label }}'\n    handlers: {on_click: pick}\n")


class DataViewModel(ViewModel):
    views = ["data_pie", "data_list"]
    made = 0

    def __init__(self):
        super().__init__()
        DataViewModel.made += 1
        self.rows = Signal([{"id": 1, "label": "a"}, {"id": 2, "label": "b"}])
        self.picked = []

    def pick(self):
        self.picked.append(True)


@pytest.fixture(autouse=True)
def reset():
    DataViewModel.made = 0


def doc(source, name="x"):
    return parse_view(source, f"{name}_View.yaml")


def test_declared_views_reads_a_list_or_a_single_string():
    class One(ViewModel):
        views = "only"

    assert declared_views(DataViewModel) == ["data_pie", "data_list"] and declared_views(One) == ["only"] and declared_views(One()) == ["only"]
    assert declared_views(ViewModel) == []


def test_one_instance_serves_two_views_at_once_and_one_signal_updates_both():
    bindings = Bindings()
    bindings.bind(DataViewModel)
    assert DataViewModel.made == 0  # lazily: nothing is made until a view it serves opens
    pie = open_view(doc(PIE), bindings)
    assert DataViewModel.made == 1
    lst = open_view(doc(LIST), bindings)
    assert DataViewModel.made == 1 and pie.viewmodel is lst.viewmodel
    vm = pie.viewmodel
    assert pie.node("total").value("text") == "2 slices"
    assert [c.value("text") for c in lst.composition.root.children] == ["a", "b"]
    vm.rows.set([{"id": 1, "label": "a"}, {"id": 2, "label": "b"}, {"id": 3, "label": "c"}])
    assert pie.node("total").value("text") == "3 slices"
    assert [c.value("text") for c in lst.composition.root.children] == ["a", "b", "c"]
    assert vm.views["data_pie"] is pie and vm.views["data_list"] is lst
    lst.composition.root.children[0].fire("on_click")
    assert vm.picked == [True]


def test_a_view_opened_twice_is_bound_to_the_same_instance_twice():
    bindings = Bindings()
    bindings.bind(DataViewModel)
    first, second = open_view(doc(PIE), bindings), open_view(doc(PIE), bindings)
    assert first.viewmodel is second.viewmodel and DataViewModel.made == 1


def test_bind_an_instance_uses_it():
    vm = DataViewModel()
    bindings = Bindings()
    bindings.bind(vm)
    assert open_view(doc(PIE), bindings).viewmodel is vm and DataViewModel.made == 1


def test_bind_a_factory_makes_one_viewmodel_per_view_instance():
    bindings = Bindings()
    bindings.bind(factory=DataViewModel)
    one, two = open_view(doc(PIE), bindings), open_view(doc(PIE), bindings)
    assert one.viewmodel is not two.viewmodel and DataViewModel.made == 2
    one.viewmodel.rows.set([])
    assert one.node("total").value("text") == "0 slices" and two.node("total").value("text") == "2 slices"


def test_an_unnamed_view_and_a_view_no_viewmodel_serves_are_not_bound():
    bindings = Bindings()
    bindings.bind(DataViewModel)
    static = open_view(doc("widget: Container\nchildren:\n  - {widget: Text, name: t, text: hello}"), bindings)
    assert static.viewmodel is None and static.name is None and DataViewModel.made == 0
    other = open_view(doc("name: elsewhere\nwidget: Text\ntext: hi"), bindings)
    assert other.viewmodel is None
    with pytest.raises(Exception, match="'rows' is not defined"):
        open_view(doc("name: elsewhere\nwidget: Text\ntext: '{{ len(rows) }}'"), bindings)  # it reads a name nothing gives it


def test_binding_errors_are_said_plainly():
    bindings = Bindings()
    bindings.bind(DataViewModel)
    with pytest.raises(BindingError, match="'data_pie' is already served by DataViewModel"):
        bindings.bind(DataViewModel)
    with pytest.raises(BindingError, match="serves no views"):
        Bindings().bind(ViewModel)
    with pytest.raises(BindingError, match="exactly one"):
        Bindings().bind()
    with pytest.raises(BindingError, match="exactly one"):
        Bindings().bind(DataViewModel, factory=DataViewModel)
    with pytest.raises(BindingError, match="not the name 'x'"):
        Bindings().bind("x")

    class NeedsView(ViewModel):
        views = ["needs"]

        def __init__(self, view):
            super().__init__(view)

    bound = Bindings()
    bound.bind(NeedsView)
    with pytest.raises(BindingError, match="takes none"):
        open_view(doc("name: needs\nwidget: Text\ntext: x"), bound)


def test_views_override_names_a_factory_function_serves():
    bindings = Bindings()
    bindings.bind(factory=lambda: DataViewModel(), views=["data_pie"])
    assert open_view(doc(PIE), bindings).viewmodel is not None
    assert bindings.serves("data_pie") and not bindings.serves("data_list")


def test_handles_find_nodes_state_and_say_what_is_missing():
    bindings = Bindings()
    bindings.bind(DataViewModel)
    lst = open_view(doc(LIST), bindings)
    assert lst.node("row").widget == "Text"
    assert lst.state("open").get() is False
    with pytest.raises(KeyError, match="no node named 'nope'"):
        lst.node("nope")
    with pytest.raises(KeyError, match="has no state 'x'"):
        lst.state("x")
    vm = lst.viewmodel
    with pytest.raises(KeyError, match="'data_pie' is not open"):
        vm.views["data_pie"]
    with pytest.raises(KeyError, match="does not serve a view named 'zzz' .it serves: data_pie, data_list"):
        vm.views["zzz"]


def test_a_viewmodel_can_swap_one_view_for_another():
    bindings = Bindings()
    bindings.bind(DataViewModel)
    pie, lst = open_view(doc(PIE), bindings), open_view(doc(LIST), bindings)
    vm = pie.viewmodel
    assert pie.visible.get() and lst.visible.get()  # both are visible at once by default
    vm.show("data_list", instead_of="data_pie")
    assert lst.visible.get() and not pie.visible.get()
    vm.show("data_pie", instead_of=["data_list"])
    assert pie.visible.get() and not lst.visible.get()
    pie.hide()
    pie.show()
    assert pie.visible.get()


def test_the_viewmodel_is_told_when_a_view_opens_and_closes_and_close_releases_the_view():
    events = []

    class Watched(DataViewModel):
        views = ["data_pie"]

        def on_attached(self, handle):
            events.append(("attached", handle.name))

        def on_detached(self, handle):
            events.append(("detached", handle.name))

    bindings = Bindings()
    bindings.bind(Watched)
    pie = open_view(doc(PIE), bindings)
    vm = pie.viewmodel
    assert events == [("attached", "data_pie")] and vm._view is pie
    pie.close()
    pie.close()
    assert events == [("attached", "data_pie"), ("detached", "data_pie")] and "data_pie" not in vm.views
    assert vm.rows._subscribers == []  # nothing of the closed view still follows the signal


def test_a_viewmodel_that_serves_a_name_no_view_has_is_a_warning():
    bindings = Bindings()
    bindings.bind(DataViewModel)
    assert bindings.unserved(["data_pie"]) == ["DataViewModel serves the view 'data_list', but no view has that name"]
    assert bindings.unserved(["data_pie", "data_list"]) == []


def test_the_old_viewmodel_form_still_attaches_to_a_view():
    attached = []

    class View:
        def _attach(self, vm):
            attached.append(vm)

    class Old(ViewModel):
        def __init__(self, view):
            self.n = Signal(0)
            super().__init__(view)

    view = View()
    vm = Old(view)
    assert attached == [vm] and vm._view is view


# -- the contract ----------------------------------------------------------------------------------------------------------


def test_the_contract_lists_every_name_and_action_a_view_uses_that_the_viewmodel_lacks():
    view = doc("name: v\nwidget: Container\nstate: {n: 0}\nchildren:\n  - {widget: Text, text: '{{ title }} {{ n }}', handlers: {on_click: save}}\n"
               "  - {for: r in rows, key: r.id, widget: Rect, handlers: {on_click: 'n = n + 1; open(r.id)'}}\n"
               "  - {widget: Rect, handlers: {on_click: window.close}}\n", "v")

    class Full:
        title = "t"
        rows = []

        def save(self):
            ...

        def open(self, id):
            ...

    assert check_view(view, Full()) == []

    class Partial:
        rows = []
        open = "not callable"

    problems = check_view(view, Partial())
    assert any("'title' is not defined by Partial" in p for p in problems)
    assert any("'save' is not a method of Partial" in p for p in problems)
    assert any("'open' is not a method of Partial" in p for p in problems)
    assert not any("'n'" in p or "'r'" in p or "window" in p for p in problems)  # state, loop variables and built-in actions are not the ViewModel's
    assert problems[0].startswith("v_View.yaml:") and ":error" not in problems[0]


def test_a_view_that_needs_names_says_it_has_no_viewmodel():
    view = doc("widget: Text\ntext: '{{ count }}'", "x")
    assert check_view(view, None) == ["x_View.yaml:1:1: 'count' is not defined: this view has no ViewModel"]
    assert check_view(doc("widget: Text\ntext: hello"), None) == []


def test_expects_declares_names_and_types_the_viewmodel_must_have():
    view = doc("expects: {count: int, rows: list, title: str, add: handler, on: bool, ratio: float}\nwidget: Text\ntext: x")

    class Good:
        count = Signal(3)
        rows = [1]
        title = "t"
        on = True
        ratio = 0.5

        def add(self):
            ...

    assert check_view(view, Good()) == []

    class Bad:
        count = "three"
        rows = {}
        add = 5
        on = 1
        ratio = "x"

    problems = " | ".join(check_view(view, Bad()))
    for expected in ("'count' should be int, it is str", "'rows' should be list, it is dict", "'add' should be a method", "'on' should be bool",
                     "'ratio' should be float", "expects 'title', which Bad does not define"):
        assert expected in problems, problems
    assert "expects 'count': this view has no ViewModel" in " ".join(check_view(view, None))
    assert "unknown type 'colour'" in " ".join(check_view(doc("expects: {a: colour}\nwidget: Text\ntext: x"), type("V", (), {"a": 1})()))


def test_reserved_names_are_not_the_viewmodels_to_provide():
    view = doc("widget: Container\nchildren:\n  - {widget: Text, text: '{{ app.current_screen }}', handlers: {on_change: 'q = event.value'}}\n"
               "  - {widget: Rect, if: 'hovered or focused or pressed'}\n", "r")
    assert check_view(view, type("V", (), {"q": Signal("")})()) == []
