"""The curated Material Symbols icons `kind: Icon` names, taken verbatim
from `tre`'s `engine-md3/src/icons.rs` at v0.3.4 (and three window
buttons drawn for Tesserae, 0.3.0) (`tre` hands its icon
data to the framework, D4). Each is an SVG path `d=` string in the
shared view box `0 -960 960 960`, drawn by a `tre` `path` node."""

from __future__ import annotations

import json
from pathlib import Path

__all__ = ["ICON_VIEW_BOX", "ICONS", "MDI_VIEW_BOX", "icon_path", "icon_view_box"]

#: Every icon's view box, `(min_x, min_y, width, height)`.
ICON_VIEW_BOX = (0.0, -960.0, 960.0, 960.0)
#: The view box of the Material Design Icons (Pictogrammers' MDI, Apache-2.0) from `icon_data/mdi.json`, which `tools/import_mdi.py` writes.
MDI_VIEW_BOX = (0.0, 0.0, 24.0, 24.0)

ICONS = {
    "home": "M240-200h120v-240h240v240h120v-360L480-740 240-560v360Zm-80 80v-480l320-240 320 240v480H520v-240h-80v240H160Zm320-350Z",
    "search": "M784-120 532-372q-30 24-69 38t-83 14q-109 0-184.5-75.5T120-580q0-109 75.5-184.5T380-840q109 0 184.5 75.5T640-580q0 44-14 83t-38 69l252 252-56 56ZM380-400q75 0 127.5-52.5T560-580q0-75-52.5-127.5T380-760q-75 0-127.5 52.5T200-580q0 75 52.5 127.5T380-400Z",
    "menu": "M120-240v-80h720v80H120Zm0-200v-80h720v80H120Zm0-200v-80h720v80H120Z",
    "close": "m256-200-56-56 224-224-224-224 56-56 224 224 224-224 56 56-224 224 224 224-56 56-224-224-224 224Z",
    "check": "M382-240 154-468l57-57 171 171 367-367 57 57-424 424Z",
    "arrow_back": "m313-440 224 224-57 56-320-320 320-320 57 56-224 224h487v80H313Z",
    "add": "M440-440H200v-80h240v-240h80v240h240v80H520v240h-80v-240Z",
    "settings": "m370-80-16-128q-13-5-24.5-12T307-235l-119 50L78-375l103-78q-1-7-1-13.5v-27q0-6.5 1-13.5L78-585l110-190 119 50q11-8 23-15t24-12l16-128h220l16 128q13 5 24.5 12t22.5 15l119-50 110 190-103 78q1 7 1 13.5v27q0 6.5-2 13.5l103 78-110 190-118-50q-11 8-23 15t-24 12L590-80H370Zm70-80h79l14-106q31-8 57.5-23.5T639-327l99 41 39-68-86-65q5-14 7-29.5t2-31.5q0-16-2-31.5t-7-29.5l86-65-39-68-99 42q-22-23-48.5-38.5T533-694l-13-106h-79l-14 106q-31 8-57.5 23.5T321-633l-99-41-39 68 86 64q-5 15-7 30t-2 32q0 16 2 31t7 30l-86 65 39 68 99-42q22 23 48.5 38.5T427-266l13 106Zm42-180q58 0 99-41t41-99q0-58-41-99t-99-41q-59 0-99.5 41T342-480q0 58 40.5 99t99.5 41Zm-2-140Z",
    "expand_more": "M480-345 240-585l56-56 184 184 184-184 56 56-240 240Z",
    "remove": "M200-440v-80h560v80H200Z",
    "arrow_forward": "M647-440H160v-80h487L423-744l57-56 320 320-320 320-57-56 224-224Z",
    "chevron_right": "M504-480 320-664l56-56 240 240-240 240-56-56 184-184Z",
    "visibility": "M480-320q75 0 127.5-52.5T660-500q0-75-52.5-127.5T480-680q-75 0-127.5 52.5T300-500q0 75 52.5 127.5T480-320Zm0-72q-45 0-76.5-31.5T372-500q0-45 31.5-76.5T480-608q45 0 76.5 31.5T588-500q0 45-31.5 76.5T480-392Zm0 192q-146 0-266-81.5T40-500q54-137 174-218.5T480-800q146 0 266 81.5T920-500q-54 137-174 218.5T480-200Zm0-300Zm0 220q113 0 207.5-59.5T832-500q-50-101-144.5-160.5T480-720q-113 0-207.5 59.5T128-500q50 101 144.5 160.5T480-280Z",
    "visibility_off": "m644-428-58-58q9-47-27-88t-93-32l-58-58q17-8 34.5-12t37.5-4q75 0 127.5 52.5T660-500q0 20-4 37.5T644-428Zm128 126-58-56q38-29 67.5-63.5T832-500q-50-101-143.5-160.5T480-720q-29 0-57 4t-55 12l-62-62q41-17 84-25.5t90-8.5q151 0 269 83.5T920-500q-23 59-60.5 109.5T772-302Zm20 246L624-222q-35 11-70.5 16.5T480-200q-151 0-269-83.5T40-500q21-53 53-98.5t73-81.5L56-792l56-56 736 736-56 56ZM222-624q-29 26-53 57t-41 67q50 101 143.5 160.5T480-280q20 0 39-2.5t39-5.5l-36-38q-11 3-21 4.5t-21 1.5q-75 0-127.5-52.5T300-500q0-11 1.5-21t4.5-21l-84-82Zm319 93Zm-151 75Z",
    "error": "M480-280q17 0 28.5-11.5T520-320q0-17-11.5-28.5T480-360q-17 0-28.5 11.5T440-320q0 17 11.5 28.5T480-280Zm-40-160h80v-240h-80v240Zm40 360q-83 0-156-31.5T197-197q-54-54-85.5-127T80-480q0-83 31.5-156T197-763q54-54 127-85.5T480-880q83 0 156 31.5T763-763q54 54 85.5 127T880-480q0 83-31.5 156T763-197q-54 54-127 85.5T480-80Zm0-80q134 0 227-93t93-227q0-134-93-227t-227-93q-134 0-227 93t-93 227q0 134 93 227t227 93Zm0-320Z",
    # 0.3.0 M3: a title bar's window buttons. Not Material Symbols (its set
    # has none for these): drawn for Tesserae in the same view box and the
    # same 80-unit stroke, a hole cut by the opposite winding.
    "window_minimize": "M240-440v-80h480v80H240Z",
    "window_maximize": "M200-200v-560h560v560H200Zm80-80h400v-400H280v400Z",
    "window_restore": "M160-160v-480h480v480H160Zm80-80h320v-320H240v320Zm480-160v-320H400v-80h400v400h-80Z",
}


