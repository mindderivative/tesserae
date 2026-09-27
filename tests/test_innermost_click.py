"""M49 Phase 2: a click goes to the innermost clickable only (M49 Q1-Q3).

`tre`'s `click` and `secondary_click` bubble to every ancestor's
listener; each activation listener Tesserae adds -- YAML `on_click`,
`Widget.on_click`, controls, `SpinBox`, overlays, `Dock` tabs -- stops the
event after it runs (`tesserae.listeners.handled`), so a clickable inside
a clickable takes its click alone, as MD3 expects. A disabled control
still takes it (Q2).
"""

import pytest
import tre

import tesserae
from tesserae import View
from tesserae.docking import Dock
from tesserae.listeners import handled
from tesserae.widgets import card, checkbox, menu, popover, search_bar, search_view, spin_box


def _rect(node_id, width=200, height=80, **extra):
    return {"id": node_id, "kind": "Rect", "style": {"width": width, "height": height, "background": "#DDDDDD"},
            **extra}


class VM(tesserae.ViewModel):
    def __init__(self, view):
        self.clicks = []
        super().__init__(view)

    def outer(self):
        self.clicks.append("outer")

    def inner(self):
        self.clicks.append("inner")


def _nested():
    inner = _rect("inner", width=60, height=30, handlers={"on_click": "inner"})
    view = View({"id": "root", "kind": "Container",
                 "children": [_rect("outer", handlers={"on_click": "outer"}, children=[inner])]})
    vm = VM(view)
    view.window.advance(16)
    return view, vm, view.window


def _heard(window):
    """What reaches the top of the tree: a raw listener on the window's root."""
    heard = []
    window.root.on("click", lambda e: heard.append("click"))
    window.root.on("secondary_click", lambda e: heard.append("secondary_click"))
    return heard


def _press(window, node):
    x = node.get("layout_x") + node.get("layout_width") / 2
    y = node.get("layout_y") + node.get("layout_height") / 2
    window.simulate("pointer_down", x=x, y=y)
    window.simulate("pointer_up", x=x, y=y)
    window.advance(16)


def test_a_pointer_click_on_a_nested_clickable_goes_to_it_alone():
    view, vm, window = _nested()
    heard = _heard(window)
    _press(window, view.node("inner"))
    assert vm.clicks == ["inner"] and heard == []
    window.simulate("pointer_down", x=150, y=60)  # the outer one, outside the inner
    window.simulate("pointer_up", x=150, y=60)
    assert vm.clicks == ["inner", "outer"] and heard == []


def test_keyboard_and_simulated_clicks_go_to_the_innermost_too():
    view, vm, window = _nested()
    view.node("inner").focus()
    window.simulate("key_down", key="enter")
    assert vm.clicks == ["inner"]
    view.click(view.node("inner"))
    assert vm.clicks == ["inner", "inner"]


def test_a_click_on_a_plain_child_still_reaches_its_clickable_parent():
    """Only a clickable stops the click: a Text or Rect with no handler
    inside a clickable lets it through, as before."""
    label = {"id": "label", "kind": "Text", "text": {"content": "Open", "typography_role": "label_large"}, "style": {"foreground": "#000000"}}
    view = View({"id": "root", "kind": "Container",
                 "children": [_rect("outer", handlers={"on_click": "outer"}, children=[label, _rect("deco", 40, 20)])]})
    vm = VM(view)
    window = view.window
    window.advance(16)
    view.click(view.node("label"))
    _press(window, view.node("deco"))
    assert vm.clicks == ["outer", "outer"]


def test_a_control_in_a_clickable_card_takes_its_click_even_when_disabled():
    window = tre.Window(width=600, height=400)
    opened = []
    c = card(window, 300, 200, on_click=lambda: opened.append("card"))
    box = checkbox(window, (0x67, 0x50, 0xA4, 0xFF), 48, 48)
    box.node.remove()
    c.node.add_child(box.node)
    window.advance(16)
    _press(window, box.node)
    assert box.checked.get() is True and opened == []
    box.disabled.set(True)
    window.advance(16)
    _press(window, box.node)
    assert box.checked.get() is True and opened == []  # nothing fires, and the card doesn't open (Q2)
    window.simulate("click", node=c.node)
    assert opened == ["card"]


