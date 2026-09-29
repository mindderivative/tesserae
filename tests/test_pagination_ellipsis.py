"""M62 (#2): `pagination` windows a long run of pages. Over `max_visible`
(7, at least 5) it has that many slots showing the first and last pages,
the current page amid its neighbours, and an inert `…` for each run left
out, redrawn as the page moves. `.shown` is each slot's page (`None` for
an ellipsis). At or under it nothing changes.
"""

import pytest
import tre

from tesserae import Theme, tokens
from tesserae.widgets import pagination
from tesserae.widgets.navigation import _pages_shown

BASE = tokens.baseline_scheme()
CLEAR = (0, 0, 0, 0)


def _window():
    return tre.Window(width=900, height=300)


def _labels(p):
    return [p.part(f"slot{k}.label").get("text") for k in range(len(p.shown))]


@pytest.mark.parametrize("current, shown", [
    (0, [0, 1, 2, 3, 4, None, 41]),        # the start: 1 2 3 4 5 … 42
    (3, [0, 1, 2, 3, 4, None, 41]),        # 4's neighbour 5 still joins the start
    (4, [0, None, 3, 4, 5, None, 41]),     # 1 … 4 5 6 … 42: two pages behind the first ellipsis
    (20, [0, None, 19, 20, 21, None, 41]),
    (37, [0, None, 36, 37, 38, None, 41]),
    (38, [0, None, 37, 38, 39, 40, 41]),   # the end: 1 … 38 39 40 41 42
    (41, [0, None, 37, 38, 39, 40, 41]),
])
def test_the_window_at_the_start_middle_and_end(current, shown):
    assert _pages_shown(42, current, 7) == shown


def test_an_ellipsis_never_stands_for_one_page_and_the_current_page_shows():
    for count in range(1, 30):
        for slots in (5, 6, 7, 9):
            for current in range(count):
                shown = _pages_shown(count, current, slots)
                assert current in shown and len(shown) == min(count, slots)
                assert shown[0] == 0 and shown[-1] == count - 1
                pages = [p for p in shown if p is not None]
                assert pages == sorted(pages) and len(set(pages)) == len(pages)
                for k, page in enumerate(shown):
                    if page is None:  # it stands for two pages or more
                        assert shown[k + 1] - shown[k - 1] > 2


def test_a_short_run_is_unchanged():
    p = pagination(_window(), 7, current=2)
    assert p.shown == list(range(7)) and p.part("page6.label").get("text") == "7"
    with pytest.raises(ValueError):
        p.part("slot0")


def test_an_even_middle_run_puts_the_extra_neighbour_after_the_current_page():
    assert _pages_shown(42, 20, 8) == [0, None, 19, 20, 21, 22, None, 41]


def test_a_long_run_draws_slots_and_an_inert_ellipsis(capfd):
    window = _window()
    p = pagination(window, 42, current=20)
    window.advance(16)
    assert _labels(p) == ["1", "…", "20", "21", "22", "…", "42"]
    assert p.part("slot3").get("fill") == BASE["primary"] and p.part("slot3").get("selected")
    assert p.part("slot3").get("label") == "Page 21" and p.part("slot0").get("label") == "Page 1"
    gap = p.part("slot1")
    assert (gap.get("focusable"), gap.get("a11y_hidden"), gap.get("cursor")) == (False, True, "default")
    assert not p.interaction("slot1").enabled and gap.get("fill") == CLEAR
    assert p.part("slot2").get("focusable") and not p.part("slot2").get("a11y_hidden")
    heard = []
    p.on_change(heard.append)
    p.view.click(gap)  # an ellipsis does nothing, quietly (tre logs a handler's error rather than raising)
    assert p.current.get() == 20 and heard == [] and "uncaught exception" not in capfd.readouterr().err


def test_moving_redraws_the_window_over_the_real_pages():
    window = _window()
    p = pagination(window, 42, current=3)
    heard = []
    p.on_change(heard.append)
    assert _labels(p) == ["1", "2", "3", "4", "5", "…", "42"]
    p.view.click(p.part("next"))
    assert p.current.get() == 4 and _labels(p) == ["1", "…", "4", "5", "6", "…", "42"]
    p.view.click(p.part("slot6"))  # the last page
    assert p.current.get() == 41 and _labels(p) == ["1", "…", "38", "39", "40", "41", "42"]
    assert p.part("slot6").get("selected") and p.part("next").get("disabled")
    gap = p.part("slot1")
    assert not gap.get("focusable") and gap.get("a11y_hidden")
    p.view.click(p.part("slot0"))
    assert p.current.get() == 0 and heard == [4, 41, 0]
    # the slot that was an ellipsis is a page again: focusable, announced, clickable
    assert _labels(p)[1] == "2" and gap.get("focusable") and not gap.get("a11y_hidden")
    assert gap.get("label") == "Page 2" and gap.get("cursor") == "pointer" and p.interaction("slot1").enabled


def test_focus_follows_the_current_page_to_its_new_slot():
    window = _window()
    p = pagination(window, 42, current=20)
    p.part("slot4").focus()  # page 22
    window.simulate("key_down", key="enter")
    assert p.current.get() == 21 and p.shown.index(21) == 3
    assert p.part("slot3").get("focused") and not p.part("slot4").get("focused")
    p.part("next").focus()
    window.simulate("key_down", key="enter")
    assert p.current.get() == 22 and p.part("next").get("focused")  # focus elsewhere stays put


def test_setting_the_page_and_a_re_colour_keep_the_window():
    window = _window()
    p = pagination(window, 42)
    p.current.set(30)
    assert _labels(p) == ["1", "…", "30", "31", "32", "…", "42"]
    theme = Theme.resolve(theme_seed=(0x00, 0x66, 0x88, 0xFF))
    p.set_theme(theme)
    assert _labels(p) == ["1", "…", "30", "31", "32", "…", "42"]
    assert p.part("slot3").get("fill") == theme.role("primary") and p.part("slot1").get("a11y_hidden")


def test_max_visible_sets_when_windowing_starts():
    assert pagination(_window(), 9, max_visible=9).shown == list(range(9))
    p = pagination(_window(), 9, current=4, max_visible=5)
    assert p.shown == [0, None, 4, None, 8]


@pytest.mark.parametrize("max_visible", [4, 0, 7.0, True, "7"])
def test_max_visible_is_a_whole_number_of_at_least_five(max_visible):
    with pytest.raises(ValueError, match="max_visible is a whole number of at least 5"):
        pagination(_window(), 10, max_visible=max_visible)
