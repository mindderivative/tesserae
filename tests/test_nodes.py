"""#209 phase 3: the node model -- every key of spec section 2, property checks, ids and names, and the shape of the errors."""

import pytest

from tesserae.expr import Template
from tesserae.spec import widgets as W
from tesserae.spec.nodes import EVENTS, LoadError, load_marked, parse_view
from tesserae.spec.widgets import Property, WidgetDecl


def node(text, **kw):
    return parse_view(text, "T_View.yaml", **kw).root


def fails(text, message, **kw):
    with pytest.raises(LoadError) as caught:
        parse_view(text, "T_View.yaml", **kw)
    assert message in str(caught.value), str(caught.value)
    return caught.value


def view_decl(name):
    return WidgetDecl(name, {"label": Property("str", required=True)}, container=True, view=True)


def resolver(name):
    return view_decl(name) if name in ("Button", "Card") else None


# -- every key of section 2 -----------------------------------------------------------------------------------------------


def accepting_foreground():
    """The widgets that declare `foreground` among their style extras, as the error names them."""
    from tesserae.spec import widgets as registry

    registry._load_builtins()
    return ", ".join(sorted(name for name, decl in registry._REGISTRY.items() if "foreground" in decl.extras))


def test_widget_picks_the_widget_and_a_missing_or_unknown_one_is_an_error():
    assert node("widget: Text").widget == "Text"
    fails("text: x", "a node needs a 'widget:'")
    fails("widget: 5", "'widget:' takes a widget name")
    err = fails("widget: Texxt", "no widget named 'Texxt'")
    assert "did you mean 'Text'" in str(err)


def test_name_is_optional_and_a_plain_identifier():
    assert node("widget: Text\nname: label").name == "label"
    assert node("widget: Text").name is None
    for bad in ("2cool", "has space", "a-b", "5"):
        fails(f"widget: Text\nname: '{bad}'", "a name is letters, digits")


def test_if_is_an_expression_without_braces():
    assert node("widget: Text\nif: unread > 0").when is not None
    fails("widget: Text\nif: '{{ unread }}'", "'if:' is an expression, not a template")
    fails("widget: Text\nif: 'unread >'", "syntax error")
    fails("widget: Text\nif: ''", "'if:' takes an expression")


def test_for_binds_names_over_an_expression_and_key_needs_it():
    n = node("widget: Text\nfor: i, item in enumerate(items)\nkey: item.id")
    assert n.loop.targets == ("i", "item") and n.loop.source == "i, item in enumerate(items)" and n.key is not None
    assert node("widget: Text\nfor: x in range(3)").loop.targets == ("x",)
    fails("widget: Text\nfor: items", "'for:' reads 'item in items'")
    fails("widget: Text\nfor: x in items +", "syntax error")
    fails("widget: Text\nkey: item.id", "'key:' needs a 'for:'")


def test_slot_names_the_parents_slot():
    assert node("widget: Container\nchildren:\n  - widget: Text\n    slot: actions").children[0].slot == "actions"
    fails("widget: Text\nslot: 'a b'", "'slot:' takes a slot name")


def test_state_declares_names_with_starting_values():
    n = node("widget: Text\nstate: {on: false, label: '{{ 1 + 1 }}'}")
    assert n.state["on"] is False and isinstance(n.state["label"], Template)
    fails("widget: Text\nstate: [a]", "'state:' takes a mapping")
    fails("widget: Text\nstate: {_x: 1}", "a state name is a plain identifier")
    fails("widget: Text\nstate: {2x: 1}", "a state name is a plain identifier")


def test_style_takes_universal_fields_a_widgets_extras_and_expressions():
    n = node("widget: Container\nstyle: {width: 100, background: '{{ color }}', flex_direction: vertical}")
    assert n.style["width"] == 100 and isinstance(n.style["background"], Template)
    err = fails("widget: Container\nstyle: {widht: 100}", "Container: style 'widht' is not valid here")
    assert "did you mean 'width'" in str(err)
    fails("widget: Container\nstyle: [1]", "'style:' takes a mapping")
    assert node("widget: Container\nstyle: row_Style.yaml").style_file == "row_Style.yaml"
    assert node("widget: Text\nstyle: {foreground: on_surface}").style["foreground"] == "on_surface"  # an extra of the widgets that draw text
    err = fails("widget: Container\nstyle: {foreground: red}", "Container: style 'foreground' is not valid here")
    assert f"widgets that accept it: {accepting_foreground()}" in str(err)
    W.register_widget(WidgetDecl("Gauge", {}, extras=("track_height",)))
    try:
        assert node("widget: Gauge\nstyle: {track_height: 4}").style["track_height"] == 4
        fails("widget: Rect\nstyle: {track_height: 4}", "style 'track_height' is not valid here")
    finally:
        W.unregister_widget("Gauge")


def test_classes_is_a_list_of_names():
    assert node("widget: Text\nclasses: [a, b]").classes == ["a", "b"]
    fails("widget: Text\nclasses: a", "'classes:' takes a list")
    fails("widget: Text\nclasses: [1]", "'classes:' takes a list")


