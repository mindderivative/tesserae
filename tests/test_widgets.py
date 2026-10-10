"""#209 phase 3: the widget registry -- declarations, property types and coercion, view `params:`, and the generated schema."""

import importlib.util
import json
from pathlib import Path

import pytest

from tesserae.spec import widgets as W
from tesserae.spec.widgets import Property, PropertyError, WidgetDecl, decl_from_params

ROOT = Path(__file__).resolve().parent.parent


def test_the_built_in_widgets_are_declared_with_their_properties():
    for name in ("Rect", "Container", "Text", "Link", "TextInput", "Image", "Icon", "Svg", "ScrollView", "Checkbox", "RadioButton", "Switch",
                 "Slider", "SpinBox", "CircularProgress", "LinearProgress", "LoadingIndicator", "TimePickerDial", "NodeGraph",
                 "GraphNode", "Window", "TitleBar", "Dock", "DockPanel", "Slot"):
        assert W.lookup(name) is not None, name
    assert set(W.lookup("Slider").properties) == {"value", "min", "max", "step", "ticks", "value_indicator", "vertical", "size", "icon", "label", "disabled"}
    assert W.lookup("Slider").properties["value"].model
    assert W.lookup("Container").container and not W.lookup("Text").container
    assert W.lookup("Nope") is None


def test_state_is_a_property_never_style():
    # the 0.4.x node keys that were state are properties of the widgets that declare them
    assert "checked" in W.lookup("Checkbox").properties and "selected" in W.lookup("Switch").properties
    assert "value" in W.lookup("SpinBox").properties and "text" in W.lookup("TextInput").properties


@pytest.mark.parametrize("type_, good, kept", [
    ("str", "hello", "hello"), ("str", 5, "5"), ("int", 3, 3), ("int", 3.0, 3), ("float", 2, 2.0), ("float", 0.5, 0.5),
    ("bool", True, True), ("color", "#6750A4", "#6750A4"), ("color", "#6750A4CC", "#6750A4CC"), ("color", "primary", "primary"),
    ("color", "rgb(1, 2, 3)", "rgb(1, 2, 3)"), ("length", 12, 12), ("length", "auto", "auto"), ("length", "50%", "50%"),
    ("icon", "home", "home"), ("list", [1], [1]), ("dict", {"a": 1}, {"a": 1}), ("handler", "save", "save"), ("any", object, object),
])
def test_a_literal_that_fits_its_type_is_kept(type_, good, kept):
    prop = Property(type_)
    prop.name = "p"
    assert prop.coerce(good) == kept


@pytest.mark.parametrize("type_, bad", [
    ("str", True), ("str", [1]), ("int", 3.5), ("int", True), ("int", "3"), ("float", "x"), ("float", False), ("bool", "yes"), ("bool", 1),
    ("color", "not a color!"), ("color", 5), ("length", "wide"), ("length", True), ("icon", "No Such Icon"), ("icon", "zzzz_missing"),
    ("list", {"a": 1}), ("dict", [1]), ("handler", 5),
])
def test_a_literal_that_does_not_fit_is_an_error_naming_the_property(type_, bad):
    prop = Property(type_)
    prop.name = "p"
    with pytest.raises(PropertyError, match="'p'"):
        prop.coerce(bad)


def test_an_enum_lists_its_choices_and_suggests_the_nearest():
    prop = Property("enum", choices=("filled", "tonal", "outlined"))
    prop.name = "variant"
    assert prop.coerce("tonal") == "tonal"
    with pytest.raises(PropertyError, match="filled, tonal, outlined") as caught:
        prop.coerce("tonl")
    assert "tonal" in caught.value.hint


def test_an_unknown_icon_suggests_the_nearest():
    prop = Property("icon")
    prop.name = "icon"
    with pytest.raises(PropertyError) as caught:
        prop.coerce("hom")
    assert "home" in caught.value.hint


def test_an_expression_none_and_structural_types_pass_coercion():
    prop = Property("int")
    prop.name = "p"
    assert prop.coerce("{{ n + 1 }}") == "{{ n + 1 }}"
    assert prop.coerce(None) is None
    assert Property("nodes").coerce([1]) == [1]
    required = Property("str", required=True)
    required.name = "label"
    with pytest.raises(PropertyError, match="needs a value"):
        required.coerce(None)


