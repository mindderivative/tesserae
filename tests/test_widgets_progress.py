"""Real coverage for `tesserae.widgets`'s Progress & Status category --
`circular_progress`/`linear_progress`/`loading_indicator`. Since M40 each
returns a Tesserae indicator, attached to the window's root.
"""

from tre import Window

from tesserae import controls
from tesserae.widgets import circular_progress, linear_progress, loading_indicator


def test_circular_progress_returns_an_indicator():
    window = Window(width=200, height=100)
    c = circular_progress(window, value=0.4)
    assert isinstance(c, controls.CircularProgress) and c.value.get() == 0.4 and c.node.get("value") == 0.4
    assert c.node.parent() == window.root


def test_linear_progress_returns_an_indicator_at_its_size():
    window = Window(width=300, height=100)
    bar = linear_progress(window, 200, height=6, value=0.6)
    assert isinstance(bar, controls.LinearProgress) and bar.value.get() == 0.6
    assert (bar.node.get("width"), bar.node.get("height"), bar.bar.get("height")) == (200.0, 6.0, 6.0)


def test_indeterminate_progress_takes_none():
    window = Window(width=300, height=100)
    assert linear_progress(window, 200, value=None).indeterminate
    assert circular_progress(window, value=None).indeterminate


def test_loading_indicator_foreground_is_its_colour():
    window = Window(width=200, height=100)
    li = loading_indicator(window, foreground=(255, 0, 0, 255))
    assert isinstance(li, controls.LoadingIndicator) and li.shape.get("fill") == (255, 0, 0, 255)


def test_loading_indicator_defaults_to_md3s_baseline_primary():
    window = Window(width=200, height=100)
    assert loading_indicator(window).shape.get("fill") == (0x67, 0x50, 0xA4, 0xFF)
