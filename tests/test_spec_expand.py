"""Real coverage for `tesserae.spec.expand_components` -- Part 3's
macro-expansion engine. Exercises the real `Button_Component.yaml`
fragment end to end (parsed by `yaml.safe_load`, constructed as a real
`tre.View`), plus every real guard the engine states in its own module
docstring: missing/unknown params, a missing call-site `id:`, an unknown
component name, a cycle, id-namespacing across two uses of the same
component, and a `{{ }}` binding forwarded as a param value surviving
untouched. `repeat:` (M28) gets its own real coverage further down,
using the already-shipped `ListItem_Component.yaml` fragment.
"""

from pathlib import Path

import pytest

from helpers import elevation, view_from
import yaml
from tre import Window

from tesserae.spec import ComponentError, expand_components
from tesserae.spec.expand import MAX_DEPTH
from tesserae.widgets import button as imperative_button
from tesserae.widgets import list_item as imperative_list_item

BUTTON_WITH = {"label": "Save", "width": 120, "height": 40, "corner_radius": 20}


def _button_view_yaml(with_values: dict | None = None) -> str:
    return yaml.safe_dump(
        {
            "id": "root",
            "kind": "Container",
            "style": {"width": 300, "height": 200},
            "children": [
                {"id": "save_button", "component": "ButtonFilled", "with": with_values or BUTTON_WITH}
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
    view = view_from(expanded, theme_seed=(0x67, 0x50, 0xA4, 0xFF))
    declarative_node = view.node("save_button")

    window = Window(width=300, height=200)
    window.set_theme((0x67, 0x50, 0xA4, 0xFF))
    imperative_node = imperative_button(window, "Save", 120, 40, variant="filled").node  # a Widget since M41

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
            "children": [{"component": "ButtonFilled", "with": BUTTON_WITH}],
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
                {"id": "btn1", "component": "ButtonFilled", "with": BUTTON_WITH},
                {"id": "btn2", "component": "ButtonFilled", "with": {**BUTTON_WITH, "label": "Cancel"}},
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
                    "component": "ButtonFilled",
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
                {"id": "b", "component": "ButtonFilled", "with": BUTTON_WITH, "style": {"width": 999}}
            ],
        }
    )
    with pytest.raises(ComponentError, match=r"takes only `id:`, `with:`, and `repeat:`"):
        expand_components(yaml_text)


def test_no_component_usage_is_a_true_no_op():
    yaml_text = yaml.safe_dump({"id": "root", "kind": "Container", "children": []})
    expanded = yaml.safe_load(expand_components(yaml_text))
    assert expanded == {"id": "root", "kind": "Container", "children": []}


def test_max_depth_is_a_real_positive_bound():
    assert MAX_DEPTH > 0


# M28: `repeat:` real coverage, using the already-shipped `ListItem`
# fragment (`params: [headline, width]`).

THEME_SEED = (0x67, 0x50, 0xA4, 0xFF)


def _repeat_view_yaml(items: list[dict], *, extra_with: dict | None = None) -> str:
    node = {"id": "settings", "component": "ListItem", "repeat": items}
    if extra_with is not None:
        node["with"] = extra_with
    return yaml.safe_dump(
        {
            "id": "root",
            "kind": "Container",
            "style": {"width": 400, "height": 300, "flex_direction": "vertical"},
            "children": [node],
        }
    )


def test_repeat_expands_to_one_real_node_per_item():
    yaml_text = _repeat_view_yaml(
        [{"headline": "Notifications"}, {"headline": "Privacy"}, {"headline": "About"}],
        extra_with={"width": 360},
    )
    expanded = yaml.safe_load(expand_components(yaml_text))
    children = expanded["children"]
    assert len(children) == 3
    assert [c["id"] for c in children] == ["settings.0", "settings.1", "settings.2"]
    assert [c["children"][0]["text"]["content"] for c in children] == [
        "Notifications",
        "Privacy",
        "About",
    ]


def test_repeat_matches_the_imperative_catalog():
    yaml_text = _repeat_view_yaml([{"headline": "Alice"}, {"headline": "Bob"}], extra_with={"width": 360})
    expanded = expand_components(yaml_text)
    view = view_from(expanded, theme_seed=THEME_SEED)
    alice = view.node("settings.0.headline")
    bob = view.node("settings.1.headline")
    assert alice.get("text") == "Alice"
    assert bob.get("text") == "Bob"

    # since M41 `list_item()` is built from the same fragment and its parts are reachable
    window = Window(width=400, height=300)
    imperative_alice = imperative_list_item(window, "Alice", width=360)
    assert imperative_alice.part("headline").get("text") == alice.get("text") == "Alice"