def test_handlers_map_known_events_to_an_action_or_statements():
    n = node("widget: Rect\nhandlers:\n  on_click: save\n  on_hover_enter: \"hint = 'Save'; count += 1\"\n  on_change: navigate.back")
    assert n.handlers["on_click"].action == "save" and n.handlers["on_change"].action == "navigate.back"
    assert n.handlers["on_hover_enter"].statements is not None and n.handlers["on_hover_enter"].action is None
    err = fails("widget: Rect\nhandlers: {on_clck: save}", "no event 'on_clck'")
    assert "did you mean 'on_click'" in str(err)
    fails("widget: Rect\nhandlers: {click: save}", "'click' is not an event name")
    fails("widget: Rect\nhandlers: {on_click: 5}", "a handler is an action name or statements")
    fails("widget: Rect\nhandlers: {on_click: 'if x: y'}", "'if' is not available")
    fails("widget: Rect\nhandlers: [on_click]", "'handlers:' takes a mapping")


def test_the_events_are_the_views_events_plus_on_key():
    from tesserae.view import _EVENTS

    assert set(EVENTS) == set(_EVENTS) | {"on_key", "on_submit", "on_press", "on_move", "on_release", "on_input"}


def test_a11y_takes_the_documented_fields_checked_and_bound():
    n = node("widget: Rect\na11y: {label: Save, role: button, hidden: false, live: polite, level: 2}")
    assert n.a11y["role"] == "button" and n.a11y["level"] == 2
    assert isinstance(node("widget: Rect\na11y: {label: '{{ title }}'}").a11y["label"], Template)
    fails("widget: Rect\na11y: {lable: x}", "no a11y field 'lable'")
    fails("widget: Rect\na11y: {role: wizard}", "a11y role 'wizard'")
    fails("widget: Rect\na11y: {level: 0}", "a11y level must be a positive whole number")
    fails("widget: Rect\na11y: {live: '{{ x }}'}", "a11y 'live' cannot be bound")


def test_interaction_is_a_switch_or_a_colour_role():
    assert node("widget: Rect\ninteraction: true").interaction is True
    assert node("widget: Rect\ninteraction: on_primary").interaction == "on_primary"
    fails("widget: Rect\ninteraction: {color: x}", "write interaction: <colour>")
    fails("widget: Rect\ninteraction: [1]", "'interaction:' takes true, false or a colour role")


def test_window_region_is_drag_or_none():
    assert node("widget: Rect\nwindow_region: drag").window_region == "drag"
    err = fails("widget: Rect\nwindow_region: dragg", "'window_region:' is one of drag, none")
    assert "did you mean 'drag'" in str(err)


def test_route_is_for_a_view_call():
    assert node("widget: Card\nlabel: x\nroute: ''", resolver=resolver).route == ""
    assert node("widget: Card\nlabel: x\nroute: notes", resolver=resolver).route == "notes"
    fails("widget: Rect\nroute: notes", "'route:' is for a view call")
    fails("widget: Card\nlabel: x\nroute: 5", "'route:' takes a path", resolver=resolver)


def test_children_need_a_container_and_each_child_is_a_node():
    n = node("widget: Container\nchildren:\n  - widget: Text\n  - widget: Rect")
    assert [c.widget for c in n.children] == ["Text", "Rect"]
    fails("widget: Text\nchildren: []", "Text takes no children")
    fails("widget: Container\nchildren: x", "'children:' takes a list of nodes")
    fails("widget: Container\nchildren:\n  - Text", "a node is a mapping with a 'widget:' key")


def test_params_and_expects_are_only_valid_on_the_root():
    doc = parse_view("params: [label]\nexpects: {count: int}\nwidget: Text\ntext: '{{ label }}'", "C_View.yaml", view_name="C")
    assert doc.params == ["label"] and doc.expects == {"count": int and "int"} and doc.decl.view and doc.decl.properties["label"].required
    fails("widget: Container\nchildren:\n  - params: [a]\n    widget: Text", "'params:' is only valid at the top of a view file")
    fails("params: 5\nwidget: Text", "params is a list or a mapping")


def test_a_property_is_checked_against_its_widgets_declaration():
    assert node("widget: Slider\nvalue: 0.5").props["value"] == 0.5
    assert node("widget: Slider\nvalue: 1").props["value"] == 1.0
    assert isinstance(node("widget: Slider\nvalue: '{{ volume }}'").props["value"], Template)
    err = fails("widget: Slider\nvalu: 1", "Slider: no property 'valu'")
    assert "did you mean 'value'" in str(err) and "properties: value, min, max, step, ticks, value_indicator, label, disabled" in str(err)
    fails("widget: Slider\nvalue: loud", "Slider: 'value' takes a number")
    fails("widget: Checkbox\nchecked: 'yes'", "'checked' takes true or false")
    fails("widget: Icon", "Icon: give one of 'icon', 'path'")
    fails("widget: Icon\nicon: home\npath: M0 0Z", "'icon' and 'path' cannot both be given")
    node("widget: Icon\npath: M0 0Z")
    fails("widget: Icon\nicon: hom", "names no built-in icon")
    fails("widget: Text\nwrap: sideways", "which is not one of: word, none")
    fails("widget: Card", "'label' is required", resolver=resolver)


