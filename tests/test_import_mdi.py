"""#216: `tools/import_mdi.py` and the MDI icons in the icon set."""

import importlib.util
import json
from pathlib import Path

import pytest

from tesserae import View, icons

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("import_mdi", ROOT / "tools" / "import_mdi.py")
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


def collection(**icons_):
    return {"width": 24, "height": 24, "aliases": {"cog-alias": {"parent": "cog"}},
            "icons": {name: {"body": body} for name, body in icons_.items()}}


PATH = '<path fill="currentColor" d="M1 1h2v2z"/>'


def test_names_become_snake_case_and_aliases_resolve():
    data = {**collection(), "icons": {"account-check": {"body": PATH}, "cog": {"body": PATH.replace("M1", "M9")}}}
    assert tool.collect(data, ["account-check", "cog-alias"]) == {"account_check": "M1 1h2v2z", "cog_alias": "M9 1h2v2z"}


def test_all_takes_every_single_path_icon_and_skips_the_rest():
    data = {**collection(), "icons": {"a": {"body": PATH}, "two": {"body": PATH + PATH}, "group": {"body": "<g>" + PATH + "</g>"}}}
    assert list(tool.collect(data, ["*"])) == ["a"]


def test_a_named_icon_that_is_not_one_path_is_refused_and_a_missing_one_named():
    data = {**collection(), "icons": {"two": {"body": PATH + PATH}}}
    with pytest.raises(ValueError, match="two: not a single <path>"):
        tool.collect(data, ["two"])
    with pytest.raises(ValueError, match="not in the collection: nope"):
        tool.collect(data, ["nope"])


def test_a_collection_that_is_not_24_square_is_refused():
    with pytest.raises(ValueError, match="not MDI's 24 x 24"):
        tool.collect({"width": 16, "height": 16, "icons": {}}, ["a"])


def test_a_bad_name_is_refused():
    with pytest.raises(ValueError, match="not an icon name"):
        tool.collect(collection(), ["Bad Name"])


def test_main_writes_and_keeps_what_was_there(tmp_path, capsys):
    src, out = tmp_path / "mdi.json", tmp_path / "o" / "mdi.json"
    src.write_text(json.dumps({**collection(), "icons": {"a-b": {"body": PATH}, "c": {"body": PATH}}}))
    assert tool.main([str(src), "--names", "a-b", "--out", str(out)]) == 0
    assert tool.main([str(src), "--names", "c", "--out", str(out)]) == 0
    assert set(json.loads(out.read_text())) == {"a_b", "c"}
    assert tool.main([str(src), "--names", "zzz", "--out", str(out)]) == 1 and "not in the collection" in capsys.readouterr().err


def test_the_bundled_mdi_icons_are_in_the_set_with_their_own_view_box():
    assert "account" in icons.ICONS and icons.icon_view_box("account") == icons.MDI_VIEW_BOX
    assert icons.icon_view_box("home") == icons.ICON_VIEW_BOX  # built in: Material Symbols, and it wins over MDI's home
    assert icons.icon_path("home").startswith("M240-200")


def test_every_curated_name_is_bundled():
    bundled = json.loads((ROOT / "src" / "tesserae" / "icon_data" / "mdi.json").read_text())
    missing = [n for n in tool.CURATED if n.replace("-", "_") not in icons.ICONS]
    assert not missing and len(bundled) >= 140


def test_an_mdi_icon_draws_in_its_24_box():
    page = {"id": "root", "kind": "Container", "style": {"width": 100, "height": 100},
            "children": [{"id": "i", "kind": "Icon", "icon": {"name": "plus"}, "style": {"width": 48, "height": 48, "foreground": "#000000"}}]}
    view = View(page, theme_seed=(103, 80, 164, 255))
    view.window.advance(16)
    assert tuple(view.node("i").get("view_box")) == icons.MDI_VIEW_BOX
    rgba, width, height = view.window.snapshot()
    inked = [(i // 4 % width, i // 4 // width) for i in range(3, len(rgba), 4) if rgba[i] > 128]
    xs, ys = [p[0] for p in inked], [p[1] for p in inked]
    assert 20 <= (max(xs) - min(xs) + 1) <= 48 and 20 <= (max(ys) - min(ys) + 1) <= 48  # fills its box: not drawn tiny in a 960 one
