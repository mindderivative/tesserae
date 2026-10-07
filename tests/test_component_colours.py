"""#93: every component's colours come from the theme, in both schemes.

Two sweeps over every component fragment: (1) in the dark scheme and the light one, no text, icon or typed text is
unreadable against what is behind it (the bug that made a TextField's text dark on dark), and (2) a component built
in one scheme and switched to the other by the app looks exactly as one built in the other, so nothing keeps a
colour the theme didn't give it.
"""

import pytest
import yaml

from test_label_wrapping import FRAGMENTS, _params
from tesserae import App, View
from tesserae.spec import expand_components_to_spec

SEED = (0x67, 0x50, 0xA4, 0xFF)
#: The time picker's selected number sits on the dial's hand, a path the check can't see behind it.
HIDDEN_BACKDROP = {"TimePickerDial"}


def _luminance(c):
    def lin(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4

    return 0.2126 * lin(c[0]) + 0.7152 * lin(c[1]) + 0.0722 * lin(c[2])


def _contrast(a, b):
    hi, lo = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def _fill(node):
    try:
        value = node.get("fill")
    except ValueError:
        return None
    return value if isinstance(value, tuple) and len(value) == 4 else None


def _walk(node):
    yield node
    for child in node.children():
        yield from _walk(child)


def _backdrop(node, surface):
    parent = node.parent()
    while parent is not None:
        fill = _fill(parent)
        if fill and fill[3] >= 230:
            return fill[:3]
        parent = parent.parent()
    return surface


def _built(name, dark, *, switch_from=None):
    app = App(width=600, height=400, theme_seed=SEED, dark=dark if switch_from is None else switch_from)
    spec = expand_components_to_spec(yaml.safe_dump({"id": "x", "component": name, "with": _params(FRAGMENTS[name], "Label")}))
    view = View(spec, window=app.window)
    surface = app.theme.role("surface")[:3]
    app.window.root.set(fill=surface + (255,))
    app.window.root.add_child(view.root)
    app.window.advance(32)
    if switch_from is not None:
        app.set_dark(dark)
        app.window.advance(64)
        surface = app.theme.role("surface")[:3]
    return app, view, surface


@pytest.mark.parametrize("dark", [True, False], ids=["dark", "light"])
@pytest.mark.parametrize("name", sorted(set(FRAGMENTS) - HIDDEN_BACKDROP))
def test_text_and_icons_are_readable(name, dark):
    _, view, surface = _built(name, dark)
    unreadable = []
    for node in _walk(view.root):
        try:
            kind = node.get("kind")
        except ValueError:
            continue
        fill = _fill(node)
        if kind not in ("text", "text_input", "path") or not fill or fill[3] == 0:
            continue
        backdrop = _backdrop(node, surface)
        alpha = fill[3] / 255
        shown = tuple(fill[i] * alpha + backdrop[i] * (1 - alpha) for i in range(3))
        if _contrast(shown, backdrop) < 2.2:
            unreadable.append((kind, fill, backdrop))
    assert not unreadable, f"{name} in the {'dark' if dark else 'light'} scheme: {unreadable}"


def _colours(root):
    rows = []
    for node in _walk(root):
        try:
            row = [node.get("kind")]
        except ValueError:
            continue
        for prop in ("fill", "stroke_color", "caret_color"):
            try:
                row.append(repr(node.get(prop)))
            except ValueError:
                row.append(None)
        rows.append(tuple(row))
    return rows


@pytest.mark.parametrize("dark", [True, False], ids=["to_dark", "to_light"])
@pytest.mark.parametrize("name", sorted(FRAGMENTS))
def test_switching_the_scheme_leaves_no_stale_colour(name, dark):
    fresh = _colours(_built(name, dark)[1].root)
    switched = _colours(_built(name, dark, switch_from=not dark)[1].root)
    assert fresh == switched
