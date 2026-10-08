"""0.3.2 (#79): the YAML schemas for Red Hat's YAML language server.

`src/tesserae/schema/*.json` (and their copies on the docs site) are written by
`tools/generate_yaml_schema.py` from Tesserae's own code. Every YAML file in
the repository must validate against the schema for its kind, the mistakes an
editor should flag must not, the committed files must be what the generator
writes (apart from the layout enums, which are `tre`'s and may grow without
Tesserae changing), and the layout enums they list must be ones `tre` accepts.
"""

import importlib.util
import json
from pathlib import Path

import jsonschema
import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
SCHEMAS = ROOT / "src" / "tesserae" / "schema"
SITE = ROOT / "docs" / "schema"
NAMES = {"view": "tesserae-yaml-schema.json",
         "theme": "tesserae-theme-schema.json", "component": "tesserae-component-schema.json",
         "style": "tesserae-style-schema.json"}


def _schema(kind: str) -> dict:
    return json.loads((SCHEMAS / NAMES[kind]).read_text(encoding="utf-8"))


def _validator(kind: str) -> jsonschema.Draft7Validator:
    return jsonschema.Draft7Validator(_schema(kind))


def _generator():
    spec = importlib.util.spec_from_file_location("generate_yaml_schema", ROOT / "tools" / "generate_yaml_schema.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _kind_of(path: Path, data) -> str | None:
    name = path.name
    if name.endswith("_View.yaml"):
        return "view"
    if name.endswith("_Component.yaml"):
        return "component"
    if name.endswith("_Style.yaml") and isinstance(data, dict) and "style" in data:
        return "style"
    if isinstance(data, dict) and "kind" not in data and {"styles", "colors", "seed", "typography", "components"} & set(data):
        return "theme"
    return None


def _yaml_files():
    for path in sorted([*(ROOT / "src").rglob("*.yaml"), *(ROOT / "examples").rglob("*.yaml"),
                        *(ROOT / "tests").rglob("*.yaml")]):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        kind = _kind_of(path, data)
        if kind is not None:
            yield pytest.param(path, kind, data, id=path.relative_to(ROOT).as_posix())


@pytest.mark.parametrize("kind", sorted(NAMES))
def test_each_schema_is_valid_draft_07_and_says_what_it_is(kind):
    schema = _schema(kind)
    jsonschema.Draft7Validator.check_schema(schema)
    assert schema["$schema"] == "http://json-schema.org/draft-07/schema#"
    assert schema["$id"] == "https://mindderivative.github.io/tesserae/schema/" + NAMES[kind]
    assert schema["title"] and schema["description"]


@pytest.mark.parametrize("path, kind, data", list(_yaml_files()))
def test_every_yaml_file_in_the_repository_validates(path, kind, data):
    errors = sorted(_validator(kind).iter_errors(data), key=lambda e: list(map(str, e.absolute_path)))
    assert not errors, "; ".join(f"{'/'.join(map(str, e.absolute_path)) or '(root)'}: {e.message[:120]}" for e in errors[:3])


def test_every_kind_of_file_has_files_to_check():
    assert {param.values[1] for param in _yaml_files()} == set(NAMES)


def _node(**extra):
    return {"id": "root", "kind": "Container", **extra}


GOOD = {
    "a plain container": _node(),
    "text with text_align": {"id": "t", "kind": "Text", "style": {"foreground": "#FFF"},
                             "text": {"content": "x", "font_family": "Roboto", "font_size": 14, "text_align": "center"}},
    "a theme role as a colour": _node(style={"background": "surface_container_high"}),
    "a colour that is no role": _node(style={"background": "oklch(60% 0.1 200)"}),
    "a user's own fragment": {"id": "c", "component": "MyOwnCard", "with": {"anything": 1}},
    "a TitleBar": {"id": "bar", "kind": "TitleBar", "title": "Notes", "icon": "home", "buttons": ["close"]},
    "a window handler": _node(handlers={"on_click": "window.close"}),
}
BAD = {
    "a misspelt style field": _node(style={"foregorund": "#FFF"}),
    "an unknown kind": {"id": "x", "kind": "Textt"},
    "a misspelt node key": _node(childrens=[]),
    "a wrong layout value": _node(style={"flex_direction": "diagonal"}),
    "a wrong percentage": _node(style={"width": "50 percent"}),
    "a misspelt handler": _node(handlers={"on_clik": "go"}),
    "a misspelt text key": {"id": "t", "kind": "Text", "text": {"contnet": "x"}},
    "a wrong text_align": {"id": "t", "kind": "Text", "text": {"content": "x", "text_align": "middle"}},
    "an unknown type role": {"id": "t", "kind": "Text", "text": {"typography_role": "body_huge"}},
    "an unknown parameter of a built-in fragment": {"id": "b", "component": "ButtonFilled", "with": {"labell": "x"}},
    "a window button that doesn't exist": {"id": "bar", "kind": "TitleBar", "buttons": ["help"]},
    "a wrong window_region": _node(window_region="dragg"),
    "a node with no kind, component or include": {"id": "x"},
    "a wrong accessibility role": _node(a11y={"role": "buton"}),
    "an unknown icon": {"id": "i", "kind": "Icon", "icon": {"name": "no_such_icon_xyz"}, "style": {"foreground": "#FFF"}},
}


@pytest.mark.parametrize("name", sorted(GOOD))
def test_a_good_view_is_accepted(name):
    assert not list(_validator("view").iter_errors(GOOD[name]))


@pytest.mark.parametrize("name", sorted(BAD))
def test_a_mistake_an_editor_should_flag_is_rejected(name):
    assert list(_validator("view").iter_errors(BAD[name])), f"{name} was accepted"


def test_a_fragment_may_use_its_parameters_where_a_view_may_not():
    node = {"id": "r", "kind": "Rect", "style": {"width": "{{ width }}", "foreground": {"if": "{{ on }}", "then": "primary", "else": "surface"}}}
    assert not list(_validator("component").iter_errors({**node, "params": ["width", {"on": False}]}))
    assert list(_validator("view").iter_errors(node))


def test_theme_files_reject_a_misspelt_key():
    assert not list(_validator("theme").iter_errors({"seed": "#6750A4", "styles": [{"kind": "Rect", "style": {"corner_radius": 4}}]}))
    assert list(_validator("theme").iter_errors({"styles": [{"kind": "Rect", "style": {"corner_radious": 4}}]}))


TRE_ENUMS = _generator().TRE_ENUMS


def _enum_values(node, found: list) -> list:
    if isinstance(node, dict):
        if "enum" in node:
            found.extend(node["enum"])
        for value in node.values():
            _enum_values(value, found)
    elif isinstance(node, list):
        for item in node:
            _enum_values(item, found)
    return found


def _without_tre_enums(schema: dict) -> dict:
    """The schema with the layout enums, which are `tre`'s, taken out."""
    schema = json.loads(json.dumps(schema))
    properties = schema.get("definitions", {}).get("style", {}).get("properties", {})
    for name in TRE_ENUMS:
        if name in properties:
            properties[name] = {"description": properties[name].get("description"), "<tre's values>": True}
    return schema


def test_the_committed_files_are_what_the_generator_writes():
    """Everything Tesserae owns must match; `tre`'s layout enums may be newer in `tre` than in the file."""
    generator = _generator()
    written = generator.schemas()
    for kind, name in NAMES.items():
        regenerated = json.loads(generator.render(written[name]))
        assert _without_tre_enums(regenerated) == _without_tre_enums(_schema(kind)), \
            f"{name} is out of date: run `python tools/generate_yaml_schema.py`"


def test_the_layout_enums_in_the_schema_are_ones_tre_accepts():
    generator = _generator()
    for kind in ("view", "component"):
        properties = _schema(kind)["definitions"]["style"]["properties"]
        for name in TRE_ENUMS:
            listed = [v for v in _enum_values(properties[name], []) if not str(v).startswith("{{")]
            assert listed and set(listed) <= set(generator._tre_values(name)), f"{kind}: {name}: {listed}"


def test_the_site_copies_are_the_shipped_ones():
    for name in NAMES.values():
        assert (SITE / name).read_text(encoding="utf-8") == (SCHEMAS / name).read_text(encoding="utf-8"), name


def test_every_style_field_is_in_exactly_one_group():
    """0.4.4 (#101): the reference and the schema show style fields in sections; a new field can't go ungrouped."""
    from tesserae.spec import cascade

    listed = [name for names in cascade.STYLE_GROUPS.values() for name in names]
    assert len(listed) == len(set(listed)), "a style field is in two groups"
    assert set(listed) == cascade.STYLE_FIELDS, (
        f"ungrouped: {sorted(cascade.STYLE_FIELDS - set(listed))}, not a field: {sorted(set(listed) - cascade.STYLE_FIELDS)}")
    schema = json.loads((ROOT / "src" / "tesserae" / "schema" / "tesserae-yaml-schema.json").read_text(encoding="utf-8"))
    properties = schema["definitions"]["style"]["properties"]
    assert {name: p["x-group"] for name, p in properties.items()} == cascade.STYLE_GROUP_OF
    assert all(f"({p['x-group']}.)" in p["description"] for p in properties.values())
