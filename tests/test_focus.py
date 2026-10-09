"""#213: focus control and keyboard navigation -- `focus(name)`, `on_press`, and `focus_group` (roving tab stops, arrows, Home/End, type-ahead)."""

import pytest

from tesserae import App, Signal, ViewModel
from tesserae.composed import open_composed
from tesserae.spec.nodes import LoadError, parse_view
from tesserae.viewmodel import Bindings, check_view

SEED = (103, 80, 164, 255)
BOX = "style: {width: 60, height: 30, background: '#6750A4'}"


class VM(ViewModel):
    views = "v"

    def __init__(self):
        super().__init__()
        self.a = Signal("")
        self.b = Signal("")
        self.log = []

    def noop(self):
        self.log.append("noop")


def render(source, vm=VM, views=None, library=None):
    bindings = Bindings()
    bindings.bind(vm)
    doc = parse_view(source, "V_View.yaml", resolver=(library.decl if library else None))
    view = open_composed(doc, bindings, library.doc if library else None, theme_seed=SEED)
    view.window.advance(16)
    return view, view.handle.viewmodel


def watch(view, *ids):
    """Records, in a list, the ids of the nodes that get the focus."""
    seen = []
    for node_id in ids:
        node = view._focus_node(view.handle.composition.find(node_id))
        view._listen(node, "focus", lambda event, node_id=node_id: seen.append(node_id))
    return seen


def key(view, name):
    view.window.simulate("key_down", key=name)
    view.window.advance(16)


FIELD = "style: {width: 100, height: 30, background: '#FFFFFF'}\n    typography_role: body_large\n"


# -- focus(name) -----------------------------------------------------------------------------------------------------------


def test_focus_gives_a_named_node_the_focus_so_typing_goes_to_it():
    view, vm = render("name: v\nwidget: Container\nstyle: {flex_direction: vertical, width: 300, height: 300}\nchildren:\n"
                      f"  - {{widget: Rect, name: go, {BOX}, handlers: {{on_click: \"focus('second')\"}}}}\n"
                      "  - widget: TextInput\n    name: first\n    text: '{{ a }}'\n    " + FIELD +
                      "  - widget: TextInput\n    name: second\n    text: '{{ b }}'\n    " + FIELD)
    view.window.simulate("click", node=view.node("root.go"))
    view.window.simulate("input", text="hi")
    assert vm.b.get() == "hi" and vm.a.get() == ""


def test_focus_names_a_node_in_the_view_the_handler_was_written_in():
    pair = ("params:\n  text: {type: str, default: '', model: true}\nwidget: Container\nstyle: {flex_direction: vertical}\nchildren:\n"
            f"  - {{widget: Rect, name: go, {BOX}, handlers: {{on_click: \"focus('input')\"}}}}\n"
            "  - widget: TextInput\n    name: input\n    text: '{{ text }}'\n    " + FIELD)
    from tesserae.shipped import ViewLibrary
    import tempfile, pathlib
    folder = pathlib.Path(tempfile.mkdtemp())
    (folder / "Pair_View.yaml").write_text(pair)
    library = ViewLibrary({"Pair": folder / "Pair_View.yaml"})
    view, vm = render("name: v\nwidget: Container\nstyle: {flex_direction: vertical, width: 300, height: 300}\nchildren:\n"
                      "  - widget: TextInput\n    name: input\n    text: '{{ a }}'\n    " + FIELD +
                      "  - widget: Pair\n    name: p\n    text: '{{ b }}'\n", library=library)
    view.window.simulate("click", node=view.node("root.p.go"))
    view.window.simulate("input", text="in the pair")
    assert vm.b.get() == "in the pair" and vm.a.get() == ""  # the callee's `input`, not the caller's


def test_focus_on_a_name_that_is_not_there_says_so():
    view, _ = render(f"name: v\nwidget: Rect\n{BOX}\nhandlers: {{on_click: \"focus('nope')\"}}\n")
    with pytest.raises(ValueError, match=r"focus\('nope'\): no node by that name in this view"):
        view.handle.composition.root.fire("on_click")


def test_a_press_on_a_container_focuses_what_it_names_without_making_it_a_button():
    view, vm = render("name: v\nwidget: Container\nstyle: {flex_direction: vertical, width: 300, height: 300}\nchildren:\n"
                      "  - widget: Container\n    name: frame\n    style: {width: 200, height: 60, padding: 20, background: '#EEEEEE'}\n"
                      "    handlers: {on_press: \"focus('field')\"}\n    children:\n"
                      "      - widget: TextInput\n        name: field\n        text: '{{ a }}'\n        " + FIELD.replace("\n    ", "\n        "))
    frame = view.node("root.frame")
    assert frame.get("role") != "button" and not frame.get("focusable")
    view.window.simulate("pointer_down", x=6, y=6)  # on the frame's padding, not on the input
    view.window.simulate("pointer_up", x=6, y=6)
    view.window.simulate("input", text="typed")
    assert vm.a.get() == "typed"


