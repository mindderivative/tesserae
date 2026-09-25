"""M37 Phase 3: Tesserae's compiler builds the same tree as `tre`'s.

Every view below is built by `tre`'s `View` and by `tesserae.spec.build`
in same-sized windows and compared node by node (`tests/treediff.py`):
laid-out box, fill, border, corner radius, opacity, elevation (`tre`)
against `shadows` (Tesserae), and text and font. They must be identical.

The corpus:
- every one of the 67 fragments, called with ordinary parameters (the
  Image fragment with a real PNG);
- every view written inline in the test suite that `tre` itself accepts;
- the five example views, built from their files (includes and images);
- every `yaml` block in the docs and README that is a whole view.

**Not comparable, because `tre` can't read them back:** a Link's text and
font properties, and a TextField's background (`tre` reports its text
colour as `fill`). Everything else `get()` reaches is compared.
"""

import ast
import re
from pathlib import Path

import pytest
import tre
import yaml
from PIL import Image

import treediff
from tesserae.spec.expand import expand_components_to_spec
from tesserae.spec.load import build_view_spec

ROOT = Path(__file__).resolve().parent.parent
COMPONENTS = ROOT / "src/tesserae/spec/components"
FENCE = re.compile(r"^```ya?ml\n(.*?)^```", re.MULTILINE | re.DOTALL)
VALUES = {
    "background": "#6750A4", "checked": True, "corner_radius": 12, "day": "12", "fit": "cover",
    "headline": "Title", "height": 40, "hour": 3, "icon": "add", "label": "Label", "left_padding": 16,
    "minute": 30, "placeholder": "Search", "scrim_height": 300, "scrim_width": 400, "selected": True,
    "size": 40, "text": "Body", "title": "Title", "value": 0.5, "width": 120, "src": "pixel.png",
}


def _fragment_calls():
    for path in sorted(COMPONENTS.glob("*_Component.yaml")):
        name = path.name.removesuffix("_Component.yaml")
        params = (yaml.safe_load(path.read_text()) or {}).get("params", [])
        values = {k: VALUES[k] for k in params}
        if name == "SpinBox":
            values["value"] = "5"  # SpinBox shows its value as text, so it's a string
        view = {"id": "root", "kind": "Container", "style": {"width": 500, "height": 400},
                "children": [{"id": "w", "component": name, "with": values}]}
        yield f"fragment:{name}", yaml.safe_dump(view)


def _inline_test_views():
    for path in sorted((ROOT / "tests").glob("test_*.py")):
        if path.name == Path(__file__).name:
            continue
        strings = [n.value for n in ast.walk(ast.parse(path.read_text()))
                   if isinstance(n, ast.Constant) and isinstance(n.value, str) and "kind:" in n.value and "id:" in n.value]
        for i, text in enumerate(strings):
            yield f"{path.stem}:{i}", text


def _doc_views():
    for path in sorted([*(ROOT / "docs").glob("**/*.md"), ROOT / "README.md"]):
        for i, block in enumerate(FENCE.findall(path.read_text())):
            yield f"{path.relative_to(ROOT)}:{i}", block


def _accepted(key, text):
    """The expanded spec, or None if it doesn't expand or `tre` itself
    rejects it (the suite's deliberately broken views)."""
    try:
        spec = expand_components_to_spec(text)
    except Exception:
        return None
    if not isinstance(spec, dict) or "kind" not in spec or "id" not in spec:
        return None
    try:
        tre.View(spec=spec, theme_seed=treediff.SEED)
    except Exception:
        return None
    return spec


CORPUS = {}
for _key, _text in [*_fragment_calls(), *_inline_test_views(), *_doc_views()]:
    if _key.startswith("fragment:Image"):
        CORPUS[_key] = ("image", _text)
        continue
    _spec = _accepted(_key, _text)
    if _spec is not None:
        CORPUS[_key] = ("spec", _spec)
for _view in sorted((ROOT / "examples").glob("*/*_View.yaml")):
    CORPUS[f"example:{_view.parent.name}/{_view.name}"] = ("file", _view)


def test_the_corpus_is_broad():
    fragments = [k for k in CORPUS if k.startswith("fragment:")]
    assert len(fragments) == len(list(COMPONENTS.glob("*_Component.yaml"))) == 67
    assert sum(k.startswith("example:") for k in CORPUS) == 5
    assert sum(k.startswith("test_") for k in CORPUS) >= 30
    assert sum(k.startswith(("docs/", "README")) for k in CORPUS) >= 2


def _frames_dict(frames):
    return {node_id: (rgba, w, h) for node_id, rgba, w, h in frames}


@pytest.mark.parametrize("key", sorted(CORPUS))
def test_tesserae_builds_the_same_tree_as_tre(key, tmp_path):
    how, source = CORPUS[key]
    if how == "spec":
        differences = treediff.diff(source)
    else:
        if how == "image":
            Image.new("RGBA", (3, 2), (200, 30, 60, 255)).save(tmp_path / "pixel.png")
            view_file = tmp_path / "Pixel_View.yaml"
            view_file.write_text(source)
        else:
            view_file = source
        spec, frames, _ = build_view_spec(view_file)
        differences = treediff.diff(spec, frames=_frames_dict(frames))
    assert differences == []