def test_widget_on_click_spin_box_and_menu_items_take_their_clicks():
    window = tre.Window(width=600, height=400)
    heard = _heard(window)
    chosen = []
    c = card(window, 200, 100, on_click=lambda: chosen.append("card"))
    window.simulate("click", node=c.node)
    spin = spin_box(window, value=1)
    window.advance(16)
    window.simulate("click", node=spin.increment)
    m = menu(window, [("Rename", lambda: chosen.append("rename"))])
    m.open_at(10, 10)
    window.advance(16)
    surface = []  # a menu sits on an overlay layer, not under the root: listen on its own surface
    m.widget.view._listen(m.node, "click", lambda e: surface.append("click"))
    window.simulate("click", node=m.items[0])
    assert chosen == ["card", "rename"] and spin.value.get() == 2
    assert heard == [] and surface == []


def test_a_right_click_opens_only_the_innermost_context_menu():
    view, vm, window = _nested()
    heard = _heard(window)
    outer_menu, inner_menu = menu(window, [("Outer", None)]), menu(window, [("Inner", None)])
    outer_menu.attach_context(view.node("outer"))
    inner_menu.attach_context(view.node("inner"))
    inner = view.node("inner")
    window.simulate("secondary_click", x=inner.get("layout_x") + 5, y=inner.get("layout_y") + 5)
    window.advance(16)
    assert inner_menu.is_open and not outer_menu.is_open and heard == []


def test_dock_tabs_take_their_clicks_and_right_clicks():
    window = tre.Window(width=900, height=500)
    window.root.set(padding_top=0, padding_right=0, padding_bottom=0, padding_left=0, gap=0, align_items="stretch")
    heard = _heard(window)
    dock = Dock(window)
    window.root.add_child(dock.add_zone("left", 300))
    window.root.add_child(dock.add_zone("right", 300))
    files, search = window.create("box", width=10, height=10), window.create("box", width=10, height=10)
    dock.add_panel("left", files, "Files")
    dock.add_panel("left", search, "Search")
    window.advance(16)
    tab = dock._zones["left"].tabs[1].node
    window.simulate("click", node=tab)
    assert dock.shown("left") == search
    window.simulate("secondary_click", x=tab.get("layout_x") + 5, y=tab.get("layout_y") + 5)
    assert dock._menu.is_open and heard == []


def test_a_popover_anchor_and_a_search_result_take_their_clicks():
    window = tre.Window(width=600, height=500)
    window.root.set(padding_top=0, padding_right=0, padding_bottom=0, padding_left=0, gap=0,
                    align_items="flex_start", flex_direction="vertical")
    heard = _heard(window)
    anchor = window.create("box", width=100, height=40, focusable=True, role="button")
    window.root.add_child(anchor)
    p = popover(window, "Details", anchor=anchor)
    window.simulate("click", node=anchor)
    assert p.is_open and heard == []
    p.close()
    chosen = []
    bar = search_bar(window, "Search mail", 360)
    view = search_view(window, 360, 300, bar=bar, results=[("Alice", lambda: chosen.append("alice"))])
    bar.part("field").focus()
    window.advance(16)
    surface = []  # on an overlay layer, like a menu
    view.widget.view._listen(view.node, "click", lambda e: surface.append("click"))
    window.simulate("click", node=view.rows[0])
    assert chosen == ["alice"] and heard == [] and surface == []


def test_handled_stops_the_event_even_if_the_handler_raises():
    stopped = []

    class Event:
        def stop(self):
            stopped.append(True)

    def boom(event):
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        handled(boom)(Event())
    assert stopped == [True]
    handled(lambda e: None)(object())  # an event with no stop() is fine
