"""M29 Phase 2: every `kind: Image` node's `image.src:` is taken out of
the spec, decoded by Tesserae, and returned as frames the builder puts
into the `image` node (M37: `tre`'s `create("image", rgba=...)`). A
`kind: Image` with no `src:` is a blank image that keeps its `fit:`.

This covers hand-written views and the `Image` fragment alike, since it
runs on the fully expanded tree -- ids are already final (namespaced)
by then.

`src:` resolves with `tre`'s own rules (`engine-spec/src/build.rs`,
`resolve_image_src`), so a view that loaded before still loads: relative
to the top-level view's directory (an `include:`d file's images too, as
under `tre`, since includes are spliced into one tree), no absolute
paths, no `../` or symlink escapes. Failures raise `ComponentError`, a
`ValueError`, as `tre`'s own image errors were.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tesserae.images import decode_image
from tesserae.spec.expand import ComponentError

__all__ = ["Frame", "check_frame", "extract_images"]

#: `(node_id, rgba, pixel_width, pixel_height)` -- one decoded image,
#: waiting to be pushed onto its node once `tre` has built the view.
Frame = tuple[str, bytes, int, int]


def _resolve_src(base_dir: Path | None, src: str, node_id: str) -> Path:
    where = f"widget {node_id!r}: image.src: {src!r}"
    if base_dir is None:
        raise ComponentError(f"{where} has no base directory to resolve against")
    if Path(src).is_absolute():
        raise ComponentError(f"{where} must be a relative path")
    try:
        canon_base = base_dir.resolve(strict=True)
        canon_src = (base_dir / src).resolve(strict=True)
    except OSError as exc:
        raise ComponentError(f"{where}: cannot read {base_dir / src}: {exc}") from exc
    if not canon_src.is_relative_to(canon_base):
        raise ComponentError(f"{where} resolves outside the view directory {canon_base}")
    return canon_src


def _svg(node: dict[str, Any], base_dir: Path | None, deps: set[Path]) -> dict[str, Any]:
    """A `kind: Svg`'s `svg:` with its document read and the pictures in it decoded (`tesserae.spec.svg`)."""
    from tesserae.spec.svg import load_svg

    node_id = node.get("id")
    svg = node.get("svg")
    if not isinstance(node_id, str):
        raise ComponentError("a `kind: Svg` needs an `id:`")
    if not isinstance(svg, dict) or ("src" in svg) == ("content" in svg):
        raise ComponentError(f"widget {node_id!r}: svg takes `src:` (a file next to the view) or `content:` (the document), one of them")
    if "src" in svg:
        src = svg["src"]
        if not isinstance(src, str):
            raise ComponentError(f"widget {node_id!r}: svg.src must be a string path, got {src!r}")
        path = _resolve_src(base_dir, src, node_id).resolve()
        deps.add(path)
        try:
            source: bytes | str = path.read_bytes()
        except OSError as exc:
            raise ComponentError(f"widget {node_id!r}: cannot read {path}: {exc}") from exc
        return load_svg(source, base_dir, node_id, deps, svg_dir=path.parent)
    content = svg["content"]
    if not isinstance(content, (str, bytes)):
        raise ComponentError(f"widget {node_id!r}: svg.content must be the document's text, got {type(content).__name__}")
    return load_svg(content, base_dir, node_id, deps, svg_dir=base_dir)


def _cursor(node: dict[str, Any], base_dir: Path | None, deps: set[Path]) -> dict[str, Any]:
    """A node's `style.cursor: {src: file.png, hotspot: [x, y]}` with its picture decoded, as `tre.CursorImage` takes it."""
    node_id = str(node.get("id"))
    cursor = node["style"]["cursor"]
    src = cursor.get("src")
    if not isinstance(src, str):
        raise ComponentError(f"widget {node_id!r}: style.cursor.src must be a string path, got {src!r}")
    unknown = set(cursor) - {"src", "hotspot"}
    if unknown:
        raise ComponentError(f"widget {node_id!r}: style.cursor has no {sorted(unknown)} (it takes src and hotspot)")
    path = _resolve_src(base_dir, src, node_id)
    deps.add(path)
    try:
        rgba, width, height = decode_image(path)
    except OSError as exc:
        raise ComponentError(f"widget {node_id!r}: {exc}") from exc
    if not (1 <= width <= 256 and 1 <= height <= 256):
        raise ComponentError(f"widget {node_id!r}: a cursor picture is 1 to 256 pixels a side, {src!r} is {width}x{height}")
    hotspot = cursor.get("hotspot", [0, 0])
    if not (isinstance(hotspot, (list, tuple)) and len(hotspot) == 2):
        raise ComponentError(f"widget {node_id!r}: style.cursor.hotspot is [x, y], got {hotspot!r}")
    return {**node, "style": {**node["style"], "cursor": {
        "rgba": rgba, "width": width, "height": height, "hotspot": [int(hotspot[0]), int(hotspot[1])]}}}


def _extract(node: Any, base_dir: Path | None, frames: list[Frame], deps: set[Path]) -> Any:
    if not isinstance(node, dict):
        return node
    out = dict(node)
    image = node.get("image")
    if node.get("kind") == "Image" and isinstance(image, dict) and "src" in image:
        node_id = node.get("id")
        if not isinstance(node_id, str):
            raise ComponentError(f"a `kind: Image` with `image.src: {image['src']!r}` needs an `id:`")
        src = image["src"]
        if not isinstance(src, str):
            raise ComponentError(f"widget {node_id!r}: image.src must be a string path, got {src!r}")
        path = _resolve_src(base_dir, src, node_id)
        deps.add(path)
        try:
            rgba, width, height = decode_image(path)
        except OSError as exc:
            raise ComponentError(f"widget {node_id!r}: {exc}") from exc
        frames.append((node_id, rgba, width, height))
        out["image"] = {k: v for k, v in image.items() if k != "src"}
    style = node.get("style")
    if isinstance(style, dict) and isinstance(style.get("cursor"), dict) and "src" in style["cursor"]:
        out["style"] = _cursor(node, base_dir, deps)["style"]
    if node.get("kind") == "Svg":
        out["svg"] = _svg(node, base_dir, deps)
    children = node.get("children")
    if isinstance(children, list):
        out["children"] = [_extract(child, base_dir, frames, deps) for child in children]
    return out


def extract_images(
    spec: Any, base_dir: Path | None, *, dependencies: set[Path] | None = None
) -> tuple[Any, list[Frame]]:
    """Returns `spec` with every `kind: Image`'s `image.src:` removed,
    plus one decoded `Frame` per image removed. `spec` itself is not
    modified. If `dependencies` is given, each image file's resolved
    path is added to it."""
    frames: list[Frame] = []
    deps = dependencies if dependencies is not None else set()
    return _extract(spec, base_dir, frames, deps), frames


def check_frame(rgba: Any, width: Any, height: Any) -> tuple[bytes, int, int]:
    """A video frame for an Image node: `width*height*4` bytes of
    RGBA, and its size. Raises `ValueError` for bytes that don't match."""
    width, height = int(width), int(height)
    data = bytes(rgba)
    if len(data) != width * height * 4:
        raise ValueError(f"a {width}x{height} frame is {width * height * 4} bytes of RGBA, got {len(data)}")
    return data, width, height