def test_a_node_and_nodes_property_hold_nodes():
    W.register_widget(WidgetDecl("Bar", {"leading": Property("node"), "actions": Property("nodes")}))
    try:
        n = node("widget: Bar\nleading: {widget: Icon, icon: home}\nactions:\n  - {widget: Text, name: t}\n  - {widget: Rect}")
        assert n.props["leading"].widget == "Icon" and [a.widget for a in n.props["actions"]] == ["Text", "Rect"]
        assert [x.id for x in n.walk()] == ["root", "root.leading", "root.t", "root.actions[1]"]
        fails("widget: Bar\nactions: x", "'actions' takes a list of nodes")
        fails("widget: Bar\nleading: x", "a node is a mapping")
    finally:
        W.unregister_widget("Bar")


def test_the_0_4_keys_say_what_to_write():
    for old, hint in (("kind: Text", "widget: X"), ("component: Card", "widget: X"), ("view: A_View.yaml", "widget: X"),
                      ("include: A.yaml", "widget: X")):
        fails(old, "is not a key in 0.5.0")
        assert hint in str(fails(old, "is not a key in 0.5.0"))
    for key, hint in (("id: a", "name:"), ("repeat: x", "for: item in items"), ("when: x", "if: expression"), ("bindings: {}", "text:"),
                      ("with: {}", "plain keys"), ("two_way: checked", "bare reference"), ("component_of: x", "address it as a part")):
        assert hint in str(fails(f"widget: Rect\n{key}", "is not a key in 0.5.0"))


# -- ids, names ------------------------------------------------------------------------------------------------------------


def test_every_node_gets_a_stable_id_from_its_path():
    n = node("widget: Container\nname: top\nchildren:\n  - widget: Text\n  - widget: Container\n    name: row\n    children:\n"
             "      - widget: Text\n      - {widget: Text, name: last}")
    assert [x.id for x in n.walk()] == ["root", "root.children[0]", "root.row", "root.row.children[0]", "root.row.last"]


def test_names_are_unique_in_a_view_but_a_parent_and_child_may_share_one():
    node("widget: Container\nname: a\nchildren:\n  - {widget: Text, name: a}")
    err = fails("widget: Container\nchildren:\n  - {widget: Text, name: x}\n  - {widget: Rect, name: x}", "the name 'x' is already used")
    assert "root.x" in str(err) and (err.line, err.column) == (4, 25)
    fails("widget: Container\nchildren:\n  - widget: Container\n    name: x\n    children: [{widget: Text}]\n  - widget: Container\n"
          "    children: [{widget: Text, name: x}]", "already used")


def test_nesting_is_capped():
    text = "{widget: Container, children: [" * 70 + "{widget: Text}" + "]}" * 70
    fails(text, "nested more than 64 deep")


# -- errors name the file, line and column ------------------------------------------------------------------------------


def test_an_error_names_the_file_line_and_column_and_renders_a_caret():
    err = fails("widget: Container\nchildren:\n  - widget: Slider\n    valu: 1\n", "T_View.yaml:4:5: error: Slider: no property 'valu'")
    shown = err.render()
    assert "    4 |     valu: 1" in shown.replace("  ", " ") or "valu: 1" in shown
    assert shown.splitlines()[-1].strip() == "|     ^".strip() or shown.endswith("^")


def test_an_error_inside_an_expression_points_into_the_yaml_string():
    err = fails("widget: Text\ntext: \"Hi {{ user. }}\"\n", "T_View.yaml:2:")
    assert err.line == 2 and err.column > 6


def test_a_yaml_syntax_error_and_a_duplicate_key_are_load_errors():
    fails("widget: Text\n  bad: [", "YAML:")
    err = fails("widget: Text\ntext: a\ntext: b", "duplicate key 'text'")
    assert err.line == 3
    fails("- widget: Text", "a view file is a mapping")
    fails("", "a view file is a mapping")


def test_load_marked_keeps_positions():
    data = load_marked("a: 1\nb:\n  - x\n  - y: 2\n")
    assert data.key_at["a"] == (1, 0) and data.val_at["a"] == (1, 3) and data["b"].item_at[1] == (4, 4)
    assert load_marked("k: \"q\"").val_at["k"] == (1, 4)  # the text of a quoted string starts after the quote


def test_a_key_that_yaml_1_1_reads_as_a_boolean_stays_the_text_written():
    data = load_marked("on: false\nno: 1\nyes: x\n")
    assert list(data) == ["on", "no", "yes"] and data["on"] is False
    assert node("widget: Text\nstate: {on: false}").state == {"on": False}
