"""M39 Phase 1: a YAML node with an `on_click` handler is reachable from
the keyboard -- focusable, a Tab stop, activated by Enter and Space -- as
it was in `tre`'s `View` (whose `set_on_click` added a click action), and
exposed to assistive technology as a button (M39 Q1). M37 had dropped
this: `node.on("click")` alone doesn't make a node focusable.
"""

import pytest
import tre

import tesserae
from tesserae import View


def _rect(node_id, **extra):
    return {"id": node_id, "kind": "Rect", "style": {"width": 40, "height": 20, "background": "#112233"}, **extra}


def _spec(*children):
    return {"id": "root", "kind": "Container", "children": list(children)}


class VM(tesserae.ViewModel):
    def __init__(self, view):
        self.clicks = 0
        super().__init__(view)

    def go(self):
        self.clicks += 1


def _keyboard(view, window, node_id):
    vm = VM(view)
    window.advance(16)
    window.simulate("key_down", key="tab")
    window.advance(16)
    focused = view.node(node_id).get("focused")
    window.simulate("key_down", key="enter")
    window.simulate("key_down", key="space")
    window.simulate("key_up", key="space")
    return focused, vm.clicks


def test_a_clickable_node_is_reachable_by_keyboard_as_in_tre():
    spec = _spec(_rect("btn", handlers={"on_click": "go"}))
    tre_view = tre.View(spec=spec)
    tre_window = tre.Window.from_view(tre_view, width=200, height=100, title="t")
    theirs = _keyboard(tre_view, tre_window, "btn")
    view = View(spec)
    ours = _keyboard(view, view.window, "btn")
    assert theirs[0] is True and ours[0] is True  # Tab reaches it in both
    assert ours[1] == 2  # Enter and Space each click it
    assert theirs[1] >= 1  # tre: Enter at least


def test_a_clickable_node_is_a_button_unless_it_has_its_own_role():
    view = View(_spec(
        _rect("btn", handlers={"on_click": "go"}),
        _rect("plain"),
        {"id": "link", "kind": "Link", "text": {"content": "Go", "font_family": "Roboto", "font_size": 14},
         "style": {"foreground": "#000000", "width": 30, "height": 20}, "handlers": {"on_click": "go"}},
    ))
    VM(view)
    assert (view.node("btn").get("role"), view.node("btn").get("focusable")) == ("button", True)
    assert (view.node("plain").get("role"), view.node("plain").get("focusable")) == (None, False)
    assert view.node("link").get("role") == "link"


def test_tab_moves_through_clickable_nodes_in_order():
    view = View(_spec(_rect("a", handlers={"on_click": "go"}), _rect("skip"), _rect("b", handlers={"on_click": "go"})))
    VM(view)
    view.window.advance(16)
    order = []
    for _ in range(2):
        view.window.simulate("key_down", key="tab")
        order.append(next(i for i in ("a", "b", "skip") if view.node(i).get("focused")))
    assert order == ["a", "b"]


def test_adding_or_removing_on_click_by_reconcile_updates_it():
    view = View(_spec(_rect("x")))
    VM(view)
    view.reconcile(_spec(_rect("x", handlers={"on_click": "go"})))
    assert (view.node("x").get("role"), view.node("x").get("focusable")) == ("button", True)
    view.reconcile(_spec(_rect("x")))
    assert (view.node("x").get("role"), view.node("x").get("focusable")) == ("none", False)


def test_a_button_fragment_wrapped_as_a_clickable_is_reachable():
    """A `component:` call takes no `handlers:`, so an app makes a fragment
    clickable by wrapping it; the wrapper is the button."""
    from tesserae.spec import expand_components_to_spec

    spec = expand_components_to_spec(
        "id: root\nkind: Container\nchildren:\n  - id: save\n    kind: Container\n    handlers: {on_click: go}\n"
        "    children:\n      - id: face\n        component: ButtonFilled\n"
        '        with: {label: "Save", width: 120, height: 40, corner_radius: 20}\n'
    )
    view = View(spec, theme_seed=(0x67, 0x50, 0xA4, 0xFF))
    focused, clicks = _keyboard(view, view.window, "save")
    assert focused is True and clicks == 2


def test_a_yaml_link_takes_a_pointer_click():
    """M41: a Link was a bare `text`, which `tre` 0.3.4 never gives pointer
    events, so only the keyboard could follow it. It's a box holding its
    text now; the box takes the click, the focus and the role."""
    link = {"id": "more", "kind": "Link", "text": {"content": "More", "font_family": "Roboto", "font_size": 14},
            "style": {"foreground": "#0000FF"}, "handlers": {"on_click": "go"}}
    view = View(_spec(link))
    vm = VM(view)
    view.window.advance(16)
    node = view.node("more")
    assert (node.get("role"), node.get("label"), node.get("focusable")) == ("link", "More", True)
    x, y = node.get("layout_x"), node.get("layout_y")
    view.window.simulate("pointer_down", x=x + 5, y=y + 5)
    view.window.simulate("pointer_up", x=x + 5, y=y + 5)
    assert vm.clicks == 1
    node.focus()
    view.window.simulate("key_down", key="enter")
    assert vm.clicks == 2
    text = node.children()[0]
    assert text.get("text") == "More" and text.get("hit_testable") is False and text.get("a11y_hidden") is True