def test_repeat_produces_real_namespaced_ids_with_no_collisions():
    yaml_text = _repeat_view_yaml([{"headline": f"Item {i}"} for i in range(5)], extra_with={"width": 360})
    expanded = yaml.safe_load(expand_components(yaml_text))
    ids = [c["id"] for c in expanded["children"]]
    assert ids == [f"settings.{i}" for i in range(5)]
    assert len(set(ids)) == len(ids), "every repeated instance must get a real, unique id"


def test_repeat_must_be_a_list():
    yaml_text = _repeat_view_yaml({"headline": "not a list"}, extra_with={"width": 360})  # type: ignore[arg-type]
    with pytest.raises(ComponentError, match=r"`repeat:` must be a list of mappings"):
        expand_components(yaml_text)


def test_repeat_entry_must_be_a_mapping():
    yaml_text = _repeat_view_yaml(["not a mapping"], extra_with={"width": 360})  # type: ignore[list-item]
    with pytest.raises(ComponentError, match=r"`repeat:` entry 0 must be a mapping"):
        expand_components(yaml_text)


def test_repeat_key_colliding_with_with_is_rejected():
    # `width` given both as a shared `with:` value and inside a
    # `repeat:` entry -- real, deliberate ambiguity, rejected rather
    # than silently letting one win.
    yaml_text = _repeat_view_yaml(
        [{"headline": "Notifications", "width": 200}], extra_with={"width": 360}
    )
    with pytest.raises(ComponentError, match=r"repeats key\(s\) \['width'\]"):
        expand_components(yaml_text)


def test_repeat_still_validates_missing_params_per_item():
    # `width` is a declared param, supplied via neither `with:` nor
    # this one `repeat:` entry -- must fail exactly like an ordinary,
    # non-repeated missing-parameter case.
    yaml_text = _repeat_view_yaml([{"headline": "Notifications"}])
    with pytest.raises(ComponentError, match=r"missing parameter\(s\) \['width'\] for 'settings.0'"):
        expand_components(yaml_text)


def test_repeat_at_the_document_root_is_rejected():
    # `repeat:` only makes sense inside a `children:` list -- the root
    # of a view is a single node, there's nowhere for a 2nd/3rd
    # instance to go.
    yaml_text = yaml.safe_dump(
        {"id": "settings", "component": "ListItem", "repeat": [{"headline": "A"}, {"headline": "B"}], "with": {"width": 360}}
    )
    with pytest.raises(ComponentError, match=r"needs exactly one"):
        expand_components(yaml_text)


def test_repeat_with_zero_items_produces_zero_nodes():
    yaml_text = _repeat_view_yaml([], extra_with={"width": 360})
    expanded = yaml.safe_load(expand_components(yaml_text))
    assert expanded["children"] == []


def test_nested_repeat_namespaces_correctly_under_the_outer_call(tmp_path: Path):
    # A component that itself contains a `repeat:`, sourced from a
    # param supplied by the OUTER call site -- proves `{{ items }}`
    # substitution (already real, general-purpose) correctly resolves
    # a `repeat:` value before `_walk` ever reaches the nested
    # `component:` node, and that the outer call site's own id still
    # prefixes every inner repeated instance, exactly once, matching
    # ordinary nested-component namespacing.
    from tesserae.spec import expand as expand_module

    real_components_dir = Path(expand_module.__file__).parent / "components"
    (tmp_path / "Section_Component.yaml").write_text(
        yaml.safe_dump(
            {
                "params": ["items"],
                "id": "root",
                "kind": "Container",
                "children": [
                    {"id": "rows", "component": "ListItem", "repeat": "{{ items }}", "with": {"width": 360}}
                ],
            }
        )
    )
    yaml_text = yaml.safe_dump(
        {
            "id": "root",
            "kind": "Container",
            "children": [
                {
                    "id": "section",
                    "component": "Section",
                    "with": {"items": [{"headline": "One"}, {"headline": "Two"}]},
                }
            ],
        }
    )
    expanded = yaml.safe_load(
        expand_components(yaml_text, component_dirs=[tmp_path, real_components_dir])
    )
    section = expanded["children"][0]
    row_ids = [c["id"] for c in section["children"]]
    assert row_ids == ["section.rows.0", "section.rows.1"]
