"""M71 (#21): `kind: ScrollView`, `tre`'s `scroll_view` holding one content
box its children lay out in (vertical unless the style says otherwise).
Since `tre` 0.4.2 (`tre` #24, M73) `tre` scrolls it with the keys around
the focused node, reveals a focused child and answers `scroll_into_view`;
Tesserae's `Scroller` follows its `scroll` event for `two_way:
scroll_offset`. These check the outcomes, whoever does the scrolling.
"""

import pytest

from tesserae import Signal, Theme, View, ViewModel

LINE = 40.0  # an arrow key's scroll (tre's)

SEED = (0x67, 0x50, 0xA4, 0xFF)


def _rows(n=10, **extra):
    return [{"id": f"r{i}", "kind": "Rect", "style": {"height": 40, "background": "#6750A4"},
             "handlers": {"on_click": "noop"}, **extra} for i in range(n)]


def _spec(style=None, children=None, **node):
    scroll = {"id": "list", "kind": "ScrollView", "style": {"width": 200, "height": 100, **(style or {})},
              "children": children if children is not None else _rows(), **node}
    return {"id": "root", "kind": "Container", "style": {"width": 300, "height": 300}, "children": [scroll]}


class VM(ViewModel):
    def __init__(self, view):
        self.pos = Signal(0.0)
        super().__init__(view)

    def noop(self):
        pass


def _view(spec=None, vm=True):
    view = View(spec or _spec(), theme_seed=SEED)
    model = VM(view) if vm else None
    view.window.advance(16)
    return view, model, view._built.outer["list"]


def test_it_is_a_scroll_view_holding_a_content_box():
    view, _, scroll = _view(_spec({"gap": 4, "padding": 8}))
    content = view.node("list")
    assert scroll.get("kind") == "scroll_view" and content.get("kind") == "box" and content.parent() == scroll
    assert [view.node(f"r{i}").parent() == content for i in range(3)] == [True] * 3
    assert [view.node(f"r{i}").get("layout_y") for i in range(3)] == [8.0, 52.0, 96.0]  # vertical, gap, padding
    assert content.get("layout_height") == 8 + 10 * 40 + 9 * 4 + 8 and content.get("layout_width") == 200.0
    assert scroll.get("focusable") and scroll.get("scrollbar_fill") == Theme.resolve(theme_seed=SEED).role("outline")


def test_a_horizontal_content_and_paint_on_the_scroll_view():
    view, _, scroll = _view(_spec({"flex_direction": "horizontal", "background": "surface", "corner_radius": 12},
                                  children=_rows(3)))
    assert view.node("r1").get("layout_y") == view.node("r0").get("layout_y")
    assert scroll.get("fill") == Theme.resolve(theme_seed=SEED).role("surface") and scroll.get("corner_radius") == 12.0


def test_the_wheel_scrolls_and_two_way_hears_it():
    view, vm, scroll = _view(_spec(bindings={"scroll_offset": "{{ pos.get() }}"}, two_way="scroll_offset"))
    view.window.simulate("wheel", node=view.node("r0"), delta_y=50.0)
    assert scroll.get("scroll_offset") == 50.0 and vm.pos.get() == 50.0
    vm.pos.set(120.0)  # and the binding scrolls it
    assert scroll.get("scroll_offset") == 120.0


@pytest.mark.parametrize("keys, offset", [
    (["arrow_down"], LINE), (["arrow_down", "arrow_down", "arrow_up"], LINE), (["page_down"], 100.0),
    (["page_down", "page_down", "page_up"], 100.0), (["end"], 300.0), (["end", "home"], 0.0),
    (["arrow_up"], 0.0), (["end", "arrow_down", "page_down"], 300.0),  # kept within the content
])
def test_the_keys_scroll_it_when_it_has_focus(keys, offset, capfd):
    view, vm, scroll = _view(_spec(bindings={"scroll_offset": "{{ pos.get() }}"}, two_way="scroll_offset"))
    scroll.focus()
    for key in keys:
        view.window.simulate("key_down", key=key)
        view.window.advance(16)  # tre clamps a far offset at its next layout
    assert scroll.get("scroll_offset") == offset and vm.pos.get() == offset  # what it reports is where it stops
    assert "uncaught exception" not in capfd.readouterr().err  # never a negative offset (tre refuses one)


