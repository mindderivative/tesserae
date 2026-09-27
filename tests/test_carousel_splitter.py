"""M42 Phase 6: `carousel` and `splitter`, new by Q1 (`tre` had them as
`add_carousel`/`add_splitter`, never wrapped), following `tre`'s
`legacy-behavior.md` (0.3.5). Driven headlessly with `simulate`/`advance`.
"""

import math

import pytest
import tre

from tesserae import Theme, tokens
from tesserae.widgets import carousel, splitter
from tesserae.widgets.containment import (CAROUSEL_GAP, CAROUSEL_INSET, CAROUSEL_PADDING, MEDIUM, MOVE_MS, SMALL,
                                          SPLIT_STEP, UNCONTAINED_WIDTH, carousel_layout)

BASE = tokens.baseline_scheme()


def _window():
    window = tre.Window(width=600, height=500)
    window.root.set(padding_top=0, padding_right=0, padding_bottom=0, padding_left=0, gap=0,
                    align_items="flex_start")
    return window


def _frames(window, ms):
    for _ in range(math.ceil(ms / 16) + 1):
        window.advance(16)


def _boxes(window, count, width=None):
    return [window.create("box", width=width, height=40) if width else window.create("box", height=40)
            for _ in range(count)]


def _spans(c):
    return [(s.get("layout_x"), s.get("layout_width")) for s in c.slots]


# -- carousel ------------------------------------------------------------------------

def test_a_multi_browse_carousel_lays_out_large_medium_small():
    window = _window()
    c = carousel(window, 400, 200, items=_boxes(window, 5))
    window.advance(16)
    large = 400 - 2 * CAROUSEL_PADDING - MEDIUM - SMALL - 2 * CAROUSEL_GAP  # 184
    assert _spans(c) == [(16.0, large), (208.0, MEDIUM), (328.0, SMALL), (392.0, SMALL), (456.0, SMALL)]
    slot = c.slots[0]
    assert (slot.get("layout_y"), slot.get("layout_height")) == (CAROUSEL_INSET, 200 - 2 * CAROUSEL_INSET)
    assert slot.get("clip_children") and slot.get("corner_radius") == 28.0
    assert slot.get("fill") == BASE["surface_container_highest"]
    assert c.node.get("clip_children") and c.node.get("role") == "group" and c.node.get("label") == "Carousel"


def test_a_hero_carousel_is_large_then_small():
    window = _window()
    c = carousel(window, 400, 200, layout="hero", items=_boxes(window, 3))
    window.advance(16)
    large = 400 - 2 * CAROUSEL_PADDING - SMALL - CAROUSEL_GAP  # 304
    assert _spans(c) == [(16.0, large), (16.0 + large + 8, SMALL), (16.0 + large + 8 + SMALL + 8, SMALL)]


def test_moving_blends_the_widths_and_settles_on_the_index_in_300ms():
    window = _window()
    c = carousel(window, 400, 200, items=_boxes(window, 5))
    window.advance(16)
    c.index.set(1)
    window.advance(16)
    window.advance(16)
    middle = c.position()
    assert 0.0 < middle < 1.0  # on its way, eased
    window.advance(16)
    expected = carousel_layout("multi_browse", 400, 5, c.position(), [])
    assert [s.get("width") for s in c.slots] == pytest.approx([w for _, w in expected], abs=0.01)
    assert c.position() > middle
    _frames(window, MOVE_MS)
    assert c.position() == 1.0
    # the new current item starts at the left padding; items before it are small
    assert _spans(c)[:3] == [(16.0 - SMALL - CAROUSEL_GAP, SMALL), (16.0, 184.0), (208.0, MEDIUM)]


def test_the_wheel_drag_and_arrows_move_a_snapping_carousel():
    window = _window()
    c = carousel(window, 400, 200, items=_boxes(window, 6))
    heard = []
    c.on_change(heard.append)
    window.advance(16)
    window.simulate("wheel", x=100, y=100, delta_y=1)  # a notch down moves on
    assert c.index.get() == 1
    window.simulate("wheel", x=100, y=100, delta_y=-1)
    assert c.index.get() == 0
    # a drag from anywhere, even over an item: one index per 60 px, left moves on
    window.simulate("pointer_down", x=300, y=100)
    window.simulate("pointer_move", x=170, y=100)
    window.simulate("pointer_move", x=40, y=100)  # 260 px: 4 steps
    window.simulate("pointer_up", x=40, y=100)
    assert c.index.get() == 4
    c.node.focus()
    window.simulate("key_down", key="arrow_right")
    window.simulate("key_down", key="arrow_right")  # clamped at the last
    assert c.index.get() == 5 and heard == [1, 0, 2, 4, 5]
    window.simulate("wheel", x=100, y=100, delta_y=1)
    assert c.index.get() == 5 and heard == [1, 0, 2, 4, 5]


def test_setting_the_index_moves_it_without_calling_on_change():
    window = _window()
    c = carousel(window, 400, 200, items=_boxes(window, 4))
    heard = []
    c.on_change(heard.append)
    c.index.set(3)
    _frames(window, MOVE_MS)
    assert c.position() == 3.0 and heard == []


