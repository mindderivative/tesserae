"""Rich text: a `Text` whose `text.runs:` are styled pieces of one text (tre 0.5.4's `spans`).

The engine styles ranges of a text, as UTF-8 byte offsets. A view lists the pieces instead and Tesserae works the
offsets out:

    text:
      runs:
        - "Sale: "
        - {text: "$12", strikethrough: true, color: on_surface_variant}
        - {text: "$9", weight: 700, color: error}
        - " ends Friday. "
        - {text: "Read the terms", link: terms}

A run is a string, or a mapping with its `text` and any of `color` (a theme role or a CSS colour), `weight`,
`italic`, `underline`, `strikethrough`, `font_size`, `font_family` and `link`. A run with a `link` is the theme's
`primary` and underlined unless it says otherwise: the engine styles nothing, and what the link means is for the
`on_link` handler to decide, from `event.href`.
"""

from __future__ import annotations

from typing import Any, Callable

__all__ = ["RUN_KEYS", "build", "measure", "spans_of"]

RGBA = tuple[int, int, int, int]

RUN_KEYS = ("text", "color", "weight", "italic", "underline", "strikethrough", "font_size", "font_family", "link")

Pieces = list[tuple[str, dict[str, Any]]]


def build(runs: Any, where: str, color: Callable[[Any], RGBA],
          link_color: RGBA) -> tuple[str, list[tuple[int, int, dict[str, Any]]], Pieces]:
    """`(content, spans, pieces)` for the list of `runs`: the text, its styled byte ranges, and each piece's text
    with its style (for measuring). Raises `ValueError`, naming `where`."""
    if not isinstance(runs, list) or not runs:
        raise ValueError(f"{where}: text.runs is a list of pieces of text, got {runs!r}")
    content: list[str] = []
    spans: list[tuple[int, int, dict[str, Any]]] = []
    pieces: Pieces = []
    offset = 0
    for index, run in enumerate(runs):
        name = f"{where}: text.runs[{index}]"
        item = {"text": run} if isinstance(run, str) else run
        if not isinstance(item, dict) or not isinstance(item.get("text"), str):
            raise ValueError(f"{name} is a string, or a mapping with `text:`, got {run!r}")
        unknown = set(item) - set(RUN_KEYS)
        if unknown:
            raise ValueError(f"{name}: unknown key(s) {sorted(unknown)}, expected {', '.join(RUN_KEYS)}")
        style: dict[str, Any] = {}
        if "link" in item:
            if not isinstance(item["link"], str) or not item["link"]:
                raise ValueError(f"{name}: link must be a non-empty string, got {item['link']!r}")
            style.update(link=item["link"], color=link_color, underline=True)  # the engine styles no link
        if "color" in item:
            style["color"] = color(item["color"])
        for key in ("weight", "font_size"):
            if key in item:
                try:
                    style[key] = float(item[key])
                except (TypeError, ValueError):
                    raise ValueError(f"{name}: {key} must be a number, got {item[key]!r}") from None
        for key in ("italic", "underline", "strikethrough"):
            if key in item:
                if not isinstance(item[key], bool):
                    raise ValueError(f"{name}: {key} must be true or false, got {item[key]!r}")
                style[key] = item[key]
        if "font_family" in item:
            style["font_family"] = str(item["font_family"])
        text = item["text"]
        size = len(text.encode("utf-8"))
        if style and size:
            spans.append((offset, offset + size, style))
        pieces.append((text, style))
        content.append(text)
        offset += size
    return "".join(content), spans, pieces


def spans_of(runs: Any, color: Callable[[Any], RGBA], link_color: RGBA,
             where: str = "text") -> tuple[str, list[tuple[int, int, dict[str, Any]]]]:
    """`(content, spans)` for `runs`, for a `text` node made in code: `node.set(text=content, spans=spans)`."""
    content, spans, _ = build(runs, where, color, link_color)
    return content, spans


def measure(window: Any, pieces: Pieces, base: dict[str, Any]) -> tuple[float, float]:
    """The `(width, height)` of the pieces on one line, each in its own style over the node's `base`
    (`font_family`, `font_size`, `font_weight`, `line_height`)."""
    width = height = 0.0
    for text, style in pieces:
        if not text:
            continue
        font = dict(font_family=style.get("font_family", base["font_family"]),
                    font_size=style.get("font_size", base["font_size"]),
                    font_weight=style.get("weight", base["font_weight"]),
                    font_style="italic" if style.get("italic") else "normal", line_height=base.get("line_height"))
        # the engine leaves a text's trailing spaces out of its width, so a piece is measured between two bars
        w, h = window.measure_text("|" + text + "|", **font)
        width += w - window.measure_text("||", **font)[0]
        height = max(height, h)
    return width, height
