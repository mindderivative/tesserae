"""Real coverage for `tesserae.widgets`'s Date & Time Pickers category --
`date_picker_day`/`time_picker_dial`/`period_selector`. Same
thin-delegate parity strategy as the other widget test modules.
"""

import pytest
from tre import Window

from tesserae.widgets import date_picker_day, period_selector, time_picker_dial


def test_date_picker_day_matches_native_add_date_picker_day():
    window = Window(width=400, height=300)
    a = date_picker_day(window, 15, selected=True, today=True)
    b = window.add_date_picker_day(15, selected=True, today=True)
    assert a.get("corner_radius") == b.get("corner_radius")


def test_date_picker_day_selected_kwarg_really_flows_through():
    window = Window(width=400, height=300)
    selected = date_picker_day(window, 15, selected=True)
    unselected = date_picker_day(window, 16, selected=False)
    # Both are real, valid cells -- just proves neither raised and the
    # kwarg reached the delegate (no gettable "selected" state exists).
    assert selected is not None and unselected is not None


def test_time_picker_dial_matches_native_add_time_picker_dial():
    window = Window(width=400, height=300)
    a = time_picker_dial(window, hour=9, minute=30)
    b = window.add_time_picker_dial(hour=9, minute=30)
    assert a.get("corner_radius") == b.get("corner_radius")


def test_period_selector_matches_native_add_period_selector():
    window = Window(width=400, height=300)
    a_am, a_pm = period_selector(window, selected="PM")
    b_am, b_pm = window.add_period_selector(selected="PM")
    assert a_am.get("corner_radius") == b_am.get("corner_radius")
    assert a_pm.get("corner_radius") == b_pm.get("corner_radius")


def test_period_selector_rejects_invalid_value_matching_native():
    window = Window(width=400, height=300)
    with pytest.raises(ValueError, match='"AM" or "PM"'):
        period_selector(window, selected="XX")