def test_an_uncontained_carousel_keeps_widths_and_scrolls_by_pixel():
    window = _window()
    c = carousel(window, 400, 200, layout="uncontained", items=_boxes(window, 2, width=150) + _boxes(window, 1))
    heard = []
    c.on_change(heard.append)
    window.advance(16)
    assert _spans(c) == [(16.0, 150.0), (174.0, 150.0), (332.0, UNCONTAINED_WIDTH)]
    window.simulate("wheel", x=100, y=100, delta_y=40)  # half the delta
    window.advance(16)
    assert c.scroll.get() == 20.0 and _spans(c)[0] == (-4.0, 150.0)
    window.simulate("pointer_down", x=300, y=100)
    window.simulate("pointer_move", x=200, y=100)  # 1:1
    window.simulate("pointer_up", x=200, y=100)
    window.advance(16)
    assert c.scroll.get() == 120.0
    for _ in range(20):
        window.simulate("wheel", x=100, y=100, delta_y=40)
    maximum = 16 + 150 + 8 + 150 + 8 + 200 + 16 - 400  # the content's end at the right padding
    assert c.scroll.get() == maximum and heard[-1] == maximum
    c.scroll.set(0.0)
    window.advance(16)
    assert _spans(c)[0] == (16.0, 150.0)


def test_a_carousel_adds_items_and_keeps_its_look_through_a_re_colour():
    window = _window()
    c = carousel(window, 400, 200)
    item = window.create("box", width=10, height=10)
    slot = c.add(item)
    window.advance(16)
    assert item.parent() == slot and slot.parent() == c.node and _spans(c) == [(16.0, 184.0)]
    theme = Theme.resolve(theme_seed=(0x00, 0x66, 0x88, 0xFF))
    c.set_theme(theme)
    assert slot.get("fill") == theme.role("surface_container_highest") and slot.get("corner_radius") == 28.0


def test_a_carousel_rejects_an_unknown_layout():
    with pytest.raises(ValueError, match="unknown carousel layout"):
        carousel(_window(), 400, 200, layout="grid")


# -- splitter --------------------------------------------------------------------------

def _split(orientation="horizontal", position=0.5):
    window = _window()
    a, b = window.create("box", width=10, height=10), window.create("box", width=10, height=10)
    size = (416, 200) if orientation == "horizontal" else (200, 416)
    s = splitter(window, a, b, *size, orientation=orientation, position=position)
    window.advance(16)
    return window, s, a, b


def test_a_splitter_shares_its_width_between_two_panes_around_a_handle():
    window, s, a, b = _split(position=0.25)
    assert a.parent() == s.part("first") and b.parent() == s.part("second")
    assert (s.part("first").get("layout_width"), s.part("second").get("layout_width")) == (100.0, 300.0)
    handle = s.part("handle")
    assert (handle.get("layout_x"), handle.get("layout_width")) == (100.0, 16.0)
    assert handle.get("cursor") == "col_resize" and handle.get("focusable")
    assert (handle.get("role"), handle.get("label"), handle.get("value")) == ("slider", "Resize panes", 0.25)
    grip = s.part("handle.grip")
    assert (grip.get("layout_width"), grip.get("layout_height")) == (4.0, 48.0)
    assert grip.get("fill") == BASE["outline"]


def test_dragging_the_handle_puts_the_split_under_the_pointer_clamped():
    window, s, _, _ = _split()
    heard = []
    s.on_change(heard.append)
    window.simulate("pointer_down", x=208, y=100)
    assert s.interaction("handle").dragged
    window.simulate("pointer_move", x=108, y=100)  # the handle's middle at 108: 100 px to the first pane
    window.advance(16)
    assert s.position.get() == 0.25 and s.part("first").get("layout_width") == 100.0
    window.simulate("pointer_move", x=580, y=100)  # past the end: clamped
    window.simulate("pointer_up", x=580, y=100)
    window.advance(16)
    assert s.position.get() == 1.0 and s.part("second").get("layout_width") == 0.0
    assert heard == [0.25, 1.0] and not s.interaction("handle").dragged
    s.position.set(0.5)
    window.advance(16)
    window.simulate("pointer_move", x=214, y=100)  # released: moving over the handle doesn't drag it
    assert s.position.get() == 0.5


def test_a_vertical_splitter_uses_heights_and_the_up_and_down_arrows():
    window, s, _, _ = _split("vertical")
    handle = s.part("handle")
    assert handle.get("cursor") == "row_resize" and s.part("first").get("layout_height") == 200.0
    assert (s.part("handle.grip").get("layout_width"), s.part("handle.grip").get("layout_height")) == (48.0, 4.0)
    handle.focus()
    window.simulate("key_down", key="arrow_down")
    window.advance(16)
    assert s.position.get() == pytest.approx(0.5 + SPLIT_STEP)
    assert s.part("first").get("layout_height") == pytest.approx(400 * (0.5 + SPLIT_STEP), abs=1)
    window.simulate("key_down", key="arrow_right")  # not this splitter's axis
    assert s.position.get() == pytest.approx(0.5 + SPLIT_STEP)
    heard = []
    s.on_change(heard.append)
    window.simulate("key_down", key="home")
    window.simulate("key_down", key="home")  # already there: no change to hear
    assert s.position.get() == 0.0 and heard == [0.0]
    window.simulate("key_down", key="end")
    assert s.position.get() == 1.0


def test_a_splitter_answers_assistive_technology_and_setting_it_moves_the_panes():
    window, s, _, _ = _split()
    heard = []
    s.on_change(heard.append)
    s.position.set(0.75)
    window.advance(16)
    assert s.part("first").get("layout_width") == 300.0 and s.part("handle").get("value") == 0.75 and heard == []
    window.simulate("a11y_action", node=s.part("handle"), action="decrement")
    window.simulate("a11y_action", node=s.part("handle"), action="set_value", value=0.4)
    assert s.position.get() == 0.4 and heard == [0.7, 0.4]


@pytest.mark.parametrize("kwargs, message", [({"orientation": "diagonal"}, "orientation"),
                                             ({"position": 1.5}, "outside 0..1")])
def test_a_splitter_rejects_bad_arguments(kwargs, message):
    window = _window()
    with pytest.raises(ValueError, match=message):
        splitter(window, window.create("box"), window.create("box"), 400, 200, **kwargs)
