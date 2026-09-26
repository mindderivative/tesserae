"""Tesserae's own namespace for the Buttons & Actions category of `tre`'s
MD3 catalog -- `button`, `icon_button`, `fab`, `extended_fab`,
`split_button`, `button_group`.

Each function here is a thin, faithful delegate to the matching
`Window.add_*` factory in `tre` itself: same parameter names, order, and
defaults, `window` as the first positional argument (matching
`tesserae.component.instantiate`'s own established convention). This is
deliberate, not a placeholder -- `tre`'s own factories already resolve MD3
color/shape/elevation correctly against the live theme, and for
`split_button`/`button_group` specifically, only the real Rust factory can
drive their hover/press shape-tightening and reflow animations (no public
Python API reaches `PaintProperties.button_group_reflow`/`shape`/
`press_interactive_shape`; a from-scratch Python reimplementation could
only ever produce a rest-state-only port). Delegating keeps full fidelity
for all six and gives Tesserae apps one consistent `tesserae.widgets`
surface to import from, so a widget "looks like Tesserae's own" whether or
not `tre` happens to implement it as a composition under the hood.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

from tesserae.widgets._composed import Widget, fragment

if TYPE_CHECKING:
    from tesserae.theme import Theme
    from tre import Node, Window


#: `button`'s variants: the fragment, and its label's colour role (its feedback's too).
_BUTTONS = {
    "elevated": ("ButtonElevated", "primary"),
    "filled": ("ButtonFilled", "on_primary"),
    "filled_tonal": ("ButtonFilledTonal", "on_secondary_container"),
    "outlined": ("ButtonOutlined", "primary"),
    "text": ("ButtonText", "primary"),
}


def _hex(color: tuple[int, int, int, int]) -> str:
    return "#" + "".join(f"{c:02X}" for c in color)


def button(
    window: "Window",
    label: str,
    width: float,
    height: float,
    variant: str = "filled",
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    corner_radius: float | None = None,
    theme: "Theme | None" = None,
    on_click: Callable[[], Any] | None = None,
) -> Widget:
    """MD3's button, built from its fragment (M41). `variant`: elevated,
    filled, filled_tonal, outlined or text. It's a pill (`corner_radius`
    half the height) unless told otherwise. `on_click` makes it a focusable
    button that Enter and Space activate, with MD3's feedback."""
    if variant not in _BUTTONS:
        raise ValueError(f"unknown button variant {variant!r}; expected one of {sorted(_BUTTONS)}")
    fragment, content = _BUTTONS[variant]
    radius = float(height) / 2 if corner_radius is None else float(corner_radius)

    def edit(spec: dict[str, Any]) -> None:
        if border_color is not None:
            spec["style"]["border_color"] = _hex(border_color)
        if border_width is not None:
            spec["style"]["border_width"] = float(border_width)

    widget = Widget(window, fragment, {"label": label, "width": width, "height": height, "corner_radius": radius},
                    theme=theme, x=x, y=y, interactive={None: content}, edit=edit, name="button")
    if on_click is not None:
        widget.on_click(on_click)
    return widget


def _borders(parts: list[str | None], border_color, border_width) -> Callable[[dict[str, Any]], None] | None:
    """An `edit` giving `parts` of a widget's spec the caller's border."""
    if border_color is None and border_width is None:
        return None

    def edit(spec: dict[str, Any]) -> None:
        for part in parts:
            node = spec if part is None else next(c for c in spec["children"] if c["id"].endswith("." + part))
            style = node.setdefault("style", {})
            if border_color is not None:
                style["border_color"] = _hex(border_color)
            if border_width is not None:
                style["border_width"] = float(border_width)
    return edit


def _variant(kind: str, variant: str, table: dict[str, str]) -> str:
    if variant not in table:
        raise ValueError(f"unknown {kind} variant {variant!r}; expected one of {sorted(table)}")
    return table[variant]


_ICON_BUTTONS = {"standard": "IconButtonStandard", "filled": "IconButtonFilled",
                 "filled_tonal": "IconButtonFilledTonal", "outlined": "IconButtonOutlined"}


