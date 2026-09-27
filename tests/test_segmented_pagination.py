"""M42 Phase 5: `segmented_button` and `pagination`, new by Q1 (`tre` had
them as `add_segmented_button`/`add_pagination`, never wrapped), built on
`tre` 0.3.4's building blocks and M39's interaction. Driven headlessly
with `simulate`/`advance`.
"""

import pytest
import tre

from tesserae import Theme, tokens
from tesserae.widgets import pagination, segmented_button
from tesserae.widgets.buttons import SEGMENT_CHECK
from tesserae.widgets.navigation import DISABLED_ALPHA

BASE = tokens.baseline_scheme()
CLEAR = (0, 0, 0, 0)


def _window():
    window = tre.Window(width=600, height=300)
    window.root.set(padding_top=0, padding_right=0, padding_bottom=0, padding_left=0, gap=0,
                    align_items="flex_start")
    return window


def _key(window, key):
    window.simulate("key_down", key=key)
    window.advance(16)


# -- segmented button ---------------------------------------------------------------

def test_a_segmented_button_is_md3s_outlined_pill():
    window = _window()
    s = segmented_button(window, ["Day", "Week", "Month"], width=304, selected=1)  # 1 + 3 x 100 + 2 + 1
    window.advance(16)
    node = s.node
    assert (node.get("layout_width"), node.get("layout_height"), node.get("corner_radius")) == (304.0, 40.0, 20.0)
    assert (node.get("stroke_color"), node.get("stroke_width")) == (BASE["outline"], 1.0)
    assert node.get("role") == "group"
    assert [s.part(f"s{i}").get("layout_width") for i in range(3)] == [100.0, 100.0, 100.0]
    assert s.part("divider1").get("fill") == BASE["outline"] and s.part("divider1").get("layout_width") == 1.0
    # the ends follow the pill, inside the outline; the middle is square
    assert tuple(s.part("s0").get("corner_radius")) == (19.0, 0.0, 0.0, 19.0)
    assert tuple(s.part("s2").get("corner_radius")) == (0.0, 19.0, 19.0, 0.0)
    assert tuple(s.interaction("s2").clip.get("corner_radius")) == (0.0, 19.0, 19.0, 0.0)
    assert s.part("s1").get("corner_radius") == 0.0
    # selected: secondary_container, a check before its label
    assert s.part("s1").get("fill") == BASE["secondary_container"]
    assert s.part("s1.check").get("visible") and s.part("s1.check").get("layout_width") == SEGMENT_CHECK
    assert s.part("s1.label").get("fill") == BASE["on_secondary_container"]
    assert s.part("s0").get("fill") == CLEAR and not s.part("s0.check").get("visible")
    assert s.part("s0.check").get("layout_width") == 0.0
    assert s.part("s0.label").get("fill") == BASE["on_surface"] and s.part("s0.label").get("font_size") == 14.0
    assert [(s.part(f"s{i}").get("role"), s.part(f"s{i}").get("label"), s.part(f"s{i}").get("checked"))
            for i in range(3)] == [("radio", "Day", False), ("radio", "Week", True), ("radio", "Month", False)]


def test_a_segmented_button_fits_its_widest_label_without_a_width():
    window = _window()
    s = segmented_button(window, ["A", "Longer label"])
    window.advance(16)
    widest = window.measure_text("Longer label", font_size=14.0, font_weight=500.0)[0]
    segment = s.part("s0").get("layout_width")
    assert segment == s.part("s1").get("layout_width")
    assert segment >= widest + 24 + SEGMENT_CHECK + 8  # 12 px either side, the check and its gap


def test_single_select_clicks_select_and_the_arrows_move_the_selection():
    window = _window()
    s = segmented_button(window, ["Day", "Week", "Month"], selected=0)
    heard = []
    s.on_change(heard.append)
    s.view.click(s.part("s2"))
    window.advance(16)
    assert s.selected.get() == 2 and heard == [2]
    assert s.part("s2").get("fill") == BASE["secondary_container"] and s.part("s0").get("fill") == CLEAR
    s.view.click(s.part("s2"))  # a selected segment stays selected
    assert s.selected.get() == 2 and heard == [2]
    # one Tab stop, the selected segment
    assert [s.part(f"s{i}").get("focusable") for i in range(3)] == [False, False, True]
    s.part("s2").focus()
    _key(window, "arrow_right")  # wraps
    assert s.selected.get() == 0 and s.part("s0").get("focused") and heard == [2, 0]
    _key(window, "arrow_left")
    assert s.selected.get() == 2 and s.part("s2").get("focused")


def test_multi_select_toggles_and_the_arrows_only_move_focus():
    window = _window()
    s = segmented_button(window, ["Bold", "Italic", "Underline"], multi=True, selected=[0])
    heard = []
    s.on_change(heard.append)
    assert s.selected.get() == frozenset({0})
    s.view.click(s.part("s2"))
    s.view.click(s.part("s0"))
    window.advance(16)
    assert s.selected.get() == frozenset({2}) and heard == [frozenset({0, 2}), frozenset({2})]
    assert [s.part(f"s{i}").get("role") for i in range(3)] == ["checkbox"] * 3
    assert all(s.part(f"s{i}").get("focusable") for i in range(3))  # each a Tab stop
    assert [s.part(f"s{i}").get("checked") for i in range(3)] == [False, False, True]
    s.part("s0").focus()
    _key(window, "arrow_right")
    assert s.part("s1").get("focused") and s.selected.get() == frozenset({2})
    _key(window, "enter")
    assert s.selected.get() == frozenset({1, 2})


