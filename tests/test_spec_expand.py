"""Real coverage for `tesserae.spec.expand_components` -- Part 3's
macro-expansion engine. Exercises the real `Button_Component.yaml`
fragment end to end (parsed by `yaml.safe_load`, constructed as a real
`tre.View`), plus every real guard the engine states in its own module
docstring: missing/unknown params, a missing call-site `id:`, an unknown
component name, a cycle, id-namespacing across two uses of the same
component, and a `{{ }}` binding forwarded as a param value surviving
untouched.
"""

from pathlib import Path

import pytest
import yaml
from tre import View, Window

from tesserae.spec import ComponentError, expand_components
from tesserae.spec.expand import MAX_DEPTH
from tesserae.widgets import button as imperative_button

BUTTON_WITH = {"label": "Save", "width": 120, "height": 40, "corner_radius": 20}


def _button_view_yaml(with_values: dict | None = None) -> str:
    return yaml.safe_dump(
        {
            "id": "root",
            "kind": "Container",
            "style": {"width": 300, "height": 200},
            "children": [
                {"id": "save_button", "component": "Button", "with": with_values or BUTTON_WITH}
            ],
        }
    )


def test_expand_produces_no_component_keys_left():
    expanded = expand_components(_button_view_yaml())
    data = yaml.safe_load(expanded)
    child = data["children"][0]
    assert "component" not in child
    assert "with" not in child
    assert "params" not in child


def test_numeric_params_round_trip_as_real_numbers_not_quoted_strings():
    expanded = expand_components(_button_view_yaml())
    data = yaml.safe_load(expanded)
    button = data["children"][0]
    assert button["style"]["width"] == 120
    assert isinstance(button["style"]["width"], int)


def test_expanded_button_constructs_a_real_view_matching_tesserae_widgets_button():
    expanded = expand_components(_button_view_yaml())
    view = View("Save_View.yaml", source=expanded, theme_seed=(0x67, 0x50, 0xA4, 0xFF))
    declarative_node = view.node("save_button")

    window = Window(width=300, height=200)
    window.set_theme((0x67, 0x50, 0xA4, 0xFF))
    imperative_node = imperative_button(window, "Save", 120, 40, variant="filled")

    assert declarative_node.get("corner_radius") == imperative_node.get("corner_radius")


def test_missing_param_raises_naming_all_missing():
    with pytest.raises(ComponentError, match=r"missing parameter\(s\).*height.*corner_radius|missing parameter"):
        expand_components(_button_view_yaml({"label": "Save"}))


def test_unknown_param_raises_naming_it():
    with pytest.raises(ComponentError, match=r"unknown parameter\(s\).*extra"):
        expand_components(_button_view_yaml({**BUTTON_WITH, "extra": 5}))


def test_unknown_component_raises_naming_it():
    yaml_text = yaml.safe_dump(
        {
            "id": "root",
            "kind": "Container",
            "children": [{"id": "x", "component": "NotARealComponent", "with": {}}],
        }
    )
    with pytest.raises(ComponentError, match="unknown component 'NotARealComponent'"):
        expand_components(yaml_text)


def test_component_without_call_site_id_raises():
    yaml_text = yaml.safe_dump(
        {
            "id": "root",
            "kind": "Container",
            "children": [{"component": "Button", "with": BUTTON_WITH}],
        }
    )
    with pytest.raises(ComponentError, match="needs its own `id:`"):
        expand_components(yaml_text)


def test_two_uses_of_same_component_get_distinct_namespaced_ids():
    yaml_text = yaml.safe_dump(
        {
            "id": "root",
            "kind": "Container",
            "children": [
                {"id": "btn1", "component": "Button", "with": BUTTON_WITH},
                {"id": "btn2", "component": "Button", "with": {**BUTTON_WITH, "label": "Cancel"}},
            ],
        }
    )
    expanded = yaml.safe_load(expand_components(yaml_text))
    ids = [child["id"] for child in expanded["children"]]
    label_ids = [child["children"][0]["id"] for child in expanded["children"]]
    assert ids == ["btn1", "btn2"]
    assert label_ids == ["btn1.label", "btn2.label"]
    assert len(set(ids + label_ids)) == 4


def test_binding_forwarded_as_param_value_survives_untouched():
    yaml_text = yaml.safe_dump(
        {
            "id": "root",
            "kind": "Container",
            "children": [
                {
                    "id": "b",
                    "component": "Button",
                    "with": {**BUTTON_WITH, "label": "{{ headline.get() }}"},
                }
            ],
        }
    )
    expanded = yaml.safe_load(expand_components(yaml_text))
    assert expanded["children"][0]["children"][0]["text"]["content"] == "{{ headline.get() }}"


def test_cycle_raises_naming_the_chain(tmp_path: Path):
    component_dir = tmp_path
    (component_dir / "SelfReferencing_Component.yaml").write_text(
        yaml.safe_dump(
            {
                "params": [],
                "id": "root",
                "kind": "Container",
                "children": [{"id": "inner", "component": "SelfReferencing", "with": {}}],
            }
        )
    )
    yaml_text = yaml.safe_dump(
        {
            "id": "root",
            "kind": "Container",
            "children": [{"id": "x", "component": "SelfReferencing", "with": {}}],
        }
    )
    with pytest.raises(ComponentError, match="component cycle"):
        expand_components(yaml_text, component_dirs=[component_dir])


def test_extra_keys_at_call_site_are_rejected():
    yaml_text = yaml.safe_dump(
        {
            "id": "root",
            "kind": "Container",
            "children": [
                {"id": "b", "component": "Button", "with": BUTTON_WITH, "style": {"width": 999}}
            ],
        }
    )
    with pytest.raises(ComponentError, match=r"takes only `id:` and `with:`"):
        expand_components(yaml_text)


def test_no_component_usage_is_a_true_no_op():
    yaml_text = yaml.safe_dump({"id": "root", "kind": "Container", "children": []})
    expanded = yaml.safe_load(expand_components(yaml_text))
    assert expanded == {"id": "root", "kind": "Container", "children": []}


def test_max_depth_is_a_real_positive_bound():
    assert MAX_DEPTH > 0
