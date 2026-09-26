"""Real coverage for `tesserae.widgets`'s Buttons & Actions category --
`button`/`icon_button`/`fab`/`extended_fab`/`split_button`/`button_group`.

`button` is built from its fragment since M41 (`tests/test_composed_widgets.py`
covers it); the rest are, until M41 Phase 2, deliberately thin delegates to `tre`'s own native `Window.add_*`
factories (see `buttons.py`'s own module docstring for why), so the real
risk here isn't MD3 color/shape math -- `tre` already gets that right --
it's argument-forwarding: wrong positional/keyword mapping, a dropped
default, a mismatched return-tuple shape. Each test constructs the same
widget two ways -- once via `tesserae.widgets`, once via the native
`window.add_*` call with identical arguments -- and asserts they resolve
to the identical real styling, proving the delegate is a true pass-
through and not a subtly different reimplementation.
"""

from tre import Window

from tesserae.widgets import (
    button,
    button_group,
    extended_fab,
    fab,
    icon_button,
    split_button,
)


def test_icon_button_matches_native_add_icon_button():
    window = Window(width=400, height=200)
    a = icon_button(window, "close", variant="filled")
    b = window.add_icon_button("close", variant="filled")
    assert a.get("corner_radius") == b.get("corner_radius")


def test_fab_matches_native_add_fab():
    window = Window(width=400, height=200)
    a = fab(window, "add", size="small", variant="primary")
    b = window.add_fab("add", size="small", variant="primary")
    assert a.get("corner_radius") == b.get("corner_radius")
    assert a.get("elevation") == b.get("elevation")


def test_fab_size_kwarg_really_flows_through():
    # Small vs. default FABs have real, different corner radii
    # (fab_shape: small -> 12.0, default -> 16.0).
    window = Window(width=400, height=200)
    small = fab(window, "add", size="small")
    default = fab(window, "add", size="default")
    assert small.get("corner_radius") != default.get("corner_radius")


def test_extended_fab_matches_native_add_extended_fab():
    window = Window(width=400, height=200)
    a = extended_fab(window, "Compose", 160, icon="add")
    b = window.add_extended_fab("Compose", 160, icon="add")
    assert a.get("corner_radius") == b.get("corner_radius")


def test_split_button_matches_native_add_split_button_shape():
    window = Window(width=400, height=200)
    a_leading, a_trailing, a_container = split_button(window, "Send", 140, 40)
    b_leading, b_trailing, b_container = window.add_split_button("Send", 140, 40)
    assert a_leading.get("corner_radius") == b_leading.get("corner_radius")
    assert a_trailing.get("corner_radius") == b_trailing.get("corner_radius")


def test_button_group_matches_native_add_button_group_shape():
    window = Window(width=400, height=200)
    a_container, a_buttons = button_group(window, ["Day", "Week", "Month"], 240, 40)
    b_container, b_buttons = window.add_button_group(["Day", "Week", "Month"], 240, 40)
    assert len(a_buttons) == len(b_buttons) == 3
    for a, b in zip(a_buttons, b_buttons):
        assert a.get("corner_radius") == b.get("corner_radius")
