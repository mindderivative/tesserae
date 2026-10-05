"""An SVG document for an `svg` node: its text, and the raster pictures it refers to, decoded.

The engine draws an SVG itself (shapes, gradients, text, clips, masks), but decodes no image format, so the
`<image href="...">` pictures in a document (PNG, JPEG, GIF, WebP) are Tesserae's to decode, as for `kind: Image`:
Pillow to straight-alpha RGBA, a side of at most 8192, keyed by the `href` exactly as the document writes it. A
file is found relative to the SVG file (inside the view's folder: no absolute path, no `..` out of it). A
`data:` URL holding a raster is decoded and its `href` rewritten to a key of its own, since the engine does not look
at those; a nested SVG `data:` URL, and a `http:` or other address, are left as they are (the engine draws the first
and never opens the others). A picture the document names that can't be found or decoded is an error here, not a
silently empty spot.
"""

from __future__ import annotations

import base64
import gzip
import io
import re
from pathlib import Path
from typing import Any, Optional
from urllib.parse import unquote_to_bytes

from PIL import Image

from tesserae.spec.expand import ComponentError

__all__ = ["MAX_SIDE", "load_svg"]

#: The longest side of a picture the engine takes.
MAX_SIDE = 8192
_TAG = re.compile(r"<image\b[^>]*>", re.IGNORECASE | re.DOTALL)
_HREF = re.compile(r"""(\s(?:xlink:)?href\s*=\s*)(["'])(.*?)\2""", re.IGNORECASE | re.DOTALL)
_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")

#: `(rgba, pixel_width, pixel_height)`
Pixels = tuple[bytes, int, int]


def _text(source: bytes | str, where: str) -> str:
    if isinstance(source, str):
        return source
    if source[:2] == b"\x1f\x8b":  # an `.svgz`
        try:
            source = gzip.decompress(source)
        except OSError as exc:
            raise ComponentError(f"{where}: not a valid gzip-compressed SVG: {exc}") from exc
    try:
        return source.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ComponentError(f"{where}: an SVG is UTF-8 text: {exc}") from exc


def _pixels(image: "Image.Image", where: str) -> Pixels:
    rgba = image.convert("RGBA")
    if not (0 < rgba.width <= MAX_SIDE and 0 < rgba.height <= MAX_SIDE):
        raise ComponentError(f"{where}: a picture is at most {MAX_SIDE} pixels on a side, got {rgba.width}x{rgba.height}")
    return rgba.tobytes(), rgba.width, rgba.height


def _data_url(href: str, where: str) -> Optional[Pixels]:
    """The pixels of a `data:image/...` URL; `None` for a nested SVG or anything that isn't a raster."""
    header, _, body = href[5:].partition(",")
    kind = header.split(";")[0].strip().lower()
    if not kind.startswith("image/") or "svg" in kind:
        return None
    data = base64.b64decode(body) if ";base64" in header.lower() else unquote_to_bytes(body)
    try:
        with Image.open(io.BytesIO(data)) as picture:
            return _pixels(picture, where)
    except (OSError, ValueError) as exc:
        raise ComponentError(f"{where}: cannot decode the picture in a data: URL: {exc}") from exc


def _file(href: str, svg_dir: Path, root: Path, where: str) -> tuple[Path, Pixels]:
    if Path(href).is_absolute():
        raise ComponentError(f"{where}: {href!r} must be a relative path")
    try:
        found = (svg_dir / href).resolve(strict=True)
        canon_root = root.resolve(strict=True)
    except OSError as exc:
        raise ComponentError(f"{where}: cannot read {svg_dir / href}: {exc}") from exc
    if not found.is_relative_to(canon_root):
        raise ComponentError(f"{where}: {href!r} is outside the view's folder {canon_root}")
    try:
        with Image.open(found) as picture:
            return found, _pixels(picture, where)
    except (OSError, ValueError) as exc:
        raise ComponentError(f"{where}: cannot decode {found}: {exc}") from exc


def load_svg(source: bytes | str, base_dir: Optional[Path], node_id: str, deps: set[Path],
             svg_dir: Optional[Path] = None) -> dict[str, Any]:
    """`{"content": <document text>, "images": {href: (rgba, width, height)}}` for `source`.

    `base_dir` is the view's folder, which a picture must stay in; `svg_dir` is where the document's own relative
    paths start (its file's folder; the view's folder for an inline document). Each file read is added to `deps`."""
    where = f"widget {node_id!r}: svg"
    text = _text(source, where)
    images: dict[str, Pixels] = {}
    counter = 0

    def rewrite(tag: re.Match[str]) -> str:
        nonlocal counter

        def href(match: re.Match[str]) -> str:
            nonlocal counter
            value = match.group(3)
            if value.startswith("#") or value == "":
                return match.group(0)
            if value[:5].lower() == "data:":
                pixels = _data_url(value, f"{where} <image>")
                if pixels is None:
                    return match.group(0)  # a nested SVG: the engine draws it
                counter += 1
                key = f"tesserae-picture-{counter}"
                images[key] = pixels
                return f"{match.group(1)}{match.group(2)}{key}{match.group(2)}"
            if _SCHEME.match(value):
                return match.group(0)  # an address: the engine never opens one, so it is not drawn
            if value not in images:
                if base_dir is None or svg_dir is None:
                    raise ComponentError(f"{where}: <image href={value!r}> has no folder to be found in")
                path, pixels = _file(value, svg_dir, base_dir, f"{where} <image href={value!r}>")
                deps.add(path)
                images[value] = pixels
            return match.group(0)

        return _HREF.sub(href, tag.group(0), count=1)

    return {"content": _TAG.sub(rewrite, text), "images": images}
