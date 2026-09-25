"""M29 Phase 2: Tesserae decodes image files itself and hands `tre` only
pixels -- straight-alpha RGBA8 bytes plus their pixel size, the exact
contract `tre`'s `Window.add_image_from_bytes` (M82) and `Node.push_frame`
take. Per the user's own rule, `tre` gets specs and bytes, never a file.

Pillow does the decoding. `.convert("RGBA")` gives straight (not
premultiplied) alpha, matching what `tre`'s own `image::open(...)
.to_rgba8()` produced when it decoded files itself. Like `tre`, this
applies no EXIF orientation and takes an animated image's first frame.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

__all__ = ["decode_image"]


def decode_image(path: str | Path) -> tuple[bytes, int, int]:
    """Decodes the image at `path` to `(rgba, pixel_width, pixel_height)`.

    Raises `OSError` naming `path` if the file can't be read or decoded
    -- the same exception type `tre`'s own `add_image` raised.
    """
    try:
        with Image.open(path) as img:
            rgba = img.convert("RGBA")
    except (OSError, ValueError) as exc:
        raise OSError(f"cannot decode image {str(path)!r}: {exc}") from exc
    return rgba.tobytes(), rgba.width, rgba.height
