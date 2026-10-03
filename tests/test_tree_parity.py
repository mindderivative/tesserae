"""M37 Phase 3: Tesserae's compiler builds the same tree as `tre`'s.

Every view below is built by `tre`'s `View` and by `tesserae.spec.build`
in same-sized windows and compared node by node (`tests/treediff.py`):
laid-out box, fill, border, corner radius, opacity, elevation (`tre`)
against `shadows` (Tesserae), and text and font. They must be identical.

The corpus:
- every fragment `tre` 0.3.4 can build, called with ordinary parameters
  (the Image fragment with a real PNG; `items:` per fragment): 67 at M43,
  76 of 77 since (`Tabs`' `width: "100%"` divider is beyond 0.3.4);
- every view written inline in the test suite that `tre` itself accepts;
- the example views, built from their files (includes and images);
- every `yaml` block in the docs and README that is a whole view.

**Not comparable, because `tre` can't read them back:** a Link's text and
font properties, and a TextField's background (`tre` reports its text
colour as `fill`). Everything else `get()` reaches is compared.

M43: each case is recorded on 0.3.4 (`tests/reference.py`) -- the expanded
spec as `tre` was given it, any image frames, and `tre`'s side
(`treediff.tre_dump`) -- and Tesserae's compiler is compared with the
recording, since 0.3.5 has no `View`. The corpus is the recorded one.
"""

import ast
import base64
import re
from pathlib import Path

import pytest
import tre
import yaml
from PIL import Image

import reference
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
    "item_width": 120,
}
#: `items:` for the fragments that repeat one (M56): each item fragment's own params.
ITEMS = {
    "Tabs": [{"label": "One"}, {"label": "Two", "selected": True}],
    "Menu": [{"label": "One"}, {"label": "Two"}],
    "ButtonGroup": [{"label": "One"}, {"label": "Two"}],
    "NavigationRail": [{"label": "One", "icon": "home"}, {"label": "Two", "icon": "search"}],
    "NavigationDrawer": [{"label": "One", "icon": "home"}, {"label": "Two", "icon": "search"}],
}

@pytest.fixture(autouse=True)
def _the_engines_own_names(monkeypatch):
    """These tests compare Tesserae with answers recorded from the engine, in the engine's own layout names."""
    from tesserae.spec import layout

    monkeypatch.setattr(layout, "LEGACY_ENGINE_NAMES", True)


def _fragment_calls():
    for path in sorted(COMPONENTS.glob("*_Component.yaml")):
        name = path.name.removesuffix("_Component.yaml")
        params = (yaml.safe_load(path.read_text()) or {}).get("params", [])
        # a `{name: default}` param (M55) keeps its default; `items` is the fragment's own
        values = {k: ITEMS[name] if k == "items" else VALUES[k] for k in params if not isinstance(k, dict)}
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
        tre.View(spec=treediff.for_tre(spec), theme_seed=treediff.SEED)  # without Tesserae's own keys
    except Exception:
        return None
    return spec


def _corpus():
    """Built with `tre` (it decides which views it accepts): recording only.
    A key recorded before keeps the case it was recorded with (its spec
    and frames), so `tre` is asked the same question and gives the same
    answer; only keys new to the sources are added. (Keys are positions
    -- a doc's third block, say -- so rebuilding one from edited files
    would quietly give an old key a new question.)"""
    before = reference.previous(__name__)
    corpus = {}
    for key in before.get("corpus", []):
        case = before.get(f"test_tesserae_builds_the_same_tree_as_tre[{key}]#1")
        if case is not None:
            corpus[key] = ("recorded", case)
    for key, text in [*_fragment_calls(), *_inline_test_views(), *_doc_views()]:
        if key in corpus:
            continue
        if key.startswith("fragment:Image"):
            corpus[key] = ("image", text)
            continue
        spec = _accepted(key, text)
        if spec is not None:
            corpus[key] = ("spec", spec)
    for view in sorted((ROOT / "examples").glob("*/*_View.yaml")):
        corpus.setdefault(f"example:{view.parent.name}/{view.name}", ("file", view))
    return corpus


CORPUS = _corpus() if reference.RECORDING else {}
KEYS = reference.answer("corpus", lambda: sorted(CORPUS), __name__)


def test_the_corpus_is_broad():
    fragments = [k for k in KEYS if k.startswith("fragment:")]
    assert len(fragments) >= 67  # every fragment tre 0.3.4 builds, when recorded (67 at M43)
    assert sum(k.startswith("example:") for k in KEYS) >= 5  # every example view, when recorded (5 at M43)
    assert sum(k.startswith("test_") for k in KEYS) >= 30
    assert sum(k.startswith(("docs/", "README")) for k in KEYS) >= 2


def _without_cascade(spec):
    """`spec` without the theme-components tag (M57): that cascade is
    Tesserae's own (`tests/test_theme_components.py`), and every case
    recorded before it has none, so the corpus compares the compiler
    alone."""
    out = {k: v for k, v in spec.items() if k != "component_of"}
    if "children" in spec:
        out["children"] = [_without_cascade(child) for child in spec["children"] or []]
    return out


def _case(key, tmp_path):
    """One recorded case: the spec, its frames (base64), and `tre`'s side."""
    how, source = CORPUS[key]
    frames = None
    if how == "recorded":  # asked again exactly as before
        spec = source["spec"]
        frames = {k: (base64.b64decode(b64), w, h) for k, (b64, w, h) in source["frames"].items()} or None
    elif how == "spec":
        spec = source
    else:
        if how == "image":
            Image.new("RGBA", (3, 2), (200, 30, 60, 255)).save(tmp_path / "pixel.png")
            view_file = tmp_path / "Pixel_View.yaml"
            view_file.write_text(source)
        else:
            view_file = source
        spec, raw, _ = build_view_spec(view_file)
        frames = {node_id: (rgba, w, h) for node_id, rgba, w, h in raw}
    if how != "recorded":
        spec = _without_cascade(spec)
    return {"spec": spec, "tre": treediff.tre_dump(spec, frames=frames),
            "frames": {k: (base64.b64encode(rgba).decode(), w, h) for k, (rgba, w, h) in (frames or {}).items()}}


@pytest.mark.parametrize("key", KEYS)
def test_tesserae_builds_the_same_tree_as_tre(key, tmp_path):
    case = reference.tre(lambda: _case(key, tmp_path))
    frames = {k: (base64.b64decode(b64), w, h) for k, (b64, w, h) in case["frames"].items()} or None
    assert treediff.diff(case["spec"], frames=frames, theirs=case["tre"]) == []
