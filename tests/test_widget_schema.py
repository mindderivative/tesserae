"""#275: the editor schemas of the current language. Every view of the repository validates against the widget schema (with the project's own views in it, as
`tesserae schema --project` writes it), every stylesheet of rules against the stylesheet schema, and the mistakes an editor should flag are flagged."""

import json
import sys
from pathlib import Path

import jsonschema
import pytest
import yaml

from tesserae import cli
from tesserae.spec.rules import is_rule_sheet

ROOT = Path(__file__).resolve().parent.parent
SCHEMAS = ROOT / "src" / "tesserae" / "schema"
WIDGET = json.loads((SCHEMAS / "tesserae-widget-schema.json").read_text(encoding="utf-8"))
STYLESHEET = json.loads((SCHEMAS / "tesserae-stylesheet-schema.json").read_text(encoding="utf-8"))


def _load(path):
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return None
    return data if isinstance(data, dict) else None


def _view_files():
    """Each view file of the current language, with the folder whose views it can call: its example project, or the shipped ones alone."""
    for path in sorted([*(ROOT / "src").rglob("*_View.yaml"), *(ROOT / "examples").rglob("*_View.yaml")]):
        data = _load(path)
        if data is not None and "widget" in data:
            project = next((p for p in path.parents if (p / "app.py").is_file()), None) if "examples" in path.parts else None
            yield pytest.param(path, project, data, id=path.relative_to(ROOT).as_posix())


def _rule_sheets():
    for path in sorted([*(ROOT / "src").rglob("*_Stylesheet.yaml"), *(ROOT / "examples").rglob("*_Stylesheet.yaml")]):
        data = _load(path)
        if data is not None and is_rule_sheet(data):  # the older `kind:` sheets (the fragments') have the theme schema
            yield pytest.param(path, data, id=path.relative_to(ROOT).as_posix())


def _validator_for(project):
    schema = cli.project_schema_data(project) if project is not None else WIDGET
    return jsonschema.Draft7Validator(schema)


def _problems(validator, data):
    return sorted(f"{'/'.join(map(str, e.absolute_path)) or '(root)'}: {e.message[:110]}" for e in validator.iter_errors(data))


def test_there_are_views_and_stylesheets_to_check():
    assert len(list(_view_files())) > 80 and len(list(_rule_sheets())) > 40


@pytest.mark.parametrize("path, project, data", list(_view_files()))
def test_every_view_validates(path, project, data):
    assert not _problems(_validator_for(project), data)


@pytest.mark.parametrize("path, data", list(_rule_sheets()))
def test_every_stylesheet_of_rules_validates(path, data):
    assert not _problems(jsonschema.Draft7Validator(STYLESHEET), data)


def _flagged(data, project=None):
    return _problems(_validator_for(project), data)


def test_a_misspelt_style_field_is_flagged_and_a_real_one_is_not():
    assert _flagged({"widget": "Container", "style": {"foregorund": "red"}})
    assert not _flagged({"widget": "Container", "style": {"width": "{{ w }}", "height": "50%", "background": "surface", "x": "10%"}})


def test_a_style_value_of_the_wrong_kind_is_flagged():
    assert _flagged({"widget": "Container", "style": {"flex_direction": "diagonal"}})
    assert _flagged({"widget": "Container", "style": {"corner_radius": [1]}})


def test_a_misspelt_widget_and_a_misspelt_property_are_flagged():
    assert _flagged({"widget": "Buton", "label": "x"})
    assert _flagged({"widget": "Button", "lable": "x"})  # a shipped view: its params are known
    assert not _flagged({"widget": "Button", "label": "x", "variant": "outlined"})


def test_a_shipped_view_with_a_wrong_choice_is_flagged():
    assert _flagged({"widget": "Button", "label": "x", "variant": "gigantic"})


def test_a_rule_of_a_stylesheet_is_checked():
    check = lambda rule: _problems(jsonschema.Draft7Validator(STYLESHEET), {"styles": [rule]})  # noqa: E731
    assert not check({"widget": "Button", "variant": "tonal", "state": "hovered", "style": {"corner_radius": 8}})
    assert check({"widget": "Button", "state": "hoverd", "style": {"corner_radius": 8}})
    assert check({"widget": "Button", "style": {"corner_radiuss": 8}})
    assert check({"widget": "Button", "colour": "x", "style": {}})
    assert check({"widget": "Button"})  # a rule sets something


def test_a_project_view_is_a_widget_in_its_project_schema(tmp_path):
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Stat_View.yaml").write_text("params: {label: {type: str, required: true}, value: {type: int, min: 0}}\nwidget: Container\n")
    (tmp_path / "Views" / "Window_View.yaml").write_text("name: Window\nwidget: Window\ntitle: T\n")
    validator = _validator_for(tmp_path)
    assert not _flagged({"widget": "Stat", "label": "x", "value": 3}, tmp_path)
    assert _flagged({"widget": "Stat", "label": "x", "valuee": 3}, tmp_path)  # a misspelt param of the project's own view
    assert _flagged({"widget": "Stat", "label": "x", "value": -1}, tmp_path)  # a bound the view declares
    assert _flagged({"widget": "Stat"}, tmp_path)  # a required param
    assert not _problems(validator, yaml.safe_load((tmp_path / "Views" / "Window_View.yaml").read_text()))  # the window's file is the built-in Window
    assert _flagged({"widget": "Stat", "label": "x"}, None) and "Stat" not in WIDGET["properties"]["widget"]["enum"]  # the packaged schema does not know it


def test_a_view_of_a_project_that_shares_a_name_with_a_shipped_one_replaces_it(tmp_path):
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Button_View.yaml").write_text("params: {caption: str}\nwidget: Container\n")
    assert not _flagged({"widget": "Button", "caption": "x"}, tmp_path)
    assert _flagged({"widget": "Button", "label": "x"}, tmp_path)


