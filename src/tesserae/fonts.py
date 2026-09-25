"""M29 Phase 4: fonts. Tesserae reads a font file and hands `tre` the
bytes (`tre.register_font`, tre M86) -- `tre` never opens a font file,
per the user's own rule that `tre` gets specs and bytes, never files.

`tre` ships four faces and never discovers system fonts. A
`font_family` naming anything else silently falls back to a bundled
face, so Tesserae keeps track of which families are really available
and warns (`FontFallbackWarning`) about any a theme or view names that
isn't. It warns rather than raises because registering a font after a
view already exists is legitimate -- `tre` picks it up on the next
frame. Turn it into an error with
`warnings.filterwarnings("error", category=FontFallbackWarning)`.
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Iterable

import tre

__all__ = [
    "BUNDLED_FAMILIES",
    "FontFallbackWarning",
    "available_families",
    "check_font_families",
    "register_font",
]

#: The families of `tre`'s four vendored faces (Roboto Regular/Medium,
#: Noto Sans Arabic, Hack Nerd Font Mono), as `tre.register_font`
#: itself reports them -- checked against `tre`'s own
#: `crates/engine-render/assets/fonts/` at `d6c30ef`.
BUNDLED_FAMILIES = frozenset({"Roboto", "Noto Sans Arabic", "Hack Nerd Font Mono"})

_registered: set[str] = set()


class FontFallbackWarning(UserWarning):
    """A `font_family` names a family that isn't bundled with `tre` and
    hasn't been registered, so `tre` will draw a bundled face instead."""


def register_font(path: str | Path) -> list[str]:
    """Reads the font file at `path` and registers it with `tre`,
    process-wide. Returns the family names it contains -- the exact
    names to use as `font_family`. Registering the same file twice is
    harmless.

    Raises `OSError` if the file can't be read, and `ValueError` (from
    `tre`) if it contains no font faces.
    """
    path = Path(path)
    try:
        families = tre.register_font(path.read_bytes())
    except ValueError as exc:
        raise ValueError(f"{path}: {exc}") from exc
    _registered.update(families)
    return families


def available_families() -> frozenset[str]:
    """Every family `tre` can draw right now: its bundled ones plus any
    registered through `register_font`."""
    return BUNDLED_FAMILIES | frozenset(_registered)


def check_font_families(families: Iterable[str], source: str) -> None:
    """Warns once, naming `source`, about any of `families` that
    `tre` would silently replace with a bundled face."""
    missing = sorted(set(families) - available_families())
    if missing:
        warnings.warn(
            f"{source}: font_family {', '.join(map(repr, missing))} is not bundled or registered -- "
            f"tre will fall back to a bundled face. Register it first with "
            f"tesserae.register_font(path); available: {sorted(available_families())}",
            FontFallbackWarning,
            stacklevel=3,
        )