def icon_button(
    window: "Window",
    icon: str,
    size: float = 40.0,
    variant: str = "standard",
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    label: str | None = None,
    theme: "Theme | None" = None,
    on_click: Callable[[], Any] | None = None,
) -> Widget:
    """MD3's icon button (M41: built from its fragment). `variant`:
    standard, filled, filled_tonal or outlined. A circle `size` across.
    Give `label=` so a screen reader can name it."""
    widget = Widget(window, _variant("icon button", variant, _ICON_BUTTONS),
                    {"icon": icon, "size": size, "corner_radius": float(size) / 2}, theme=theme, label=label,
                    x=x, y=y, interactive={None: None}, edit=_borders([None], border_color, border_width),
                    name="icon_button")
    if on_click is not None:
        widget.on_click(on_click)
    return widget


_FABS = {"surface": "FabSurface", "primary": "FabPrimary", "secondary": "FabSecondary", "tertiary": "FabTertiary"}
#: MD3's FAB sizes: container, corner radius, icon.
_FAB_SIZES = {"small": (40.0, 12.0, 24.0), "default": (56.0, 16.0, 24.0), "large": (96.0, 28.0, 36.0)}


def fab(
    window: "Window",
    icon: str,
    size: str = "default",
    variant: str = "surface",
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    label: str | None = None,
    theme: "Theme | None" = None,
    on_click: Callable[[], Any] | None = None,
) -> Widget:
    """MD3's floating action button (M41: built from its fragment).
    `size`: small (40), default (56) or large (96, with a 36 px icon).
    `variant`: surface, primary, secondary or tertiary."""
    if size not in _FAB_SIZES:
        raise ValueError(f"unknown FAB size {size!r}; expected one of {sorted(_FAB_SIZES)}")
    box, radius, glyph = _FAB_SIZES[size]
    border = _borders([None], border_color, border_width)

    def edit(spec: dict[str, Any]) -> None:
        spec["children"][0]["style"].update(width=glyph, height=glyph)
        if border is not None:
            border(spec)

    widget = Widget(window, _variant("FAB", variant, _FABS), {"icon": icon, "size": box, "corner_radius": radius},
                    theme=theme, label=label, x=x, y=y, interactive={None: None}, edit=edit, name="fab")
    if on_click is not None:
        widget.on_click(on_click)
    return widget


_EXTENDED_FABS = {"surface": "ExtendedFabSurface", "primary": "ExtendedFabPrimary",
                  "secondary": "ExtendedFabSecondary", "tertiary": "ExtendedFabTertiary"}


def extended_fab(
    window: "Window",
    label: str,
    width: float,
    icon: str | None = None,
    variant: str = "primary",
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    theme: "Theme | None" = None,
    on_click: Callable[[], Any] | None = None,
) -> Widget:
    """MD3's extended FAB (M41: built from its fragment): an optional
    leading icon and a label, 56 px tall."""
    border = _borders([None], border_color, border_width)

    def edit(spec: dict[str, Any]) -> None:
        if icon is None:  # MD3's icon-less extended FAB: the label alone, 20 px either side
            spec["children"] = [c for c in spec["children"] if not c["id"].endswith(".icon")]
            spec["style"].update(padding={"left": 20, "right": 20, "top": 0, "bottom": 0}, justify_content="center")
        if border is not None:
            border(spec)

    widget = Widget(window, _variant("extended FAB", variant, _EXTENDED_FABS),
                    {"label": label, "icon": icon or "add", "width": width}, theme=theme, x=x, y=y,
                    interactive={None: None}, edit=edit, name="extended_fab")
    if on_click is not None:
        widget.on_click(on_click)
    return widget


_SPLIT_BUTTONS = {"elevated": "SplitButtonElevated", "filled": "SplitButtonFilled",
                  "filled_tonal": "SplitButtonFilledTonal", "outlined": "SplitButtonOutlined",
                  "text": "SplitButtonText"}
#: `tre`'s split button: the facing corners tighten to this on hover, over 100 ms.
SPLIT_TIGHTENED = 8.0
MORPH_MS = 100


