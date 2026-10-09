"""#209 phase 5: a composed view on screen -- bindings, handlers, `for:` and `if:` reaching real nodes, two-way edits, and the App glue."""

import pytest

from tesserae import App, Signal, ViewModel
from tesserae.composed import ComposedView, open_composed
from tesserae.spec.nodes import parse_view
from tesserae.spec.widgets import decl_from_params
from tesserae.viewmodel import Bindings

SEED = (103, 80, 164, 255)
TEXT = "typography_role: body_large\n    style: {width: 100, height: 20, foreground: '#000000'}"


class DemoVM(ViewModel):
    views = ["demo", "other"]

    def __init__(self):
        super().__init__()
        self.title = Signal("Hello")
        self.rows = Signal([{"id": 1, "t": "a"}])
        self.show_extra = Signal(False)
        self.done = Signal(False)
        self.color = Signal("#6750A4")
        self.log = []

    def bump(self):
        self.log.append("bump")


def render(source, vmcls=DemoVM, views=None, **kw):
    doc = parse_view(source, "Demo_View.yaml", resolver=(views or {}).get)
    bindings = Bindings()
    bindings.bind(vmcls)
    callee = kw.pop("callee", None)
    view = open_composed(doc, bindings, callee, theme_seed=SEED, **kw)
    return view, view.handle.viewmodel, bindings


BASE = "name: demo\nwidget: Container\nstyle: {flex_direction: vertical, width: 300, height: 300}\nchildren:\n"


def test_a_bound_property_reaches_the_node_and_follows_its_signal():
    view, vm, _ = render(BASE + "  - widget: Text\n    name: head\n    text: '{{ title }} {{ 1 + 1 }}'\n    " + TEXT + "\n")
    assert view.node("root.head").get("text") == "Hello 2"
    vm.title.set("Bye")
    assert view.node("root.head").get("text") == "Bye 2"


def test_a_reactive_style_value_reaches_the_node():
    view, vm, _ = render(BASE + "  - widget: Rect\n    name: r\n    style: {width: 40, height: 20, background: '{{ color }}'}\n")
    before = view.node("root.r").get("fill")
    vm.color.set("#B3261E")
    assert view.node("root.r").get("fill") != before


def test_a_click_runs_the_handler_in_the_scope_it_was_written():
    view, vm, _ = render(BASE + "  - widget: Rect\n    name: a\n    style: {width: 40, height: 20, background: '#6750A4'}\n    handlers: {on_click: bump}\n"
                         "  - widget: Rect\n    name: b\n    state: {n: 0}\n    style: {width: 40, height: 20, background: '#6750A4'}\n    handlers: {on_click: 'n += 1'}\n"
                         "  - widget: Text\n    name: t\n    text: 'x'\n    " + TEXT + "\n")
    view.window.advance(16)
    view.window.simulate("click", node=view.node("root.a"))
    assert vm.log == ["bump"]
    view.window.simulate("click", node=view.node("root.b"))
    view.window.simulate("click", node=view.node("root.b"))
    assert view.handle.node("b").state["n"].get() == 2


def test_for_adds_and_removes_real_nodes_and_keeps_the_ones_that_stay():
    view, vm, _ = render(BASE + "  - for: r in rows\n    key: r.id\n    widget: Text\n    name: row\n    text: '{{ r.t }}'\n    " + TEXT + "\n")
    first = view.node("root.row[1]")
    vm.rows.set([{"id": 1, "t": "a"}, {"id": 2, "t": "b"}])
    assert view.node("root.row[2]").get("text") == "b" and view.node("root.row[1]") == first
    vm.rows.set([{"id": 2, "t": "B"}])
    assert view.node("root.row[2]").get("text") == "B"
    with pytest.raises(ValueError, match="no widget with id 'root.row.1.'"):
        view.node("root.row[1]")


def test_if_builds_and_removes_a_real_node_and_a_handler_on_it_stays_wired():
    view, vm, _ = render(BASE + "  - widget: Rect\n    name: extra\n    if: show_extra\n    style: {width: 40, height: 20, background: '#6750A4'}\n"
                         "    handlers: {on_click: bump}\n")
    with pytest.raises(ValueError, match="no widget"):
        view.node("root.extra")
    vm.show_extra.set(True)
    view.window.advance(16)
    view.window.simulate("click", node=view.node("root.extra"))
    assert vm.log == ["bump"]
    vm.show_extra.set(False)
    with pytest.raises(ValueError, match="no widget"):
        view.node("root.extra")


def test_a_checkbox_follows_the_signal_and_the_users_click_writes_it_back():
    view, vm, _ = render(BASE + "  - widget: Checkbox\n    name: c\n    checked: '{{ done }}'\n    style: {width: 24, height: 24, background: '#6750A4'}\n")
    control = view.control("root.c")
    assert control.checked.get() is False
    vm.done.set(True)
    assert control.checked.get() is True
    view.window.advance(16)
    view.window.simulate("click", node=view.node("root.c"))
    assert vm.done.get() is False  # the click toggled the control and the edit went back to the Signal