def test_a_declaration_checks_its_properties_unknown_first_then_required():
    decl = WidgetDecl("Thing", {"value": Property("float"), "label": Property("str", required=True)})
    problems = decl.check_properties(["valu"])
    assert problems[0][0] == "Thing: no property 'valu'" and "did you mean 'value'" in problems[0][1] and "properties: value, label" in problems[0][1]
    assert problems[1][0] == "Thing: 'label' is required"
    assert decl.check_properties(["value", "label"]) == []


def test_a_property_cannot_take_the_name_of_a_universal_key():
    with pytest.raises(ValueError, match="'style'"):
        W.declare("Bad", {"style": Property("str")})
    with pytest.raises(ValueError, match="'children'"):
        decl_from_params("Card", ["children"])


def test_the_decorator_declares_a_widget_from_a_class():
    @W.widget("TestDecoratedSlider", doc="Test.")
    class TestDecoratedSlider:
        value = Property("float", default=0.0, model=True)
        extras = ("track_height",)
        parts = ("track", "handle")

    try:
        decl = W.lookup("TestDecoratedSlider")
        assert decl is TestDecoratedSlider.decl
        assert decl.properties["value"].name == "value" and decl.extras == ("track_height",) and decl.parts == ("track", "handle")
        with pytest.raises(ValueError, match="already declared"):
            W.declare("TestDecoratedSlider")
    finally:
        W.unregister_widget("TestDecoratedSlider")


def test_an_app_registers_its_own_widget_and_replacing_a_built_in_is_deliberate():
    decl = WidgetDecl("MyGauge", {"level": Property("float")})
    try:
        W.register_widget(decl)
        assert W.lookup("MyGauge") is decl
        with pytest.raises(ValueError, match="already registered"):
            W.register_widget(WidgetDecl("MyGauge"))
        assert W.register_widget(WidgetDecl("MyGauge"), replace=True) is W.lookup("MyGauge")
    finally:
        W.unregister_widget("MyGauge")


def test_a_params_list_declares_required_names_and_defaults():
    decl = decl_from_params("Card", ["title", {"width": 120}])
    assert decl.view and decl.container
    assert decl.properties["title"].required and not decl.properties["width"].required and decl.properties["width"].default == 120


def test_a_params_mapping_declares_types_choices_and_model():
    decl = decl_from_params("Button", {
        "label": {"type": "str", "required": True},
        "variant": {"type": "enum", "choices": ["filled", "text"], "default": "filled"},
        "selected": {"type": "bool", "default": False, "model": True},
        "disabled": "bool",
    })
    assert decl.properties["label"].required and decl.properties["variant"].choices == ("filled", "text")
    assert decl.properties["selected"].model and decl.properties["disabled"].type == "bool" and decl.properties["disabled"].default is False


@pytest.mark.parametrize("params, message", [
    ("nope", "params is a list or a mapping"), ([5], "a name or"), ({"a": 5}, "a type or a mapping"),
    ({"a": {"type": "str", "wat": 1}}, "unknown field"), ({"a": "not_a_type"}, "not one of"), ({"a": {"type": "enum"}}, "needs choices"),
])
def test_bad_params_are_errors(params, message):
    with pytest.raises(ValueError, match=message):
        decl_from_params("V", params)


def test_the_schema_has_a_branch_per_widget_and_is_what_the_tool_writes():
    schema = W.json_schema()
    assert schema["properties"]["widget"]["enum"] == W.names()
    assert len(schema["allOf"]) == len(W.names())
    spec = importlib.util.spec_from_file_location("generate_widget_schema", ROOT / "tools" / "generate_widget_schema.py")
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    assert tool.PATH.read_text(encoding="utf-8") == tool.render(), "run `python tools/generate_widget_schema.py`"
    slider = next(b for b in schema["allOf"] if b["if"]["properties"]["widget"]["const"] == "Slider")["then"]
    assert "value" in slider["properties"] and "value" in slider["propertyNames"]["enum"] and "valu" not in slider["propertyNames"]["enum"]
    json.dumps(schema)
