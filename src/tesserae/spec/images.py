"""M29 Phase 2: every `kind: Image` node's `image.src:` is taken out of
the spec before `tre` sees it, decoded by Tesserae, and pushed onto the
built node with `Node.push_frame`. `tre` builds a `kind: Image` with no
`src:` as a blank image that keeps its `fit:` (valid since `tre` M75),
so the pushed pixels display exactly as a `tre`-loaded file did.

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

__all__ = ["Frame", "extract_images", "push_frames"]

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


def _extract(node: Any, base_dir: Path | None, frames: list[Frame]) -> Any:
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
        try:
            rgba, width, height = decode_image(path)
        except OSError as exc:
            raise ComponentError(f"widget {node_id!r}: {exc}") from exc
        frames.append((node_id, rgba, width, height))
        out["image"] = {k: v for k, v in image.items() if k != "src"}
    children = node.get("children")
    if isinstance(children, list):
        out["children"] = [_extract(child, base_dir, frames) for child in children]
    return out


def extract_images(spec: Any, base_dir: Path | None) -> tuple[Any, list[Frame]]:
    """Returns `spec` with every `kind: Image`'s `image.src:` removed,
    plus one decoded `Frame` per image removed. `spec` itself is not
    modified."""
    frames: list[Frame] = []
    return _extract(spec, base_dir, frames), frames


def push_frames(owner: Any, frames: list[Frame]) -> None:
    """Pushes each decoded frame onto its node. `owner` is whatever
    `tre` object has `node(id)` -- a `View` or a `Component`."""
    for node_id, rgba, width, height in frames:
        owner.node(node_id).push_frame(rgba, width, height)
