"""M37 Phase 3: the tree differ. Builds one expanded view spec with
`tre`'s `View` and with Tesserae's compiler, lays both out in same-sized
windows, and compares them node by node through 0.3.4's `get()`.

Used by `tests/test_tree_parity.py`; kept importable for poking at a
single view by hand.
"""

from __future__ import annotations

import tre

from tesserae import tokens
from tesserae.spec.build import build

SEED = (0x67, 0x50, 0xA4, 0xFF)
SIZE = (500, 400)

LAYOUT = ("layout_x", "layout_y", "layout_width", "layout_height")
PAINT = ("fill", "stroke_color", "stroke_width", "corner_radius", "opacity")
TEXT = ("text", "font_family", "font_size", "font_weight", "line_height")
#: Fields `tre` never had (M39): its builder rejects them, so its copy of
#: the spec goes without; they add no layout or paint the differ reads.
TESSERAE_ONLY = ("a11y", "interaction", "group")
#: Kinds Tesserae draws as MD3's controls since M40 (Q2: MD3's look, not
#: tre's legacy one), so they aren't compared.
CONTROLS = frozenset({"Checkbox", "RadioButton", "Switch", "Slider", "CircularProgress", "LinearProgress",
                      "LoadingIndicator", "TimePickerDial"})


def for_tre(spec, sizes=None):
    """`spec` without Tesserae-only fields, for `tre`'s builder. `sizes`
    (id -> width/height) gives text the content size Tesserae measures for
    it (M41), since `tre`'s text has none."""
    out = {k: v for k, v in spec.items() if k not in TESSERAE_ONLY}
    if sizes and spec.get("id") in sizes:
        out["style"] = {**sizes[spec["id"]], **(spec.get("style") or {})}
    if "children" in spec:
        out["children"] = [for_tre(child, sizes) for child in spec["children"] or []]
    return out


def _get(node, prop):
    try:
        value = node.get(prop)
    except Exception as exc:  # a property this kind doesn't have
        return ("n/a", type(exc).__name__)
    return round(value, 3) if isinstance(value, float) else value


def ids(spec):
    yield spec["id"], spec
    for child in spec.get("children") or []:
        yield from ids(child)


def _text_sizes(built, spec):
    sizes = {}
    for node_id, node_spec in ids(spec):
        if node_spec.get("kind") in ("Text", "Link"):
            style = node_spec.get("style") or {}
            node = built.nodes[node_id]
            sizes[node_id] = {d: node.get(d) for d in ("width", "height") if style.get(d) is None}
    return sizes


def build_both(spec, frames=None, stylesheet=None):
    probe = tre.Window(width=SIZE[0], height=SIZE[1])
    sizes = _text_sizes(build(probe, spec, scheme=tokens.color_scheme(SEED), stylesheet=stylesheet, frames=frames),
                        spec)
    view = tre.View(spec=for_tre(spec, sizes), theme_seed=SEED, **({"stylesheet_spec": stylesheet} if stylesheet else {}))
    if frames:
        for node_id, (rgba, w, h) in frames.items():
            view.node(node_id).push_frame(rgba, w, h)
    tre_window = tre.Window.from_view(view, width=SIZE[0], height=SIZE[1], title="tre")
    tre_window.advance(16)

    window = tre.Window(width=SIZE[0], height=SIZE[1])
    window.set_theme(SEED)
    # like a `Window.from_view` root: no padding, and an unsized root sized to its content
    window.root.set(padding_top=0, padding_right=0, padding_bottom=0, padding_left=0, align_items="flex_start")
    built = build(window, spec, scheme=tokens.color_scheme(SEED), stylesheet=stylesheet, frames=frames)
    window.root.add_child(built.root)
    window.advance(16)
    return view, built


def diff(spec, frames=None, stylesheet=None):
    """Every difference, as `(node_id, property, tre's value, Tesserae's)`."""
    view, built = build_both(spec, frames, stylesheet)
    out = []
    for node_id, node_spec in ids(spec):
        theirs, outer, inner = view.node(node_id), built.outer[node_id], built.nodes[node_id]
        kind = node_spec.get("kind")
        if kind in CONTROLS:
            continue  # MD3's controls, deliberately not tre's legacy drawing (M40 Q2)
        props = LAYOUT + PAINT
        if kind in ("Text", "Link", "TextField"):
            props = props + TEXT
        for prop in props:
            # On a TextField, tre's `fill` reads back its text colour, which
            # Tesserae's inner `text_input` carries; its background can't be read.
            ours_node = inner if (kind == "TextField" and (prop in TEXT or prop == "fill")) else outer
            a, b = _get(theirs, prop), _get(ours_node, prop)
            if isinstance(a, tuple) and a[:1] == ("n/a",):
                if prop == "text" and hasattr(theirs, "get_text"):
                    a = theirs.get_text()  # tre's legacy getter where get() doesn't reach
                else:
                    continue  # not readable on tre's side: nothing to compare
            if a != b:
                out.append((node_id, prop, a, b))
        elevation = _get(theirs, "elevation")
        if isinstance(elevation, (int, float)):
            expected = tokens.elevation_shadows(elevation)
            if _get(outer, "shadows") != expected:
                out.append((node_id, "shadows", expected, _get(outer, "shadows")))
    return out