def split_button(
    window: "Window",
    label: str,
    width: float,
    height: float,
    variant: str = "filled",
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    theme: "Theme | None" = None,
    on_click: Callable[[], Any] | None = None,
    on_menu: Callable[[], Any] | None = None,
) -> Widget:
    """MD3's split button (M41: built from its fragment): a `leading`
    action and a `trailing` chevron, parts of the returned `Widget`. While
    it's hovered, the corners where the two meet tighten, as `tre`'s did.
    `on_click` is the action, `on_menu` the chevron."""
    rest = float(height) / 2
    widget = Widget(window, _variant("split button", variant, _SPLIT_BUTTONS),
                    {"label": label, "width": width, "height": height, "corner_radius": rest}, theme=theme,
                    x=x, y=y, interactive={"leading": None, "trailing": None},
                    edit=_borders(["leading", "trailing"], border_color, border_width), name="split_button")
    tight = (widget.theme.shape("split_button", "tightened") if widget.theme.is_set else None) or SPLIT_TIGHTENED
    corners = {  # (top_left, top_right, bottom_right, bottom_left)
        "leading": ((rest,) * 4, (rest, tight, tight, rest)),
        "trailing": ((rest,) * 4, (tight, rest, rest, tight)),
    }

    def morph(hovered: bool) -> None:
        for part, (resting, tightened) in corners.items():
            radius = tightened if hovered else resting
            for node in (widget.part(part), widget.interaction(part).clip):
                node.animate("corner_radius", radius, MORPH_MS)

    widget._undo.append(widget.view._listen(widget.node, "pointer_enter", lambda e: morph(True)))
    widget._undo.append(widget.view._listen(widget.node, "pointer_leave", lambda e: morph(False)))
    if on_click is not None:
        widget.on_click(on_click, part="leading")
    if on_menu is not None:
        widget.on_click(on_menu, part="trailing")
    return widget


#: The pressed child's corners in a button group, by its height (`tre`'s):
#: 8 up to 38 px, 12 up to 44, else 16.
def _group_tightened(height: float) -> float:
    return 8.0 if height <= 38 else 12.0 if height <= 44 else 16.0


#: How much wider a pressed group child grows; its neighbours share the loss.
GROUP_GROWTH = 12.0


def button_group(
    window: "Window",
    labels: list[str],
    width: float,
    height: float,
    variant: str = "filled",
    x: float | None = None,
    y: float | None = None,
    *,
    theme: "Theme | None" = None,
    on_click: Callable[[int], Any] | None = None,
) -> Widget:
    """MD3's button group (M41): one button per label, `width`x`height`,
    8 px apart; parts `b0`, `b1`, ... While one is pressed, its corners
    tighten and it grows 12 px, its neighbours sharing the loss, and it
    all comes back on release -- the intent of `tre`'s, whose reflow
    compounded and never restored. `on_click(index)` hears each."""
    fragment_name, _ = _BUTTONS[variant] if variant in _BUTTONS else (None, None)
    if fragment_name is None:
        raise ValueError(f"unknown button group variant {variant!r}; expected one of {sorted(_BUTTONS)}")
    rest = float(height) / 2
    name = "button_group"
    children = [fragment(fragment_name, {"label": text, "width": width, "height": height, "corner_radius": rest},
                         f"{name}.b{i}") for i, text in enumerate(labels)]
    spec = {"id": name, "kind": "Container", "style": {"flex_direction": "horizontal", "gap": 8},
            "children": children}
    widget = Widget(window, spec=spec, theme=theme, x=x, y=y, interactive={f"b{i}": None for i in range(len(labels))},
                    name=name)
    tight = (widget.theme.shape("button_group", "tightened") if widget.theme.is_set else None) or _group_tightened(
        float(height))
    count = len(labels)
    pressed: list[int] = []

    def press(index: int) -> None:
        release()
        pressed.append(index)
        neighbours = [n for n in (index - 1, index + 1) if 0 <= n < count]
        widths = {index: float(width) + GROUP_GROWTH}
        for n in neighbours:
            widths[n] = max(0.0, float(width) - GROUP_GROWTH / len(neighbours))
        for i, w in widths.items():
            widget.part(f"b{i}").set(width=w)
        for node in (widget.part(f"b{index}"), widget.interaction(f"b{index}").clip):
            node.animate("corner_radius", tight, MORPH_MS)

    def release() -> None:
        while pressed:
            index = pressed.pop()
            for i in range(count):
                widget.part(f"b{i}").set(width=float(width))
            for node in (widget.part(f"b{index}"), widget.interaction(f"b{index}").clip):
                node.animate("corner_radius", rest, MORPH_MS)

    for i in range(count):
        part = widget.part(f"b{i}")
        widget._undo.append(widget.view._listen(part, "pointer_down", lambda e, i=i: press(i)))
        widget._undo.append(widget.view._listen(part, "pointer_up", lambda e: release()))
        widget._undo.append(widget.view._listen(part, "pointer_leave", lambda e: release()))
        if on_click is not None:
            widget.on_click(lambda i=i: on_click(i), part=f"b{i}")
    return widget
