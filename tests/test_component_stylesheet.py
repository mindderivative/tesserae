"""0.3.4 (#83): a component's look lives in its stylesheet, and an app's own fragments are found.

- Every built-in `<Name>_Component.yaml` is structure; its look is in
  `<Name>_Stylesheet.yaml`, a list of `{id: <part>, style: {...}}` rules whose
  values may be the component's `{{ parameters }}`.
- An app restyles a built-in component by putting its own `<Name>_Stylesheet.yaml`
  next to its views: field by field over the built-in's.
- A fragment next to the view (`MyCard_Component.yaml`) is found without a
  `component_dirs=`, and its own stylesheet is applied.
"""

from pathlib import Path

import pytest
import yaml

from tesserae.spec import expand_components_to_spec, load_view
from tesserae.spec.expand import ComponentError, _parts_of, expand_with_dependencies

BUILTIN = Path(__file__).resolve().parent.parent / "src" / "tesserae" / "spec" / "components"
SHEETS = sorted(BUILTIN.glob("*_Stylesheet.yaml"))
SEED = (0x67, 0x50, 0xA4, 0xFF)


def _node(spec, node_id):
    stack = [spec]
    while stack:
        node = stack.pop()
        if node.get("id") == node_id:
            return node
        stack.extend(node.get("children") or [])
    raise KeyError(node_id)


def _use(directory: Path, call: str) -> dict:
    view = directory / "Home_View.yaml"
    view.write_text(f"id: root\nkind: Container\nchildren:\n  - {call}\n")
    return expand_components_to_spec(view.read_text(), base_dir=directory)


def test_there_is_a_stylesheet_for_most_built_in_components():
    assert len(SHEETS) >= 70


@pytest.mark.parametrize("sheet", SHEETS, ids=lambda p: p.name)
def test_a_built_in_stylesheet_names_parts_its_component_has(sheet):
    name = sheet.name.removesuffix("_Stylesheet.yaml")
    fragment = yaml.safe_load((BUILTIN / f"{name}_Component.yaml").read_text(encoding="utf-8"))
    rules = yaml.safe_load(sheet.read_text(encoding="utf-8"))["styles"]
    assert {rule["id"] for rule in rules} <= _parts_of(fragment)
    assert all(set(rule) == {"id", "style"} for rule in rules)


@pytest.mark.parametrize("sheet", SHEETS, ids=lambda p: p.name)
def test_a_built_in_fragment_keeps_no_style_of_its_own(sheet):
    name = sheet.name.removesuffix("_Stylesheet.yaml")
    assert "style:" not in (BUILTIN / f"{name}_Component.yaml").read_text(encoding="utf-8")


def test_a_component_is_styled_by_its_stylesheet():
    spec = expand_components_to_spec("id: root\nkind: Container\nchildren:\n"
                                     "  - {id: b, component: ButtonFilled, with: {label: Go, width: 120, height: 40, corner_radius: 20}}\n")
    assert _node(spec, "b")["style"]["background"] == "primary"
    assert _node(spec, "b")["style"]["width"] == 120  # a parameter, filled in the stylesheet
    assert _node(spec, "b.label")["style"]["foreground"] == "on_primary"


def test_a_conditional_in_a_stylesheet_follows_the_parameters():
    def tab(selected):
        spec = expand_components_to_spec(f"id: root\nkind: Container\nchildren:\n"
                                         f"  - {{id: t, component: TabsItem, with: {{label: A, width: 90, selected: {selected}}}}}\n")
        return _node(spec, "t.label")["style"]["foreground"]

    assert (tab("true"), tab("false")) == ("primary", "on_surface_variant")


def test_an_apps_own_stylesheet_restyles_a_built_in_field_by_field(tmp_path):
    (tmp_path / "ButtonFilled_Stylesheet.yaml").write_text(
        "styles:\n  - {id: label, style: {foreground: tertiary}}\n  - {id: root, style: {background: secondary}}\n")
    spec = _use(tmp_path, "{id: b, component: ButtonFilled, with: {label: Go, width: 120, height: 40, corner_radius: 20}}")
    assert _node(spec, "b.label")["style"]["foreground"] == "tertiary"
    root = _node(spec, "b")["style"]
    assert root["background"] == "secondary"
    assert root["corner_radius"] == 20 and root["align_items"] == "center"  # the rest is the built-in's


def test_a_built_in_is_unchanged_by_a_stylesheet_for_another_component(tmp_path):
    (tmp_path / "ButtonText_Stylesheet.yaml").write_text("styles:\n  - {id: root, style: {background: error}}\n")
    spec = _use(tmp_path, "{id: b, component: ButtonFilled, with: {label: Go, width: 120, height: 40, corner_radius: 20}}")
    assert _node(spec, "b")["style"]["background"] == "primary"