def test_the_command_maps_views_to_the_widget_schema_and_the_project_one_on_request(tmp_path, capsys):
    assert cli.main(["schema", "--settings"]) == 0
    setting = json.loads(capsys.readouterr().out)["yaml.schemas"]
    assert setting[str(cli.SCHEMAS / "tesserae-widget-schema.json")] == ["**/*_View.yaml"]
    assert str(cli.SCHEMAS / cli.OLDER_VIEW_SCHEMA) not in setting  # the older syntax is for a file that names it in a comment
    assert setting[str(cli.SCHEMAS / "tesserae-stylesheet-schema.json")][0] == "**/*_Stylesheet.yaml"
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Mine_View.yaml").write_text("params: {x: int}\nwidget: Container\n")
    assert cli.main(["schema", "--settings", "--project", str(tmp_path)]) == 0
    setting = json.loads(capsys.readouterr().out)["yaml.schemas"]
    written = tmp_path / ".tesserae" / "tesserae-widget-schema.json"
    assert written.is_file() and setting[str(written)] == ["**/*_View.yaml"]
    assert "Mine" in json.loads(written.read_text())["properties"]["widget"]["enum"]


@pytest.mark.parametrize("flags", [[], ["--window"]])
def test_a_new_project_validates_against_its_own_schema(tmp_path, flags):
    assert cli.main(["new", "fresh", *flags, "--no-venv", "--dir", str(tmp_path)]) == 0
    validator = _validator_for(tmp_path / "fresh")
    for path in (tmp_path / "fresh" / "Views").glob("*_View.yaml"):
        assert not _problems(validator, yaml.safe_load(path.read_text())), path.name


def test_a_link_where_the_project_schema_goes_is_refused_not_followed(tmp_path):
    """The schema is written under the project's `.tesserae/`; a symbolic link there would write elsewhere."""
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    project = tmp_path / "project"
    (project / "Views").mkdir(parents=True)
    (project / ".tesserae").symlink_to(outside, target_is_directory=True)
    with pytest.raises(cli.CliError, match="symbolic link"):
        cli.project_schema(project)
    assert not list(outside.iterdir())
    (project / ".tesserae").unlink()
    (project / ".tesserae").mkdir()
    victim = tmp_path / "victim.json"
    victim.write_text("mine")
    (project / ".tesserae" / "tesserae-widget-schema.json").symlink_to(victim)
    with pytest.raises(cli.CliError, match="symbolic link"):
        cli.project_schema(project)
    assert victim.read_text() == "mine"


def test_the_project_schema_is_written_whole_and_leaves_no_temporary_file(tmp_path):
    (tmp_path / "Views").mkdir()
    path = cli.project_schema(tmp_path)
    assert json.loads(path.read_text())["title"] and not list(path.parent.glob("*.tmp"))
    assert cli.project_schema(tmp_path) == path  # again: it replaces its own file


def test_a_link_planted_at_the_old_temporary_name_is_not_written_through(tmp_path):
    """The temporary file is a new one with a name nobody could plant, not `<schema>.tmp`."""
    (tmp_path / "Views").mkdir()
    (tmp_path / ".tesserae").mkdir()
    victim = tmp_path / "victim.json"
    victim.write_text("mine")
    (tmp_path / ".tesserae" / "tesserae-widget-schema.json.tmp").symlink_to(victim)
    path = cli.project_schema(tmp_path)
    assert victim.read_text() == "mine" and json.loads(path.read_text())["title"]
    assert not path.is_symlink()
    if sys.platform != "win32":  # Windows has no permission bits to set: a file is 0o666 there
        assert path.stat().st_mode & 0o777 == 0o644


def test_a_failed_write_leaves_no_temporary_file(tmp_path, monkeypatch):
    (tmp_path / "Views").mkdir()
    monkeypatch.setattr(cli.os, "replace", lambda *a: (_ for _ in ()).throw(OSError("disk full")))
    with pytest.raises(OSError):
        cli.project_schema(tmp_path)
    assert not [p for p in (tmp_path / ".tesserae").iterdir() if p.name != ".gitkeep"]


def test_the_insets_and_sums_are_in_the_editor_schemas():
    ok = {"widget": "Container", "style": {"position": "absolute", "left": 8, "right": "10%", "bottom": -4, "top": "auto", "inset": 2,
                                           "width": "calc(100% - 16)", "height": "fit-content", "min_width": "50%"}}
    assert not _flagged(ok)
    for style in ({"width": "40px"}, {"width": -3}, {"right": "calc(100% - 4)"}, {"min_width": "calc(100% - 4)"}, {"inset": "-5%"}, {"width": "100%-16"}):
        assert _flagged({"widget": "Container", "style": style}), style
    rule = {"widget": "Rect", "style": {"right": 4, "width": "100% - 8"}}
    assert not _problems(jsonschema.Draft7Validator(STYLESHEET), {"styles": [rule]})


def test_the_anchor_fields_are_in_the_editor_schemas():
    ok = {"widget": "Rect", "style": {"anchor": "target", "placement": "top_end", "offset": [4, -4]}}
    assert not _flagged(ok)
    for style in ({"anchor": ""}, {"placement": "above_end"}, {"offset": [1]}, {"offset": "3"}):
        assert _flagged({"widget": "Rect", "style": style}), style
    assert not _flagged({"widget": "Overlay", "anchor": "t", "placement": "bottom_start", "offset": [0, 8], "flip": False})
    assert _flagged({"widget": "Overlay", "anchor": "t", "placement": "diagonal"})