def test_a_click_on_a_text_fields_padding_focuses_its_input(tmp_path):
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text("name: main\nwidget: Container\nstyle: {flex_direction: vertical, width: 400, height: 300, padding: 16}\n"
                                                         "children:\n  - {widget: TextField, name: f, label: Name, text: '{{ name }}'}\n")

    class Main(ViewModel):
        views = "main"

        def __init__(self):
            super().__init__()
            self.name = Signal("")

    app = App(root=tmp_path)
    app.bind(Main)
    view = app.open_view("Main")
    app.show("main")
    view.window.advance(16)
    view.window.simulate("pointer_down", x=30, y=20)  # inside the field's box, left of the input
    view.window.simulate("pointer_up", x=30, y=20)
    view.window.simulate("input", text="Ada")
    assert view.handle.viewmodel.name.get() == "Ada"


# -- focus_group -----------------------------------------------------------------------------------------------------------


def group(mode, labels=("one", "two", "three", "four"), extra=""):
    items = "".join(f"      - {{widget: Rect, name: i{n}, {BOX}, handlers: {{on_click: noop}}, a11y: {{label: {label}}}}}\n" for n, label in enumerate(labels))
    return ("name: v\nwidget: Container\nstyle: {flex_direction: horizontal, width: 400, height: 100}\nchildren:\n"
            f"  - widget: Container\n    name: g\n    focus_group: {mode}\n    style: {{flex_direction: horizontal, gap: 4}}\n    children:\n{items}{extra}")


def ids(n):
    return [f"root.g.i{i}" for i in range(n)]


def tab_stops(view, n=4):
    return [view.node(i).get("tab_index") for i in ids(n)]


def test_a_group_has_one_tab_stop_and_the_arrow_keys_move_it_along_the_axis():
    view, _ = render(group("horizontal"))
    assert tab_stops(view) == [0, -1, -1, -1]
    seen = watch(view, *ids(4))
    view.node(ids(4)[0]).focus()
    key(view, "arrow_right")
    key(view, "arrow_right")
    assert seen == ["root.g.i0", "root.g.i1", "root.g.i2"] and tab_stops(view) == [-1, -1, 0, -1]
    key(view, "arrow_left")
    assert seen[-1] == "root.g.i1" and tab_stops(view) == [-1, 0, -1, -1]
    count = len(seen)
    key(view, "arrow_down")  # not this group's axis
    key(view, "arrow_up")
    assert len(seen) == count and tab_stops(view) == [-1, 0, -1, -1]


def test_the_arrows_wrap_and_home_and_end_go_to_the_ends():
    view, _ = render(group("both"))
    seen = watch(view, *ids(4))
    view.node(ids(4)[0]).focus()
    key(view, "arrow_left")
    assert seen[-1] == "root.g.i3"
    key(view, "arrow_down")
    assert seen[-1] == "root.g.i0"
    key(view, "arrow_up")
    assert seen[-1] == "root.g.i3"
    key(view, "Home")
    assert seen[-1] == "root.g.i0"
    key(view, "End")
    assert seen[-1] == "root.g.i3" and tab_stops(view) == [-1, -1, -1, 0]


def test_a_vertical_group_uses_up_and_down_only():
    view, _ = render(group("vertical"))
    seen = watch(view, *ids(4))
    view.node(ids(4)[1]).focus()
    key(view, "arrow_right")
    key(view, "arrow_down")
    assert seen == ["root.g.i1", "root.g.i2"]


def test_focusing_an_item_any_way_moves_the_tab_stop_to_it():
    view, _ = render(group("horizontal"))
    view.node(ids(4)[2]).focus()
    view.window.advance(16)
    assert tab_stops(view) == [-1, -1, 0, -1]


def test_the_tab_stop_survives_a_change_to_the_view():
    view, vm = render(group("horizontal", extra="      - {widget: Rect, name: late, " + BOX + ", handlers: {on_click: noop}, if: show}\n").replace(
        "class VM", "class VM"), vm=type("V2", (VM,), {"views": "v", "__init__": lambda self: (VM.__init__(self), setattr(self, "show", Signal(False)))[0]}))
    view.node(ids(4)[1]).focus()
    view.window.advance(16)
    vm.show.set(True)
    assert tab_stops(view) == [-1, 0, -1, -1]
    assert view.node("root.g.late").get("tab_index") == -1


def test_a_disabled_item_is_skipped():
    items = ("  - widget: Container\n    name: g\n    focus_group: horizontal\n    style: {flex_direction: horizontal, gap: 4}\n    children:\n"
             f"      - {{widget: TextInput, name: a, style: {{width: 60, height: 30, background: '#FFFFFF'}}, typography_role: body_large}}\n"
             f"      - {{widget: TextInput, name: b, disabled: true, style: {{width: 60, height: 30, background: '#FFFFFF'}}, typography_role: body_large}}\n"
             f"      - {{widget: TextInput, name: c, style: {{width: 60, height: 30, background: '#FFFFFF'}}, typography_role: body_large}}\n")
    view, _ = render("name: v\nwidget: Container\nstyle: {width: 400, height: 100}\nchildren:\n" + items)
    seen = watch(view, "root.g.a", "root.g.b", "root.g.c")
    view.node("root.g.a").focus()
    key(view, "arrow_right")
    assert seen == ["root.g.a", "root.g.c"]


