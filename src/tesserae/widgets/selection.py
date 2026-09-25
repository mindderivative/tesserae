"""Tesserae's own namespace for the Selection & Input category --
`checkbox`, `slider`, `radio_button`, `switch`, `spin_box`.

`checkbox`/`slider`/`radio_button`/`switch` are real `NodeKind` primitives
in `tre` itself (not compositions), already fully reachable from Python
via `Window.add_checkbox`/etc. -- these wrappers exist purely for a
uniform `tesserae.widgets` surface a GUI designer can rely on regardless
of what's a primitive vs. a composition underneath `tre`, matching
`buttons.py`'s own thin-delegate shape. `spin_box` is a real composition
(a text field flanked by minus/plus icon buttons). None of these expose
an ambiguous color kwarg -- `background` already means "this widget's own
fill" in every one that takes it -- so no naming translation is needed
here (see `buttons.py`'s module docstring for when that would apply).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tre import Node, Window


def checkbox(
    window: "Window",
    background: tuple[int, int, int, int],
    width: float,
    height: float,
    checked: bool = False,
    x: float | None = None,
    y: float | None = None,
) -> "Node":
    """A real MD3 checkbox. The engine never flips `checked` itself on
    click -- call `node.set_checked(...)` from your own `on_click`."""
    return window.add_checkbox(background, width, height, checked=checked, x=x, y=y)


def slider(
    window: "Window",
    background: tuple[int, int, int, int],
    width: float,
    height: float,
    value: float = 0.0,
    x: float | None = None,
    y: float | None = None,
) -> "Node":
    """A real MD3 slider. `value` seeds `thumb_position`, clamped to
    0.0..=1.0. Drag-to-set and arrow-key nudging are built into the
    engine's own input dispatch -- no Python wiring needed for those."""
    return window.add_slider(background, width, height, value=value, x=x, y=y)


def radio_button(
    window: "Window",
    size: float = 20.0,
    selected: bool = False,
    x: float | None = None,
    y: float | None = None,
) -> "Node":
    """A real MD3 radio button. Grouping/exclusivity is the app's own
    concern -- the engine has no notion of a radio group."""
    return window.add_radio_button(size=size, selected=selected, x=x, y=y)


def switch(
    window: "Window",
    width: float = 52.0,
    height: float = 32.0,
    selected: bool = False,
    x: float | None = None,
    y: float | None = None,
) -> "Node":
    """A real MD3 switch. `selected` is its on/off state (`tre` 0.3.3
    names it the same as `radio_button`'s; read it back with
    `Node.get_selected`)."""
    return window.add_switch(width=width, height=height, selected=selected, x=x, y=y)


def spin_box(
    window: "Window",
    value: str,
    x: float | None = None,
    y: float | None = None,
) -> tuple["Node", "Node", "Node"]:
    """A real MD3 numeric stepper (a text field flanked by minus/plus
    icon buttons). Returns `(field, minus_button, plus_button)`, matching
    `tre`'s own `add_spin_box`. No `width`/`height` -- sized from its own
    content, matching the native factory."""
    return window.add_spin_box(value, x=x, y=y)
