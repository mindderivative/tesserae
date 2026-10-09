"""#216: `tools/import_material_symbols.py` turns a folder of Material Symbols SVGs into bundled icon data."""

import importlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("import_material_symbols", ROOT / "tools" / "import_material_symbols.py")
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)

SVG = '<svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 -960 960 960" width="24"><path d="{d}"/></svg>'


def write(folder, name, d="M0-80h80v80Z", box=None):
    text = SVG.format(d=d)
    (folder / name).write_text(text.replace("0 -960 960 960", box) if box else text)


def test_icons_are_read_by_name_whatever_the_file_suffix(tmp_path):
    write(tmp_path, "alarm_24px.svg", "M1 1\n  L2 2Z")
    write(tmp_path, "bolt_wght400_24px.svg")
    assert tool.collect(tmp_path) == {"alarm": "M1 1 L2 2Z", "bolt": "M0-80h80v80Z"}


def test_names_pick_some_and_a_missing_one_is_an_error(tmp_path):
    write(tmp_path, "alarm.svg")
    write(tmp_path, "bolt.svg")
    assert list(tool.collect(tmp_path, {"bolt"})) == ["bolt"]
    with pytest.raises(ValueError, match="no SVG file for: cloud"):
        tool.collect(tmp_path, {"alarm", "cloud"})


@pytest.mark.parametrize("name, kwargs, message", [
    ("Bad-Name.svg", {}, "an icon name is lower-case"), ("a.svg", {"box": "0 0 24 24"}, "the view box is 0 0 24 24"),
])
def test_a_file_that_is_not_a_symbol_says_why(tmp_path, name, kwargs, message):
    write(tmp_path, name, **kwargs)
    with pytest.raises(ValueError, match=message):
        tool.collect(tmp_path)


def test_a_file_with_two_paths_is_refused(tmp_path):
    (tmp_path / "a.svg").write_text('<svg viewBox="0 -960 960 960"><path d="M0 0"/><path d="M1 1"/></svg>')
    with pytest.raises(ValueError, match="expected one <path>, found 2"):
        tool.collect(tmp_path)


def test_main_writes_the_json_and_keeps_what_was_there(tmp_path, capsys):
    folder, out = tmp_path / "svg", tmp_path / "out" / "m.json"
    folder.mkdir()
    write(folder, "alarm.svg")
    assert tool.main([str(folder), "--out", str(out)]) == 0
    write(folder, "bolt.svg")
    assert tool.main([str(folder), "--names", "bolt", "--out", str(out)]) == 0
    assert set(json.loads(out.read_text())) == {"alarm", "bolt"}
    assert tool.main([str(folder), "--names", "nope", "--out", str(out)]) == 1
    assert "no SVG file for: nope" in capsys.readouterr().err


def test_bundled_icons_join_the_set_but_never_replace_a_built_in_one(tmp_path):
    import tesserae.icons as icons

    (tmp_path / "material_symbols.json").write_text(json.dumps({"alarm": "M0 0Z", "home": "M9 9Z"}))
    bundled = icons._bundled(tmp_path)
    assert bundled == {"alarm": "M0 0Z", "home": "M9 9Z"} and icons._bundled(tmp_path / "none") == {}
    merged = icons._merge(bundled, {"home": "built in"})
    assert merged == {"alarm": "M0 0Z", "home": "built in"}
