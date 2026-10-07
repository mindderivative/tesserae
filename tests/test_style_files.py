"""M75 (#22): a node's `style:` can name a `*_Style.yaml` file instead of
being written inline -- read as `include:` is (relative to the file it's
in, confined to its folder, recorded for hot reload). A stylesheet or a
theme rule's `style:` can too. And the file conventions tell the kinds
apart: `*_Style.yaml` one node's style, `*_Stylesheet.yaml` a stylesheet,
`*_Theme.yaml` a theme; each loader refuses the others' names.
"""

import pytest
import yaml

from tesserae import View
from tesserae.spec import expand_components_to_spec
from tesserae.spec.expand import ComponentError
from tesserae.spec.load import build_view_spec, load_view
from tesserae.spec.themes import load_stylesheet, load_theme

SEED = (0x67, 0x50, 0xA4, 0xFF)
COUNTER = {"flex_direction": "vertical", "width": 240, "height": 120, "gap": 12, "padding": 16}


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data) if not isinstance(data, str) else data)
    return path


def _counter_view(tmp_path, style="counter_Style.yaml"):
    _write(tmp_path / "counter_Style.yaml", COUNTER)
    return _write(tmp_path / "Counter_View.yaml", {
        "id": "root", "kind": "Container", "style": style,
        "children": [{"id": "label", "kind": "Text", "text": {"content": "Count: 0", "font_family": "Roboto", "font_size": 20},
                      "style": {"width": 200, "height": 32, "foreground": "#FFFFFF"}}]})


def test_the_issues_example_reads_its_style_from_the_file(tmp_path):
    view_file = _counter_view(tmp_path)
    spec, _, deps = build_view_spec(view_file)
    assert spec["style"] == COUNTER and spec["children"][0]["style"]["width"] == 200  # inline still inline
    assert (tmp_path / "counter_Style.yaml").resolve() in deps  # watched for hot reload
    view = load_view(view_file, theme_seed=SEED)
    root = view.node("root")
    assert (root.get("flex_direction"), root.get("width"), root.get("gap")) == ("vertical", 240.0, 12.0)


def test_it_is_relative_to_the_file_its_in(tmp_path):
    _write(tmp_path / "parts" / "row_Style.yaml", {"height": 30, "background": "#000000"})
    _write(tmp_path / "parts" / "row.yaml", {"id": "row", "kind": "Rect", "style": "row_Style.yaml"})
    view_file = _write(tmp_path / "Home_View.yaml", {"id": "root", "kind": "Container", "style": {"width": 100},
                                                     "children": [{"include": "parts/row.yaml"}]})
    spec, _, deps = build_view_spec(view_file)
    assert spec["children"][0]["style"] == {"height": 30, "background": "#000000"}
    assert (tmp_path / "parts" / "row_Style.yaml").resolve() in deps


@pytest.mark.parametrize("style, message", [
    ("counter.yaml", r'widget "root": `style:` is a mapping of style fields or a `\*_Style.yaml` file, got \'counter.yaml\'$'),
    ("Brand_Theme.yaml", r"got 'Brand_Theme.yaml' \('Brand_Theme.yaml' is a theme\)"),
    ("Home_Stylesheet.yaml", r"is a stylesheet\)"),
])
def test_a_string_that_isnt_a_style_file_is_refused(tmp_path, style, message):
    with pytest.raises(ComponentError, match=message):
        build_view_spec(_counter_view(tmp_path, style))


def test_a_style_file_holds_a_mapping_and_stays_in_its_folder(tmp_path):
    _write(tmp_path / "list_Style.yaml", "- width\n- 10\n")
    with pytest.raises(ComponentError, match=r'widget "root": list_Style.yaml: a style file holds a mapping of style fields, got list'):
        build_view_spec(_counter_view(tmp_path, "list_Style.yaml"))
    _write(tmp_path.parent / "outside_Style.yaml", {"width": 1})
    with pytest.raises(ComponentError, match="escapes its base directory"):
        build_view_spec(_counter_view(tmp_path, "../outside_Style.yaml"))


def test_without_a_file_there_is_nothing_to_resolve_against():
    with pytest.raises(ComponentError, match="has no base directory"):
        expand_components_to_spec("id: root\nkind: Container\nstyle: counter_Style.yaml\n")


@pytest.mark.parametrize("fragment", [
    {"params": [], "id": "root", "kind": "Rect", "style": "chip_Style.yaml"},
    {"params": [], "id": "root", "kind": "Container", "children": [{"id": "dot", "kind": "Rect", "style": "dot_Style.yaml"}]},
])
def test_a_fragment_cant_name_a_style_file(tmp_path, fragment):
    _write(tmp_path / "Chip_Component.yaml", fragment)
    with pytest.raises(ComponentError, match=r"`include:` \(or a `style:` file\) is not supported inside a component fragment"):
        expand_components_to_spec("id: root\nkind: Container\nchildren:\n  - {id: c, component: Chip}\n",
                                  component_dirs=[tmp_path])


