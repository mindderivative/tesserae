"""#209 phase 3: the old-to-new translator -- each rule of spec section 15, and every file in the repository."""

import re
from pathlib import Path

import pytest
import yaml

from tesserae.spec.nodes import LoadError, parse_view
from tesserae.spec.translate import Translator, to_yaml
from tesserae.spec.widgets import WidgetDecl, decl_from_params

ROOT = Path(__file__).resolve().parent.parent


def tr(old, **kw):
    t = Translator(**kw)
    return t.translate(old), t.notes


def test_kind_component_view_and_include_become_widget():
    assert tr({"id": "root", "kind": "Rect"})[0] == {"widget": "Rect"}
    assert tr({"id": "root", "kind": "Container", "children": [{"id": "b", "component": "ButtonFilled"}]})[0]["children"][0] == \
        {"widget": "ButtonFilled", "name": "b"}
    assert tr({"id": "x", "view": "Home_View.yaml", "route": ""})[0] == {"widget": "Home", "name": "x", "route": ""}
    new, notes = tr({"id": "x", "include": "Part.yaml"})
    assert new["widget"] == "Part" and "became a call of the view 'Part'" in notes[0]


def test_id_becomes_name_and_the_roots_id_root_is_dropped():
    assert tr({"id": "root", "kind": "Rect"})[0] == {"widget": "Rect"}
    assert tr({"id": "main", "kind": "Rect"})[0] == {"widget": "Rect", "name": "main"}
    assert tr({"id": "a", "kind": "Rect"}, addressed=set())[0] == {"widget": "Rect"}  # nothing addresses it
    assert tr({"id": "a", "kind": "Rect"}, addressed={"a"})[0]["name"] == "a"


def test_with_becomes_plain_keys_and_a_clash_is_reported():
    new, notes = tr({"id": "r", "component": "Card", "label": "old", "with": {"label": "new", "width": 4}})
    assert new["label"] == "new" and new["width"] == 4 and "overrides" in notes[0]


def test_text_icon_image_and_svg_mappings_are_flattened():
    new, _ = tr({"id": "t", "kind": "Text", "text": {"content": "Hi", "typography_role": "body_large", "wrap": "none"}})
    assert new == {"widget": "Text", "name": "t", "text": "Hi", "typography_role": "body_large", "wrap": "none"}
    assert tr({"id": "i", "kind": "Icon", "icon": {"name": "home"}})[0]["icon"] == "home"
    assert tr({"id": "m", "kind": "Image", "image": {"src": "a.png", "fit": "contain"}})[0] | {} == \
        {"widget": "Image", "name": "m", "src": "a.png", "fit": "contain"}
    assert tr({"id": "s", "kind": "Svg", "svg": {"content": "<svg/>"}})[0]["content"] == "<svg/>"
    assert tr({"id": "t", "kind": "Text", "text": "plain"})[0]["text"] == "plain"


def test_bindings_become_the_property_and_a_bound_style_value_goes_to_style():
    new, _ = tr({"id": "t", "kind": "Text", "text": {"content": ""}, "bindings": {"text": "{{ title.get() }}", "foreground": "{{ c }}"}})
    assert new["text"] == "{{ title.get() }}" and new["style"] == {"foreground": "{{ c }}"}
    new, _ = tr({"id": "t", "kind": "Rect", "style": {"width": 1}, "bindings": {"background": "{{ c }}"}})
    assert new["style"] == {"width": 1, "background": "{{ c }}"}


def test_two_way_becomes_a_bare_reference():
    new, notes = tr({"id": "c", "kind": "Checkbox", "bindings": {"checked": "{{ done.get() }}"}, "two_way": "checked"})
    assert new["checked"] == "{{ done }}" and not notes
    _, notes = tr({"id": "c", "kind": "Checkbox", "bindings": {"checked": "{{ not done.get() }}"}, "two_way": "checked"})
    assert "needs a bare reference" in notes[0]
    _, notes = tr({"id": "c", "kind": "Checkbox", "two_way": "checked"})
    assert "names no property" in notes[0]


def test_when_and_if_then_else_become_if():
    assert tr({"id": "i", "kind": "Icon", "when": "{{ icon }}"})[0]["if"] == "icon"
    new, _ = tr({"kind": "Container", "id": "root", "children": [{"if": "{{ a }}", "then": {"id": "x", "kind": "Text"},
                                                                  "else": {"id": "y", "kind": "Rect"}}]})
    assert new["children"] == [{"widget": "Text", "name": "x", "if": "a"}, {"widget": "Rect", "name": "y", "if": "not (a)"}]


def test_a_literal_repeat_becomes_the_sibling_nodes_the_old_expander_made():
    new, _ = tr({"id": "root", "kind": "Container", "children": [
        {"id": "i", "component": "Item", "with": {"width": 4}, "repeat": [{"label": "A"}, {"label": "B"}]}]})
    assert new["children"] == [{"widget": "Item", "name": "i_0", "width": 4, "label": "A"},
                               {"widget": "Item", "name": "i_1", "width": 4, "label": "B"}]


