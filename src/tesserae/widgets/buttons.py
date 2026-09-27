"""Tesserae's own namespace for the Buttons & Actions category --
`button`, `icon_button`, `fab`, `extended_fab`, `split_button`,
`button_group` (M41) and `segmented_button` (M42).

Each is built by Tesserae from its fragment (or several) with
`tesserae.widgets._composed.Widget`, with MD3's feedback (M39) in its
content's colour. The split button's hover and the button group's press
morph animate `corner_radius` on the part and its feedback's clip, which
`tre`'s own factories did in Rust with no public Python API.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any, Callable, Optional

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


#: A segmented button's check, and the gap after it (MD3).
SEGMENT_CHECK = 18.0
SEGMENT_GAP = 8.0


def segmented_button(
    window: "Window",
    labels: list[str],
    width: float | None = None,
    height: float = 40.0,
    selected: "int | list[int] | None" = None,
    multi: bool = False,
    x: float | None = None,
    y: float | None = None,
    *,
    theme: "Theme | None" = None,
) -> Widget:
    """MD3's outlined segmented button (M42): equal segments in one 1 px
    `outline` pill, 1 px dividers between them, `label_large` labels in
    `on_surface`. A selected segment is `secondary_container` with an 18 px
    check before its `on_secondary_container` label. Single-select (a
    click selects; one Tab stop, the arrows move the selection, as radio
    buttons do) or `multi=True` (a click toggles; each segment a Tab stop,
    the arrows move focus). `.selected` is a `Signal`: an index or `None`,
    or a `frozenset` of indices with `multi`; `.on_change(fn)` hears the
    user's changes. Without `width`, segments fit the widest label. Parts
    `s0`, `s1`, ... with `label`/`check`."""
    from tesserae import a11y
    from tesserae.reactive import Effect, Signal

    count = len(labels)
    if count < 2:
        raise ValueError(f"a segmented button needs at least 2 labels, got {count}")
    chosen = _segments_selected(selected, multi, count)
    height = float(height)
    inner = height - 2.0  # inside the 1 px outline
    if width is None:  # MD3: 12 px padding, the check and its gap, the label
        widest = max(window.measure_text(text, font_size=14.0, font_weight=500.0)[0] for text in labels)
        width = 2.0 + math.ceil(max(48.0, 24.0 + SEGMENT_CHECK + SEGMENT_GAP + widest)) * count + (count - 1)
    width = float(width)
    segment = (width - 2.0 - (count - 1)) / count
    name = "segmented_button"
    children: list[dict[str, Any]] = []
    for i, text in enumerate(labels):
        if i:
            children.append({"id": f"{name}.divider{i}", "kind": "Rect",
                             "style": {"width": 1, "height": inner, "background": "outline"}})
        children.append({"id": f"{name}.s{i}", "kind": "Rect",
                         "style": {"width": segment, "height": inner, "background": "transparent",
                                   "flex_direction": "horizontal", "align_items": "center",
                                   "justify_content": "center"},
                         "children": [
                             {"id": f"{name}.s{i}.check", "kind": "Icon", "icon": {"name": "check"},
                              "style": {"width": SEGMENT_CHECK, "height": SEGMENT_CHECK,
                                        "foreground": "on_secondary_container"}},
                             {"id": f"{name}.s{i}.label", "kind": "Text",
                              "text": {"content": text, "typography_role": "label_large"},
                              "style": {"foreground": "on_surface"}}]})
    spec = {"id": name, "kind": "Rect",
            "style": {"width": width, "height": height, "corner_radius": height / 2, "background": "transparent",
                      "border_color": "outline", "border_width": 1, "padding": 1, "flex_direction": "horizontal"},
            "children": children}
    widget = Widget(window, spec=spec, theme=theme, x=x, y=y,
                    interactive={f"s{i}": "on_surface" for i in range(count)}, name=name)
    a11y.describe(widget.node, role="group")
    widget.multi = multi
    widget.selected = Signal(chosen)
    changes: list[Callable[[Any], Any]] = []
    widget.on_change = lambda fn: (changes.append(fn), lambda: changes.remove(fn) if fn in changes else None)[1]
    end = inner / 2
    ends = {0: (end, 0.0, 0.0, end), count - 1: (0.0, end, end, 0.0)}  # (top_left, top_right, bottom_right, bottom_left)

    def is_on(i: int) -> bool:
        value = widget.selected.get()
        return i in value if multi else value == i

    def shape() -> None:  # a style takes one radius, so set here, and after re-colouring
        for i, corners in ends.items():
            for node in (widget.part(f"s{i}"), widget.interaction(f"s{i}").clip):
                node.set(corner_radius=corners)

    def draw() -> None:
        value = widget.selected.get()
        stop = None if multi else (value if value is not None else 0)
        for i in range(count):
            on = is_on(i)
            widget.part(f"s{i}").set(fill=widget.color("secondary_container") if on else (0, 0, 0, 0),
                                     focusable=stop is None or i == stop, checked=on)
            widget.part(f"s{i}.check").set(visible=on, width=SEGMENT_CHECK if on else 0.0,
                                           margin_right=SEGMENT_GAP if on else 0.0)
            widget.part(f"s{i}.label").set(fill=widget.color("on_secondary_container" if on else "on_surface"))

    def change(value: Any, focus: Optional[int] = None) -> None:
        if value != widget.selected.get():
            widget.selected.set(value)
            for fn in list(changes):
                fn(value)
        if focus is not None:
            widget.part(f"s{focus}").focus()

    def press(i: int) -> None:
        if multi:
            value = widget.selected.get()
            change(value - {i} if i in value else value | {i})
        else:
            change(i)

    def on_key(event: Any, i: int) -> None:
        step = {"arrow_right": 1, "arrow_left": -1}.get(event.key)
        if step is None:
            return
        target = (i + step) % count
        if multi:
            widget.part(f"s{target}").focus()
        else:
            change(target, focus=target)

    for i, text in enumerate(labels):
        widget.on_click(lambda i=i: press(i), part=f"s{i}", role="checkbox" if multi else "radio")
        a11y.describe(widget.part(f"s{i}"), label=text)
        widget._undo.append(widget.view._listen(widget.part(f"s{i}"), "key_down", lambda e, i=i: on_key(e, i)))
    effect = Effect(draw)  # after `on_click`, which makes every segment focusable
    widget._undo.append(effect.dispose)
    shape()
    widget.after_theme(lambda: (shape(), draw()))
    return widget


def _segments_selected(selected: Any, multi: bool, count: int) -> Any:
    chosen = [] if selected is None else [selected] if isinstance(selected, int) else list(selected)
    for i in chosen:
        if not isinstance(i, int) or not 0 <= i < count:
            raise ValueError(f"selected={selected!r} is out of range for {count} segments")
    if multi:
        return frozenset(chosen)
    if len(chosen) > 1:
        raise ValueError(f"a single-select segmented button can't select {selected!r}; pass multi=True")
    return chosen[0] if chosen else None