def test_a_stylesheet_and_a_theme_rule_can_name_a_style_file(tmp_path):
    _write(tmp_path / "styles" / "card_Style.yaml", {"corner_radius": 16, "padding": 12})
    sheet = load_stylesheet(_write(tmp_path / "styles" / "Home_Stylesheet.yaml", {"styles": [
        {"kind": "Rect", "class": "card", "style": "card_Style.yaml"}, {"kind": "Text", "style": {"opacity": 0.8}}]}))
    assert sheet["styles"][0]["style"] == {"corner_radius": 16, "padding": 12} and sheet["styles"][1]["style"] == {"opacity": 0.8}
    theme = load_theme(_write(tmp_path / "styles" / "Brand_Theme.yaml", {"seed": "#6750A4", "styles": [
        {"kind": "Rect", "style": "card_Style.yaml"}]}))
    assert theme["styles"][0]["style"]["corner_radius"] == 16
    with pytest.raises(ValueError, match=r"Bad_Stylesheet.yaml: a style rule: `style:` is a mapping"):
        load_stylesheet(_write(tmp_path / "Bad_Stylesheet.yaml", {"styles": [{"kind": "Rect", "style": "card.yaml"}]}))


def test_a_stylesheet_with_a_style_file_styles_a_view(tmp_path):
    _write(tmp_path / "wide_Style.yaml", {"width": 150})
    sheet = load_stylesheet(_write(tmp_path / "App_Stylesheet.yaml", {"styles": [{"kind": "Rect", "style": "wide_Style.yaml"}]}))
    view = View({"id": "root", "kind": "Container", "children": [
        {"id": "r", "kind": "Rect", "style": {"height": 10, "background": "#000000"}}]}, theme_seed=SEED, stylesheet_spec=sheet)
    assert view.node("r").get("width") == 150.0


@pytest.mark.parametrize("loader, name, message", [
    (load_theme, "Card_Style.yaml", r"loaded as a theme, but its name says it's one node's style"),
    (load_theme, "App_Stylesheet.yaml", r"loaded as a theme, but its name says it's a stylesheet"),
    (load_stylesheet, "Brand_Theme.yaml", r"loaded as a stylesheet, but its name says it's a theme"),
    (load_stylesheet, "Card_Style.yaml", r"loaded as a stylesheet, but its name says it's one node's style"),
])
def test_each_loader_refuses_another_kinds_name(tmp_path, loader, name, message):
    with pytest.raises(ValueError, match=message):
        loader(_write(tmp_path / name, {"styles": []}))


def test_names_without_a_convention_still_load(tmp_path):
    assert load_theme(_write(tmp_path / "themes" / "Brand.yaml", {"seed": "#6750A4"}))["seed"] == "#6750A4"
    assert load_stylesheet(_write(tmp_path / "styles" / "Default.yaml", {"styles": []})) == {"styles": []}


# -- 0.4.3.1 (#92): `style:` over the fields, and an `id:` --------------------------------------

def test_a_style_file_can_say_what_it_is(tmp_path):
    _write(tmp_path / "counter_Style.yaml", {"id": "counter_style", "style": COUNTER})
    view_file = _write(tmp_path / "Counter_View.yaml", {"id": "root", "kind": "Container", "style": "counter_Style.yaml"})
    spec, _, _ = build_view_spec(view_file)
    assert spec["style"] == COUNTER  # the fields, with no `id` or `style` in them


def test_the_id_is_optional_and_the_bare_form_still_works(tmp_path):
    _write(tmp_path / "a_Style.yaml", {"style": COUNTER})
    _write(tmp_path / "b_Style.yaml", COUNTER)
    for name in ("a_Style.yaml", "b_Style.yaml"):
        view_file = _write(tmp_path / "V_View.yaml", {"id": "root", "kind": "Container", "style": name})
        assert build_view_spec(view_file)[0]["style"] == COUNTER


@pytest.mark.parametrize("body, message", [
    ({"id": 3, "style": {"gap": 1}}, "id must be a string"),
    ({"id": "x", "style": ["gap"]}, "`style:` holds a mapping of style fields"),
])
def test_a_badly_formed_style_file_is_refused(tmp_path, body, message):
    _write(tmp_path / "bad_Style.yaml", body)
    view_file = _write(tmp_path / "V_View.yaml", {"id": "root", "kind": "Container", "style": "bad_Style.yaml"})
    with pytest.raises(ComponentError, match=message):
        build_view_spec(view_file)


def test_a_rule_can_name_the_wrapped_form(tmp_path):
    _write(tmp_path / "card_Style.yaml", {"id": "card_style", "style": {"corner_radius": 12}})
    sheet = _write(tmp_path / "Page_Stylesheet.yaml", {"styles": [{"kind": "Rect", "style": "card_Style.yaml"}]})
    assert load_stylesheet(sheet)["styles"][0]["style"] == {"corner_radius": 12}