def _bundled(folder: Path = Path(__file__).parent / "icon_data", file: str = "material_symbols.json") -> dict[str, str]:
    """The icons in `folder/file`, if there is one: Material Symbols from `tools/import_material_symbols.py`, or MDI from `tools/import_mdi.py`."""
    path = folder / file
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def _merge(bundled: dict[str, str], built_in: dict[str, str]) -> dict[str, str]:
    """The set: an icon built in above wins over a bundled one of the same name."""
    return {**bundled, **built_in}


_SYMBOLS = _merge(_bundled(), ICONS)
_MDI = {name: data for name, data in _bundled(Path(__file__).parent / "icon_data", "mdi.json").items() if name not in _SYMBOLS}
#: Every icon name and its path data: the ones built in, then Material Symbols added by the importer, then MDI (a name in an earlier set wins).
ICONS = {**_MDI, **_SYMBOLS}


def icon_path(name: str) -> str | None:
    """The path data for `name`, or `None` if there's no such icon."""
    return ICONS.get(name)


def icon_view_box(name: str) -> tuple[float, float, float, float]:
    """The view box `name`'s path is drawn in: MDI's 24 x 24 for an MDI icon, Material Symbols' otherwise."""
    return MDI_VIEW_BOX if name in _MDI else ICON_VIEW_BOX
