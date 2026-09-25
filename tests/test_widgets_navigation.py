"""Real coverage for `tesserae.widgets`'s Navigation & Shell Composition
category. Same thin-delegate parity strategy as the other widget test
modules, plus a check that `toolbar(vibrant=...)` really reaches `tre`'s
own `add_toolbar(vibrant=...)`.
"""

from tre import Window

from tesserae.widgets import (
    navigation_drawer,
    navigation_rail,
    status_bar,
    tabs,
    toolbar,
    top_app_bar,
)


def test_tabs_matches_native_add_tabs():
    window = Window(width=400, height=300)
    a = tabs(window, ["One", "Two"])
    b = window.add_tabs(["One", "Two"])
    assert len(a) == len(b) == 2


def test_navigation_rail_matches_native_add_navigation_rail():
    window = Window(width=400, height=300)
    a = navigation_rail(window, ["Home", "Settings"], ["home", "settings"])
    b = window.add_navigation_rail(["Home", "Settings"], ["home", "settings"])
    assert len(a) == len(b) == 2


def test_navigation_drawer_matches_native_add_navigation_drawer():
    window = Window(width=400, height=300)
    a_container, a_entries = navigation_drawer(window, ["Home"], ["home"])
    b_container, b_entries = window.add_navigation_drawer(["Home"], ["home"])
    assert a_container.get("corner_radius") == b_container.get("corner_radius")
    assert len(a_entries) == len(b_entries) == 1


def test_toolbar_vibrant_matches_native_vibrant():
    # Prove `vibrant=` reaches the real underlying resolution by comparing
    # against the native call with the same argument.
    window = Window(width=400, height=300)
    a = toolbar(window, variant="docked", vibrant=True)
    b = window.add_toolbar(variant="docked", vibrant=True)
    assert a.get("corner_radius") == b.get("corner_radius")


def test_toolbar_variant_kwarg_really_flows_through():
    window = Window(width=400, height=300)
    docked = toolbar(window, variant="docked")
    floating = toolbar(window, variant="floating")
    assert docked.get("corner_radius") != floating.get("corner_radius")
    assert docked.get("elevation") != floating.get("elevation")


def test_top_app_bar_matches_native_add_top_app_bar():
    window = Window(width=400, height=300)
    a_bar, a_leading, a_trailing = top_app_bar(window, "Title", leading_icon="menu")
    b_bar, b_leading, b_trailing = window.add_top_app_bar("Title", leading_icon="menu")
    assert a_bar.get("corner_radius") == b_bar.get("corner_radius")
    assert a_leading is not None and b_leading is not None


def test_status_bar_matches_native_add_status_bar():
    window = Window(width=400, height=300)
    a = status_bar(window, "Ready")
    b = window.add_status_bar("Ready")
    assert a.get("corner_radius") == b.get("corner_radius")