def test_a_focused_childs_keys_scroll_it_but_a_text_field_keeps_its_arrows():  # tre 0.4.2 (M73)
    field = {"id": "field", "kind": "TextField", "text": {"content": "", "font_family": "Roboto", "font_size": 14},
             "style": {"height": 32, "foreground": "#000000", "background": "#FFFFFF"}}
    view, vm, scroll = _view(_spec(children=[*_rows(), field],
                                   bindings={"scroll_offset": "{{ pos.get() }}"}, two_way="scroll_offset"))
    view.node("r0").focus()
    view.window.simulate("key_down", key="page_down")  # the Scroller mustn't keep it from tre (it did, before M73)
    assert scroll.get("scroll_offset") == 100.0 and vm.pos.get() == 100.0
    view.node("field").focus()  # revealed at the bottom
    at = scroll.get("scroll_offset")
    view.window.simulate("key_down", key="arrow_up")  # the text field's own
    assert scroll.get("scroll_offset") == at


def test_a_focused_child_is_scrolled_into_view_and_only_as_far_as_needed():
    view, vm, scroll = _view(_spec(bindings={"scroll_offset": "{{ pos.get() }}"}, two_way="scroll_offset"))
    view.node("r5").focus()  # top 200: shown at the bottom
    assert scroll.get("scroll_offset") == 140.0 and vm.pos.get() == 140.0
    view.node("r4").focus()  # already in view: nothing moves
    assert scroll.get("scroll_offset") == 140.0
    view.node("r1").focus()  # above: shown at the top
    assert scroll.get("scroll_offset") == 40.0


def test_scroll_into_view_is_answered():
    view, _, scroll = _view()
    view.window.simulate("a11y_action", node=view.node("r9"), action="scroll_into_view")
    assert scroll.get("scroll_offset") == 300.0
    scroll.set(scroll_offset=0.0)
    view.window.simulate("a11y_action", node=view.node("r9"), action="increment")  # another action: nothing
    assert scroll.get("scroll_offset") == 0.0


def test_focusing_the_scroll_view_itself_moves_nothing():
    view, _, scroll = _view()
    scroll.set(scroll_offset=100.0)
    view.window.advance(16)
    scroll.focus()
    view.window.simulate("a11y_action", node=scroll, action="scroll_into_view")
    assert scroll.get("scroll_offset") == 100.0


def test_on_scroll_hears_each_change_until_undone():
    view, _, scroll = _view(vm=False)
    scroller, heard = view._scrollers["list"], []
    undo = scroller.on_scroll(heard.append)
    scroll.set(scroll_offset=0.0)  # already there: no change
    scroll.set(scroll_offset=60.0)
    view.window.simulate("wheel", node=view.node("r3"), delta_y=20.0)
    assert heard == [60.0, 80.0] and scroller.offset == 80.0
    undo()
    scroll.set(scroll_offset=0.0)
    assert heard == [60.0, 80.0]


def test_a_nested_scroll_view_reveals_through_both():
    inner = {"id": "inner", "kind": "ScrollView", "style": {"width": 180, "height": 80},
             "children": [{**r, "id": f"i{n}"} for n, r in enumerate(_rows(6))]}
    view, _, outer = _view(_spec(children=[*_rows(3), inner]))
    inner_node = view._built.outer["inner"]
    view.node("i5").focus()  # inner content top 200, its viewport 80: inner scrolls 160
    assert inner_node.get("scroll_offset") == 160.0
    # the outer then shows the child where the inner scrolled it: 120 + (200 - 160) + 40 - 100
    assert outer.get("scroll_offset") == 100.0


def test_it_scrolls_without_a_viewmodel_and_survives_a_re_theme_and_reconcile():
    view, _, scroll = _view(vm=False)
    scroll.focus()
    view.window.simulate("key_down", key="page_down")
    view.set_theme(theme_seed=SEED, dark=True)
    assert scroll.get("scroll_offset") == 100.0
    assert scroll.get("scrollbar_fill") == Theme.resolve(theme_seed=SEED, dark=True).role("outline")
    view.reconcile(_spec({"gap": 2}, children=_rows(12)))
    view.window.advance(16)
    assert view._built.outer["list"] == scroll and scroll.get("scroll_offset") == 100.0
    assert view.node("r11").parent() == view.node("list")  # a new child goes in the content box
    view.window.simulate("key_down", key="end")
    assert scroll.get("scroll_offset") == 12 * 40 + 11 * 2 - 100