def test_a_model_parameter_given_a_bare_signal_passes_the_signal_through_a_view():
    check = "params:\n  on: {type: bool, model: true}\nwidget: Checkbox\nchecked: '{{ on }}'\nstyle: {width: 24, height: 24, background: '#6750A4'}\n"
    decls = {"Check": decl_from_params("Check", {"on": {"type": "bool", "model": True}})}
    docs = {"Check": parse_view(check, "Check_View.yaml", resolver=decls.get, view_name="Check")}
    view, vm, _ = render(BASE + "  - {widget: Check, name: c, on: '{{ done }}'}\n", views=decls, callee=docs.get)
    control = view.control("root.c")
    vm.done.set(True)
    assert control.checked.get() is True
    view.window.advance(16)
    view.window.simulate("click", node=view.node("root.c"))
    assert vm.done.get() is False


def test_a_view_call_with_slot_content_renders_in_one_tree_and_a_handler_at_the_call_runs_in_the_callers_scope():
    card = "params: [title]\nwidget: Container\nstyle: {flex_direction: vertical, width: 200, height: 100}\nchildren:\n  - widget: Text\n    name: head\n    text: '{{ title }}'\n    " + TEXT + "\n  - widget: Slot\n"
    decls = {"Card": decl_from_params("Card", ["title"])}
    docs = {"Card": parse_view(card, "Card_View.yaml", resolver=decls.get, view_name="Card")}
    view, vm, _ = render(BASE + "  - widget: Card\n    name: c\n    title: '{{ title }}!'\n    handlers: {on_click: bump}\n    children:\n"
                         "      - {widget: Text, name: inside, text: slotted, " + TEXT.replace("\n    ", ", ") + "}\n", views=decls, callee=docs.get)
    assert view.node("root.c.head").get("text") == "Hello!" and view.node("root.c.inside").get("text") == "slotted"
    vm.title.set("Yo")
    assert view.node("root.c.head").get("text") == "Yo!"
    view.window.advance(16)
    view.window.simulate("click", node=view.node("root.c"))
    assert vm.log == ["bump"]


def test_hiding_a_view_hides_its_root_and_close_stops_it_following_anything():
    view, vm, _ = render(BASE + "  - widget: Text\n    name: head\n    text: '{{ title }}'\n    " + TEXT + "\n")
    assert view.root.get("visible") is True
    view.handle.hide()
    assert view.root.get("visible") is False
    view.handle.show()
    assert view.root.get("visible") is True
    view.close()
    vm.title.set("after")  # nothing follows it any more
    assert view.node("root.head").get("text") == "Hello"
    assert vm.title._subscribers == []


def test_two_views_of_one_viewmodel_are_rendered_at_once_and_both_follow_one_signal():
    class Pair(ViewModel):
        views = ["pie", "list"]

        def __init__(self):
            super().__init__()
            self.rows = Signal([1, 2])

    bindings = Bindings()
    bindings.bind(Pair)
    pie = open_composed(parse_view("name: pie\nwidget: Text\ntext: '{{ len(rows) }} slices'\ntypography_role: body_large\nstyle: {width: 100, height: 20, foreground: '#000000'}\n", "Pie_View.yaml"), bindings, theme_seed=SEED)
    lst = open_composed(parse_view("name: list\nwidget: Container\nstyle: {flex_direction: vertical, width: 100, height: 100}\nchildren:\n"
                                   "  - for: r in rows\n    key: r\n    widget: Text\n    name: row\n    text: '{{ r }}'\n    " + TEXT, "List_View.yaml"),
                        bindings, theme_seed=SEED)
    vm = pie.handle.viewmodel
    assert vm is lst.handle.viewmodel and pie.root.get("text") == "2 slices"
    vm.rows.set([1, 2, 3])
    assert pie.root.get("text") == "3 slices" and lst.node("root.row[3]").get("text") == "3"
    assert vm.views["pie"].closed is False and vm.views["list"] is lst.handle


def test_a_property_the_renderer_does_not_draw_yet_is_named_not_dropped():
    with pytest.raises(ValueError, match="Image.frame .a video frame. is not drawn"):
        render(BASE + "  - {widget: Image, name: i, frame: '{{ title }}', style: {width: 10, height: 10}}\n")


# -- the App ---------------------------------------------------------------------------------------------------------------


def project(tmp_path):
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        "name: main\nwidget: Container\nstyle: {flex_direction: vertical, width: 300, height: 200}\nchildren:\n"
        "  - widget: Banner\n    name: banner\n    text: '{{ title }}'\n"
        "  - {widget: Rect, name: go, style: {width: 40, height: 20, background: '#6750A4'}, handlers: {on_click: bump}}\n")
    (tmp_path / "Views" / "Banner_View.yaml").write_text(
        "params: [text]\nwidget: Text\ntext: '{{ text }}'\ntypography_role: body_large\nstyle: {width: 100, height: 20, foreground: '#000000'}\n")
    return tmp_path