def test_a_repeat_over_an_expression_becomes_for_with_the_per_item_parameters():
    old = {"id": "root", "kind": "Container", "children": [{"id": "item", "component": "Item", "with": {"width": "{{ w }}"},
                                                              "repeat": "{{ items }}"}]}
    new, notes = tr(old, params_of=lambda n: ["label", "icon", "width"])
    child = new["children"][0]
    assert child["for"] == "item in items" and child["label"] == "{{ item.label }}" and child["icon"] == "{{ item.icon }}"
    assert child["width"] == "{{ w }}" and "stand-in" in notes[-1]
    _, notes = tr(old)
    assert "per-item keys are not known" in notes[0]


def test_interaction_color_becomes_the_role_and_component_of_is_dropped():
    new, notes = tr({"id": "r", "kind": "Rect", "interaction": {"color": "on_primary"}, "component_of": "Button"})
    assert new["interaction"] == "on_primary" and "component_of" in notes[0] and "component_of" not in new


def test_a_parameter_spliced_inside_an_expression_is_just_the_name():
    new, _ = tr({"id": "p", "kind": "Rect", "bindings": {"background": "{{ app.screen == '{{ screen }}' and 'a' or 'b' }}"}})
    assert new["style"]["background"] == "{{ app.screen == screen and 'a' or 'b' }}"


def test_navigate_to_a_parameter_becomes_a_call():
    new, notes = tr({"id": "r", "kind": "Container", "handlers": {"on_click": "navigate.{{ screen }}"}})
    assert new["handlers"] == {"on_click": "navigate_to(screen)"} and "navigate_to" in notes[0]
    assert tr({"id": "r", "kind": "Container", "handlers": {"on_click": "navigate.back"}})[0]["handlers"] == {"on_click": "navigate.back"}


def test_a_dynamic_widget_name_and_an_undeclared_call_property_are_reported():
    _, notes = tr({"id": "b", "component": "{{ button }}"})
    assert "no dynamic widget names" in notes[0]
    _, notes = tr({"id": "b", "component": "ButtonText", "bindings": {"disabled": "{{ x }}"}}, params_of=lambda n: ["label"])
    assert "ButtonText declares no parameter 'disabled'" in notes[0]


def test_the_header_is_kept_first_and_the_output_is_yaml():
    new, _ = tr({"params": ["label"], "id": "root", "kind": "Text", "text": {"content": "{{ label }}"}})
    assert list(new) == ["params", "widget", "text"]
    assert yaml.safe_load(to_yaml(new)) == new


# -- every file in the repository ----------------------------------------------------------------------------------------

FILES = sorted(f for f in ROOT.glob("**/*.yaml") if re.search(r"_(View|Component)\.yaml$", f.name)
               and not {".venv", "site", ".git", "node_modules"} & set(f.relative_to(ROOT).parts))
STEM = re.compile(r"_(View|Component)\.yaml$")
PARAMS = {}
for _f in FILES:
    _d = yaml.safe_load(_f.read_text(encoding="utf-8"))
    if _f.name.endswith("_View.yaml") or STEM.sub("", _f.name) not in PARAMS:  # a view of a name beats a 0.4 component of it (Divider, Tabs)
        PARAMS[STEM.sub("", _f.name)] = _d.get("params") if isinstance(_d, dict) else None


def _resolver(name):
    if name in PARAMS:
        return decl_from_params(name, PARAMS[name]) if PARAMS[name] is not None else WidgetDecl(name, container=True, view=True)
    return None


#: What the translator reports and the loader rejects, for the component pass to settle: file -> a word in the note that says why.
KNOWN_GAPS = {
    "ButtonGroup_Component.yaml": "no dynamic widget names",
    "Settings_View.yaml": "declares no parameter 'disabled'",
}


def test_the_repository_has_the_files_the_sweep_expects():
    assert len(FILES) >= 130


@pytest.mark.parametrize("path", FILES, ids=lambda p: str(p.relative_to(ROOT)))
def test_every_file_translates_and_loads_in_the_new_syntax(path):
    old = yaml.safe_load(path.read_text(encoding="utf-8"))
    translator = Translator(params_of=PARAMS.get)
    text = to_yaml(translator.translate(old))
    try:
        doc = parse_view(text, path.name, resolver=_resolver)
    except LoadError as error:
        reason = KNOWN_GAPS.get(path.name)
        assert reason and any(reason in note for note in translator.notes), f"{error}\n\nnotes: {translator.notes}\n\n{text}"
        return
    assert doc.root.widget and all(n.id for n in doc.root.walk())


def test_the_known_gaps_are_still_gaps():
    # when the component pass settles one, this fails and the entry goes
    failing = set()
    for path in FILES:
        text = to_yaml(Translator(params_of=PARAMS.get).translate(yaml.safe_load(path.read_text(encoding="utf-8"))))
        try:
            parse_view(text, path.name, resolver=_resolver)
        except LoadError:
            failing.add(path.name)
    assert failing == set(KNOWN_GAPS)


def test_a_translated_file_loads_back_to_the_same_names():
    path = ROOT / "src" / "tesserae" / "spec" / "components" / "ListItem_Component.yaml"
    old = yaml.safe_load(path.read_text(encoding="utf-8"))
    old_ids = set()

    def collect(node):
        if isinstance(node, dict):
            if "id" in node and node["id"] != "root":
                old_ids.add(node["id"])
            for child in node.get("children") or []:
                collect(child)

    collect(old)
    doc = parse_view(to_yaml(Translator().translate(old)), path.name)
    assert {n.name for n in doc.root.walk() if n.name} == old_ids