def test_a_rebuilt_scroll_view_gets_a_new_scroller_and_the_old_one_stops():
    view, _, scroll = _view()
    old = view._scrollers["list"]
    view.reconcile({"id": "root", "kind": "Container", "style": {"width": 300, "height": 300},
                    "children": [{"id": "list", "kind": "Container", "style": {"width": 10}}]})
    assert "list" not in view._scrollers and old._followers == []
    view.reconcile(_spec())
    assert view._scrollers["list"] is not old and view._scrollers["list"].node == view._built.outer["list"]


def test_a_whole_rebuild_gives_the_new_node_its_scroller():
    view, _, _ = _view(vm=False)
    spec = _spec()
    view.reconcile({**spec, "id": "root2"})  # a new root id rebuilds everything, the ScrollView kept its id
    scroll = view._built.outer["list"]
    assert view._scrollers["list"].node == scroll
    scroll.focus()
    view.window.simulate("key_down", key="page_down")
    assert scroll.get("scroll_offset") == 100.0


def test_a_style_dropping_flex_wrap_resets_the_content():
    view, _, _ = _view(_spec({"flex_wrap": "wrap"}))
    assert view.node("list").get("flex_wrap") == "wrap"
    view.reconcile(_spec())
    assert view.node("list").get("flex_wrap") == "no_wrap"


def test_padding_and_gap_bind_on_the_content_and_the_rest_on_the_scroll_view():
    class Sizes(ViewModel):
        def __init__(self, view):
            self.gap, self.w = Signal(6), Signal(150)
            super().__init__(view)

        def noop(self):
            pass

    view = View(_spec(bindings={"gap": "{{ gap.get() }}", "width": "{{ w.get() }}"}), theme_seed=SEED)
    Sizes(view)
    assert view.node("list").get("gap") == 6.0 and view._built.outer["list"].get("width") == 150.0


def test_two_way_on_anything_but_scroll_offset_is_refused():
    view = View(_spec(bindings={"width": "{{ pos.get() }}"}, two_way="width"), theme_seed=SEED)
    with pytest.raises(ValueError, match='a ScrollView\'s only user-editable property is "scroll_offset"'):
        VM(view)


def test_a_detached_scroller_hears_nothing_more():
    view, _, scroll = _view(vm=False)
    scroller, heard = view._scrollers["list"], []
    scroller.on_scroll(heard.append)
    scroll.set(scroll_offset=40.0)
    scroller.detach()
    scroll.set(scroll_offset=80.0)
    assert heard == [40.0]
    assert scroller._followers == []  # and it lets them go
    assert not [key for key in view._events._slots if key[1] == "scroll"]  # its listener is off the node


def test_an_offset_past_the_end_is_held_at_the_end_and_written_back():  # tre 0.4.3 (M79)
    view, vm, scroll = _view(_spec(bindings={"scroll_offset": "{{ pos.get() }}"}, two_way="scroll_offset"))
    view.window.advance(16)
    vm.pos.set(9999.0)  # no frame needed: tre clamps it as it's set, with one `scroll` event
    assert scroll.get("scroll_offset") == 300.0 and vm.pos.get() == 300.0


def test_a_nested_scroll_view_keeps_the_wheel_even_when_its_content_fits():  # tre 0.4.3 (M79)
    """`tre` 0.4.3 hands a wheel on past a scroll view that doesn't scroll
    in its direction; every `ScrollView` is vertical, so an inner one keeps
    a vertical wheel, room or not (no browser-style chaining)."""
    row = {"id": "only", "kind": "Rect", "style": {"height": 40, "background": "#6750A4"}}
    inner = {"id": "inner", "kind": "ScrollView", "style": {"height": 40}, "children": [row]}
    view, vm, scroll = _view(_spec(children=[inner, *_rows()]))
    view.window.simulate("wheel", node=view.node("only"), delta_y=50.0)  # inner's content fits it
    assert view._built.outer["inner"].get("scroll_offset") == 0.0 and scroll.get("scroll_offset") == 0.0


@pytest.mark.parametrize("modifier, scrolls", [("ctrl", False), ("alt", False), ("meta", False), ("shift", True)])
def test_a_shortcut_does_not_scroll_but_shift_does(modifier, scrolls):  # tre 0.4.3 (M79)
    view, vm, scroll = _view(_spec(bindings={"scroll_offset": "{{ pos.get() }}"}, two_way="scroll_offset"))
    scroll.focus()
    view.window.simulate("key_down", key="page_down", **{modifier: True})
    assert scroll.get("scroll_offset") == (100.0 if scrolls else 0.0) and vm.pos.get() == scroll.get("scroll_offset")