def test_the_app_binds_opens_shows_and_checks_a_view_written_in_the_new_syntax(tmp_path):
    root = project(tmp_path)
    class MainVM(DemoVM):
        views = ["main", "other"]

    app = App(root=root)
    app.bind(MainVM)
    opened = app.open_view("Main")
    assert isinstance(opened, ComposedView) and opened.node("root.banner").get("text") == "Hello"
    vm = opened.handle.viewmodel
    vm.title.set("Changed")
    assert opened.node("root.banner").get("text") == "Changed"
    window = app.show("main")
    assert window is app._window
    opened.window.advance(16)
    opened.window.simulate("click", node=opened.node("root.go"))
    assert vm.log == ["bump"]
    assert app.check() == ["MainVM serves the view 'other', but no view has that name"]


def test_the_app_reports_a_view_that_needs_a_name_its_viewmodel_lacks(tmp_path):
    root = project(tmp_path)
    (root / "Views" / "Main_View.yaml").write_text(
        "name: main\nwidget: Rect\nstyle: {width: 10, height: 10, background: '#6750A4'}\nhandlers: {on_click: nope_missing}\n")

    class Small(ViewModel):
        views = "main"

    app = App(root=root)
    app.bind(Small)
    app.open_view("Main")
    problems = app.check()
    assert len(problems) == 1 and "'nope_missing' is not a method of Small" in problems[0] and "Main_View.yaml:1:1" in problems[0].replace(str(root) + "/Views/", "")


def test_a_name_no_view_or_binding_serves_is_still_an_error_at_open(tmp_path):
    root = project(tmp_path)
    app = App(root=root)
    with pytest.raises(Exception, match="'title' is not defined"):
        app.open_view("Main")  # the view reads `title`, and no ViewModel is bound to give it


# -- rules the mutation check found no test for -----------------------------------------------------------------------------


def test_a_disabled_nodes_handlers_do_not_run():
    view, vm, _ = render(BASE + "  - widget: TextInput\n    name: f\n    disabled: '{{ not show_extra }}'\n    typography_role: body_large\n"
                         "    style: {width: 100, height: 30, background: '#FFFFFF'}\n    handlers: {on_click: bump}\n")
    view.window.advance(16)
    view.window.simulate("click", node=view.node("root.f"))
    assert vm.log == []
    vm.show_extra.set(True)  # enabled: the handler runs
    view.window.simulate("click", node=view.node("root.f"))
    assert vm.log == ["bump"]


def test_a_click_on_a_child_is_handled_there_and_does_not_also_run_the_parents_handler():
    view, vm, _ = render(BASE + "  - widget: Rect\n    name: outer\n    style: {width: 80, height: 40, background: '#6750A4'}\n    handlers: {on_click: 'log_outer()'}\n"
                         "    children:\n      - {widget: Rect, name: inner, style: {width: 30, height: 20, background: '#B3261E'}, handlers: {on_click: bump}}\n")
    vm.log_outer = lambda: vm.log.append("outer")
    view.window.advance(16)
    view.window.simulate("click", node=view.node("root.outer.inner"))
    assert vm.log == ["bump"]


def test_a_loop_variable_given_to_a_model_property_is_not_two_way():
    class Flags(ViewModel):
        views = "demo"

        def __init__(self):
            super().__init__()
            self.flags = Signal([True, False])

    view, vm, _ = render(BASE + "  - for: f in flags\n    key: f\n    widget: Checkbox\n    name: c\n    checked: '{{ f }}'\n"
                         "    style: {width: 24, height: 24, background: '#6750A4'}\n", vmcls=Flags)
    assert view.handle.node("c").models == {}
    view.window.advance(16)
    view.window.simulate("click", node=view.node("root.c[True]"))  # the control toggles; nothing is written back and nothing fails
    assert vm.flags.get() == [True, False]


def test_the_built_in_actions_exist_without_an_app_and_do_nothing_there():
    view, vm, _ = render(BASE + "  - {widget: Rect, name: w, style: {width: 40, height: 20, background: '#6750A4'}, handlers: {on_click: window.close}}\n"
                         "  - {widget: Rect, name: n, style: {width: 40, height: 20, background: '#6750A4'}, handlers: {on_click: navigate.back}}\n")
    view.window.advance(16)
    view.window.simulate("click", node=view.node("root.w"))
    view.window.simulate("click", node=view.node("root.n"))


def test_after_close_showing_and_hiding_the_view_no_longer_changes_its_nodes():
    view, vm, _ = render(BASE + "  - widget: Text\n    name: head\n    text: x\n    " + TEXT + "\n")
    view.close()
    view.handle.hide()
    assert view.root.get("visible") is True


def test_the_built_in_actions_resolve_for_a_view_and_nothing_else_does():
    from tesserae.composed import builtin_actions

    class Stub:
        window = None

        def node(self, name):
            return None

    resolve = builtin_actions(lambda: Stub())
    for path in ("window.close", "window.minimize", "navigate.back", "navigate.forward", "navigate.Settings", "navigate_to", "surface.dismiss"):
        assert callable(resolve(path)), path
    for path in ("window.bogus", "surface.explode", "navigate", "save", "window"):
        assert resolve(path) is None, path
    assert resolve("window.close")() is None and resolve("navigate.back")() is None and resolve("navigate_to")("Home") is None  # no App: nothing to do
