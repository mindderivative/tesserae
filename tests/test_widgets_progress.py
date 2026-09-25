"""Real coverage for `tesserae.widgets`'s Progress & Status category --
`circular_progress`/`linear_progress`/`loading_indicator`. Same
thin-delegate parity strategy. Since `tre` 0.3.3, `loading_indicator
(foreground=...)` and `add_loading_indicator(foreground=...)` share a name,
so no translation is left to check.
"""

from tre import Window

from tesserae.widgets import circular_progress, linear_progress, loading_indicator


def test_circular_progress_matches_native_add_circular_progress():
    window = Window(width=200, height=100)
    a = circular_progress(window, value=0.4)
    b = window.add_circular_progress(value=0.4)
    assert a.get("value") == b.get("value") == 0.4


def test_linear_progress_matches_native_add_linear_progress():
    window = Window(width=200, height=100)
    a = linear_progress(window, 200, value=0.6)
    b = window.add_linear_progress(200, value=0.6)
    assert a.get("value") == b.get("value") == 0.6


def test_loading_indicator_foreground_matches_native_foreground():
    # No gettable color property on 0.3.3 -- this proves the call reaches
    # tre without raising, matching the native call with the same name.
    window = Window(width=200, height=100)
    a = loading_indicator(window, foreground=(255, 0, 0, 255))
    b = window.add_loading_indicator(foreground=(255, 0, 0, 255))
    assert a is not None and b is not None


def test_loading_indicator_default_foreground_matches_native_default():
    window = Window(width=200, height=100)
    a = loading_indicator(window)
    b = window.add_loading_indicator()
    assert a is not None and b is not None