def test_a_fragment_next_to_the_view_is_found_with_its_stylesheet(tmp_path):
    (tmp_path / "MyCard_Component.yaml").write_text(
        "params: [title, {tone: primary}]\nid: root\nkind: Rect\nchildren:\n  - {id: t, kind: Text, text: {content: \"{{ title }}\"}}\n")
    (tmp_path / "MyCard_Stylesheet.yaml").write_text(
        "styles:\n  - {id: root, style: {width: 200, background: \"{{ tone }}\"}}\n  - {id: t, style: {foreground: on_primary}}\n")
    spec = _use(tmp_path, "{id: c, component: MyCard, with: {title: Hi, tone: tertiary}}")
    assert _node(spec, "c")["style"] == {"width": 200, "background": "tertiary"}
    assert _node(spec, "c.t")["style"] == {"foreground": "on_primary"}


def test_the_fragments_own_style_wins_over_its_stylesheet(tmp_path):
    (tmp_path / "MyCard_Component.yaml").write_text("id: root\nkind: Rect\nstyle: {width: 50}\n")
    (tmp_path / "MyCard_Stylesheet.yaml").write_text("styles:\n  - {id: root, style: {width: 200, height: 10}}\n")
    spec = _use(tmp_path, "{id: c, component: MyCard}")
    assert _node(spec, "c")["style"] == {"width": 50, "height": 10}


def test_an_apps_fragment_that_shadows_a_built_in_does_not_get_the_built_ins_stylesheet(tmp_path):
    (tmp_path / "ButtonFilled_Component.yaml").write_text(
        "params: [label]\nid: root\nkind: Rect\nchildren:\n  - {id: label, kind: Text, text: {content: \"{{ label }}\"}}\n")
    spec = _use(tmp_path, "{id: b, component: ButtonFilled, with: {label: Go}}")
    assert "style" not in _node(spec, "b")


def test_a_stylesheet_for_a_part_the_component_lacks_is_an_error_naming_its_parts(tmp_path):
    (tmp_path / "ButtonFilled_Stylesheet.yaml").write_text("styles:\n  - {id: lable, style: {foreground: tertiary}}\n")
    with pytest.raises(ComponentError, match=r"lable.*its parts are \['label', 'root'\]"):
        _use(tmp_path, "{id: b, component: ButtonFilled, with: {label: Go, width: 1, height: 1, corner_radius: 1}}")


@pytest.mark.parametrize("text", ["styles: 3\n", "colors: {}\n", "styles:\n  - {id: root}\n",
                                  "styles:\n  - {style: {gap: 1}}\n", "styles:\n  - {id: root, style: {gap: 1}, kind: Rect}\n"])
def test_a_malformed_component_stylesheet_is_refused(tmp_path, text):
    (tmp_path / "ButtonFilled_Stylesheet.yaml").write_text(text)
    with pytest.raises(ComponentError, match="ButtonFilled_Stylesheet.yaml"):
        _use(tmp_path, "{id: b, component: ButtonFilled, with: {label: Go, width: 1, height: 1, corner_radius: 1}}")


def test_the_stylesheets_are_dependencies_so_hot_reload_watches_them(tmp_path):
    (tmp_path / "ButtonFilled_Stylesheet.yaml").write_text("styles:\n  - {id: root, style: {background: secondary}}\n")
    text = "id: root\nkind: Container\nchildren:\n  - {id: b, component: ButtonFilled, with: {label: Go, width: 1, height: 1, corner_radius: 1}}\n"
    _, deps = expand_with_dependencies(text, base_dir=tmp_path)
    assert (tmp_path / "ButtonFilled_Stylesheet.yaml").resolve() in deps
    assert (BUILTIN / "ButtonFilled_Stylesheet.yaml").resolve() in deps


def test_a_view_built_from_a_file_uses_the_apps_own_component_and_stylesheet(tmp_path):
    (tmp_path / "MyCard_Component.yaml").write_text("params: [title]\nid: root\nkind: Rect\nchildren:\n"
                                                     "  - {id: t, kind: Text, text: {content: \"{{ title }}\", typography_role: body_medium}}\n")
    (tmp_path / "MyCard_Stylesheet.yaml").write_text("styles:\n  - {id: root, style: {width: 200, height: 60, background: tertiary}}\n  - {id: t, style: {foreground: on_tertiary}}\n")
    view_file = tmp_path / "Home_View.yaml"
    view_file.write_text("id: root\nkind: Container\nchildren:\n  - {id: c, component: MyCard, with: {title: Hi}}\n")
    view = load_view(view_file, theme_seed=SEED)
    assert view.node("c").get("width") == 200.0
    assert view.node("c").get("fill") == view.theme.role("tertiary")