def test_setting_the_selection_redraws_it_without_calling_on_change():
    window = _window()
    s = segmented_button(window, ["Day", "Week"])
    heard = []
    s.on_change(heard.append)
    assert s.selected.get() is None and s.part("s0").get("focusable")  # nothing selected: the first is the stop
    s.selected.set(1)
    window.advance(16)
    assert s.part("s1").get("fill") == BASE["secondary_container"] and s.part("s1.check").get("visible")
    assert heard == []


def test_a_segmented_button_takes_a_theme_and_keeps_its_state_and_shape_through_a_re_colour():
    window = _window()
    s = segmented_button(window, ["Day", "Week"], selected=1)
    theme = Theme.resolve(theme_seed=(0x00, 0x66, 0x88, 0xFF))
    s.set_theme(theme)
    window.advance(16)
    assert s.part("s1").get("fill") == theme.role("secondary_container")
    assert s.part("s0.label").get("fill") == theme.role("on_surface")
    assert s.node.get("stroke_color") == theme.role("outline")
    assert s.part("s1.check").get("visible") and not s.part("s0.check").get("visible")
    assert tuple(s.part("s1").get("corner_radius")) == (0.0, 19.0, 19.0, 0.0)
    assert tuple(s.interaction("s1").clip.get("corner_radius")) == (0.0, 19.0, 19.0, 0.0)


@pytest.mark.parametrize("labels, kwargs, message", [
    (["Only"], {}, "at least 2 labels"),
    (["A", "B"], {"selected": 2}, "out of range"),
    (["A", "B"], {"selected": [0, 1]}, "multi=True"),
    (["A", "B"], {"selected": [3], "multi": True}, "out of range"),
])
def test_a_segmented_button_rejects_bad_arguments(labels, kwargs, message):
    with pytest.raises(ValueError, match=message):
        segmented_button(_window(), labels, **kwargs)


# -- pagination ------------------------------------------------------------------------

def test_pagination_is_previous_numbered_pages_and_next():
    window = _window()
    p = pagination(window, 3, current=1)
    window.advance(16)
    parts = ["previous", "page0", "page1", "page2", "next"]
    xs = [p.part(n).get("layout_x") for n in parts]
    assert [b - a for a, b in zip(xs, xs[1:])] == [44.0] * 4  # 40 px circles, 4 apart
    assert all((p.part(n).get("layout_width"), p.part(n).get("corner_radius")) == (40.0, 20.0) for n in parts)
    assert p.node.get("role") == "group" and p.node.get("label") == "Pagination"
    assert p.part("page1").get("fill") == BASE["primary"] and p.part("page1.label").get("fill") == BASE["on_primary"]
    assert p.part("page1").get("selected") and not p.part("page0").get("selected")
    assert p.part("page0").get("fill") == CLEAR and p.part("page0.label").get("fill") == BASE["on_surface_variant"]
    assert p.part("page2.label").get("text") == "3" and p.part("page2").get("label") == "Page 3"
    assert p.part("previous.icon").get("rotation_deg") == 180.0 and p.part("next.icon").get("rotation_deg") == 0.0
    assert (p.part("previous").get("label"), p.part("next").get("label")) == ("Previous page", "Next page")
    assert p.part("previous.icon").get("fill") == BASE["on_surface_variant"]


def test_pages_previous_and_next_move_the_current_page():
    window = _window()
    p = pagination(window, 4)
    heard = []
    p.on_change(heard.append)
    p.view.click(p.part("next"))
    p.view.click(p.part("page3"))
    p.view.click(p.part("previous"))
    window.advance(16)
    assert p.current.get() == 2 and heard == [1, 3, 2]
    assert p.part("page2").get("fill") == BASE["primary"] and p.part("page3").get("fill") == CLEAR
    p.part("next").focus()
    _key(window, "enter")
    assert p.current.get() == 3


def test_previous_and_next_are_disabled_at_the_ends():
    window = _window()
    p = pagination(window, 2)
    heard = []
    p.on_change(heard.append)
    r, g, b, _ = BASE["on_surface"]

    def disabled(part):
        return (not p.part(part).get("focusable"), p.part(part).get("disabled"),
                p.part(f"{part}.icon").get("fill") == (r, g, b, DISABLED_ALPHA), not p.interaction(part).enabled)

    assert disabled("previous") == (True, True, True, True)
    assert disabled("next") == (False, False, False, False)
    p.view.click(p.part("previous"))  # ignored
    assert p.current.get() == 0 and heard == []
    p.view.click(p.part("next"))
    window.advance(16)
    assert p.current.get() == 1 and heard == [1]
    assert disabled("next") == (True, True, True, True)
    assert disabled("previous") == (False, False, False, False)
    p.view.click(p.part("next"))
    assert p.current.get() == 1 and heard == [1]


def test_setting_the_page_redraws_it_and_a_re_colour_keeps_it():
    window = _window()
    p = pagination(window, 3)
    heard = []
    p.on_change(heard.append)
    p.current.set(2)
    window.advance(16)
    assert p.part("page2").get("fill") == BASE["primary"] and p.part("next").get("disabled") and heard == []
    theme = Theme.resolve(theme_seed=(0x00, 0x66, 0x88, 0xFF))
    p.set_theme(theme)
    window.advance(16)
    assert p.part("page2").get("fill") == theme.role("primary")
    assert p.part("page0.label").get("fill") == theme.role("on_surface_variant")
    assert p.part("previous.icon").get("rotation_deg") == 180.0
    r, g, b, _ = theme.role("on_surface")
    assert p.part("next.icon").get("fill") == (r, g, b, DISABLED_ALPHA)


@pytest.mark.parametrize("count, current, message", [(0, 0, "at least one page"), (3, 3, "out of range")])
def test_pagination_rejects_bad_arguments(count, current, message):
    with pytest.raises(ValueError, match=message):
        pagination(_window(), count, current=current)