def test_typing_the_start_of_a_name_jumps_to_it_and_a_pause_starts_over(monkeypatch):
    import tesserae.composed as composed

    view, _ = render(group("vertical", labels=("Apple", "Banana", "Blueberry", "Cherry")))
    seen = watch(view, *ids(4))
    view.node(ids(4)[0]).focus()
    key(view, "b")
    assert seen[-1] == "root.g.i1"
    key(view, "l")  # "bl" -> Blueberry
    assert seen[-1] == "root.g.i2"
    monkeypatch.setattr(composed, "TYPEAHEAD_RESET", 0.0)  # a pause: the next letter starts a new search
    key(view, "c")
    assert seen[-1] == "root.g.i3"
    monkeypatch.setattr(composed, "TYPEAHEAD_RESET", 60.0)
    key(view, "z")
    assert seen[-1] == "root.g.i3"  # nothing starts with it: the focus stays


def test_the_same_letter_again_goes_on_to_the_next_item_that_starts_with_it():
    view, _ = render(group("vertical", labels=("Bat", "Bear", "Cow", "Bee")))
    seen = watch(view, *ids(4))
    view.node(ids(4)[0]).focus()
    for _ in range(3):
        key(view, "b")
    assert seen[1:] == ["root.g.i1", "root.g.i3"]


def test_typing_in_a_text_item_is_not_taken_for_a_search():
    items = ("  - widget: Container\n    name: g\n    focus_group: horizontal\n    style: {flex_direction: horizontal, gap: 4}\n    children:\n"
             "      - {widget: TextInput, name: a, text: '{{ a }}', style: {width: 80, height: 30, background: '#FFFFFF'}, typography_role: body_large}\n"
             "      - {widget: Rect, name: bee, style: {width: 60, height: 30, background: '#6750A4'}, handlers: {on_click: noop}, a11y: {label: Bee}}\n")
    view, vm = render("name: v\nwidget: Container\nstyle: {width: 400, height: 100}\nchildren:\n" + items)
    seen = watch(view, "root.g.a", "root.g.bee")
    view.node("root.g.a").focus()
    key(view, "b")
    assert seen == ["root.g.a"]


def test_a_group_inside_a_group_looks_after_its_own_items():
    inner = ("      - widget: Container\n        name: inner\n        focus_group: vertical\n        style: {flex_direction: vertical}\n        children:\n"
             f"          - {{widget: Rect, name: x, {BOX}, handlers: {{on_click: noop}}}}\n          - {{widget: Rect, name: y, {BOX}, handlers: {{on_click: noop}}}}\n")
    view, _ = render(group("horizontal", labels=("a", "b"), extra=inner))
    assert [view.node(f"root.g.i{i}").get("tab_index") for i in range(2)] == [0, -1]
    assert view.node("root.g.inner.x").get("tab_index") == 0 and view.node("root.g.inner.y").get("tab_index") == -1
    seen = watch(view, "root.g.i0", "root.g.i1", "root.g.inner.x", "root.g.inner.y")
    view.node("root.g.inner.x").focus()
    key(view, "arrow_down")
    assert seen == ["root.g.inner.x", "root.g.inner.y"]
    view.node("root.g.i1").focus()
    key(view, "arrow_right")  # the outer group wraps among its own items, never into the inner group's
    assert seen[-2:] == ["root.g.i1", "root.g.i0"]


# -- the language ----------------------------------------------------------------------------------------------------------


def test_focus_group_is_checked_and_focus_is_a_known_action():
    with pytest.raises(LoadError, match="'focus_group:' is one of horizontal, vertical, both") as caught:
        parse_view("widget: Container\nfocus_group: horizontl\n", "T_View.yaml")
    assert "did you mean 'horizontal'" in str(caught.value)
    doc = parse_view("name: v\nwidget: Rect\nhandlers: {on_click: \"focus('x')\", on_press: \"focus('x')\"}\n", "T_View.yaml")
    assert check_view(doc, VM()) == []


def test_the_widget_schema_knows_focus_group():
    import jsonschema

    from tesserae.spec import widgets

    validator = jsonschema.Draft7Validator(widgets.json_schema())
    assert not list(validator.iter_errors({"widget": "Container", "focus_group": "both", "children": []}))
    assert list(validator.iter_errors({"widget": "Container", "focus_group": "sideways"}))
    with pytest.raises(ValueError, match="'focus_group'"):
        widgets.declare("Clash", {"focus_group": widgets.Property("str")})
