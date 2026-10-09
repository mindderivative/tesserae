"""#209 phase 6: stylesheet rules -- the shape and its errors, specificity, layers, inline over rules, variants, parts and states."""

import pytest
import yaml

from tesserae import App, Signal, ViewModel
from tesserae.composed import open_composed
from tesserae.spec import widgets as W
from tesserae.spec.compose import Composer
from tesserae.spec.nodes import LoadError, load_marked, parse_view
from tesserae.spec.rules import Rule, RuleSheet, STATES, is_rule_sheet, load_rule_sheet, ordered
from tesserae.spec.widgets import Property, WidgetDecl, decl_from_params
from tesserae.viewmodel import Bindings


def sheet(text):
    return RuleSheet.of(load_marked(text, "S_Stylesheet.yaml"), "S_Stylesheet.yaml", text)


def bad(text, message):
    with pytest.raises(LoadError) as caught:
        sheet(text)
    assert message in str(caught.value), str(caught.value)
    return caught.value


class VM:
    def __init__(self):
        self.mode = Signal("filled")
        self.on = Signal(False)


def compose(main, rules, views=None, vm=None):
    """Composes `main` with the rule sheets (lowest layer first); `views` maps a name to its source."""
    sources = views or {}
    decls = {n: decl_from_params(n, yaml.safe_load(s).get("params")) for n, s in sources.items()}
    docs = {n: parse_view(s, f"{n}_View.yaml", resolver=decls.get, view_name=n) for n, s in sources.items()}
    doc = parse_view(main, "Main_View.yaml", resolver=decls.get)
    return Composer(docs, vm or VM(), rules=[sheet(r) if isinstance(r, str) else r for r in rules]).compose(doc)


# -- the shape -------------------------------------------------------------------------------------------------------------


def test_a_sheet_of_rules_is_checked_and_prepared():
    s = sheet("styles:\n  - widget: Text\n    classes: [big]\n    state: hovered\n    style: {foreground: on_surface, opacity: 0.5}\n"
              "  - style: {corner_radius: 4}\n")
    assert [r.widget for r in s.rules] == ["Text", None]
    assert s.rules[0].classes == {"big"} and s.rules[0].state == "hovered"
    assert [r.widget for r in s.candidates(["Text"])] == [None, "Text"] and [r.widget for r in s.candidates(["Rect"])] == [None]
    assert RuleSheet.of(None).rules == [] and sheet("styles: []").rules == []


def test_the_old_and_the_new_shape_are_told_apart():
    assert is_rule_sheet({"styles": [{"widget": "Button", "style": {}}]}) and is_rule_sheet({"styles": [{"part": "x"}]})
    assert not is_rule_sheet({"styles": [{"kind": "Rect", "style": {}}, {"id": "a", "style": {}}]}) and not is_rule_sheet({}) and not is_rule_sheet(None)


def test_a_rule_with_an_unknown_key_widget_or_state_says_what_is_allowed():
    err = bad("styles:\n  - widgit: Text\n    style: {opacity: 1}", "a rule has no 'widgit'")
    assert "did you mean 'widget'" in str(err) and (err.line, err.column) == (2, 4)
    err = bad("styles:\n  - widget: Text\n    state: hover\n    style: {opacity: 1}", "'state:' is one of hovered, focused")
    assert "did you mean 'hovered'" in str(err) and err.line == 3
    bad("styles:\n  - widget: Text\n    style: {}", "a rule needs a 'style:' mapping")
    bad("styles:\n  - widget: 5\n    style: {opacity: 1}", "'widget:' is a widget name")
    bad("styles:\n  - 5", "a rule is a mapping")
    bad("styles: 5", "'styles:' is a list of rules")
    bad("- 1", "a stylesheet is a mapping")
    bad("rules: []", "a stylesheet has only 'styles:'")
    bad("styles:\n  - classes: a\n    style: {opacity: 1}", "'classes:' is a list of names")
    bad("styles:\n  - widget: Text\n    name: 5\n    style: {opacity: 1}", "'name:' is a node's name")


def test_selectors_must_be_properties_the_widget_declares_and_values_it_allows():
    W.register_widget(WidgetDecl("Btn2", {"variant": Property("enum", choices=("filled", "text"), default="filled")}, parts=("label",)))
    try:
        sheet("styles:\n  - widget: Btn2\n    variant: text\n    part: label\n    style: {opacity: 1}")
        err = bad("styles:\n  - widget: Btn2\n    variant: tonal\n    style: {opacity: 1}", "Btn2.variant is one of filled, text, not 'tonal'")
        assert err.line == 3
        bad("styles:\n  - widget: Btn2\n    size: large\n    style: {opacity: 1}", "Btn2 has no property 'size' to select on")
        err = bad("styles:\n  - widget: Btn2\n    part: lable\n    style: {opacity: 1}", "Btn2 has no part 'lable'")
        assert "parts: label" in str(err)
    finally:
        W.unregister_widget("Btn2")
    bad("styles:\n  - variant: tonal\n    style: {opacity: 1}", "'variant:' needs a 'widget:'")
    bad("styles:\n  - part: label\n    style: {opacity: 1}", "'part:' needs a 'widget:'")
    sheet("styles:\n  - widget: SomeView\n    variant: anything\n    part: whatever\n    style: {opacity: 1}")  # a view is checked when it is composed


def test_foreground_is_an_extra_and_the_error_names_who_accepts_it():
    sheet("styles:\n  - widget: Text\n    style: {foreground: primary}\n  - widget: SomeView\n    style: {foreground: primary}")
    err = bad("styles:\n  - widget: Container\n    style: {foreground: primary}", "Container: style 'foreground' is not valid here")
    assert "widgets that accept it: Icon, Link, LoadingIndicator, Svg, Text, TextInput" in str(err) and (err.line, err.column) == (3, 12)
    err = bad("styles:\n  - widget: Container\n    style: {widht: 1}", "style 'widht' is not valid here")
    assert "did you mean 'width'" in str(err)


def test_an_expression_in_a_rule_is_checked_where_it_is_written():
    sheet("styles:\n  - widget: Text\n    style: {width: '{{ height / 2 }}'}")
    err = bad("styles:\n  - widget: Text\n    style: {width: '{{ height / }}'}", "syntax error")
    assert err.line == 3


def test_a_stylesheet_file_is_read_with_positions(tmp_path):
    path = tmp_path / "App_Stylesheet.yaml"
    path.write_text("styles:\n  - widget: Text\n    style: {opacity: 0.5}\n")
    assert load_rule_sheet(path).rules[0].widget == "Text"
    path.write_text("styles:\n  - widget: Text\n    state: nope\n    style: {opacity: 0.5}\n")
    with pytest.raises(LoadError, match=r"App_Stylesheet.yaml:3:12"):
        load_rule_sheet(path)


# -- specificity -----------------------------------------------------------------------------------------------------------


def rule(**kw):
    kw.setdefault("style", {})
    return Rule(kw.pop("widget", None), kw.pop("style"), **kw)


@pytest.mark.parametrize("weaker, stronger", [
    (rule(widget="Text"), rule(widget="Text", state="hovered")),                       # a state beats the widget alone
    (rule(widget="Text", state="hovered"), rule(widget="Text", selectors={"variant": "a"})),   # a property beats a state
    (rule(widget="Text", selectors={"variant": "a"}), rule(widget="Text", selectors={"variant": "a", "size": "s"})),   # more properties win
    (rule(widget="Text", classes=frozenset({"a"})), rule(widget="Text", classes=frozenset({"a"}), selectors={"size": "s"})),
    (rule(widget="Text", selectors={"variant": "a", "size": "s", "shape": "r"}), rule(widget="Text", name="x")),   # a name beats everything
    (rule(), rule(widget="Text")),                                                      # no widget is the weakest
])
def test_specificity_orders_name_then_property_count_then_state_then_widget(weaker, stronger):
    assert weaker.specificity < stronger.specificity
    first, second = rule(order=0), rule(order=1)
    assert ordered([stronger, weaker])[-1] is stronger
    assert ordered([second, first]) == [first, second]  # a tie goes to the later rule


# -- resolution ------------------------------------------------------------------------------------------------------------


def style(comp, id="root"):
    return comp.find(id).effective_style()


def test_a_widget_rule_styles_the_nodes_of_that_widget_and_inline_wins_only_for_its_own_fields():
    comp = compose("widget: Container\nchildren:\n  - {widget: Rect, name: a, style: {width: 5}}\n  - {widget: Container, name: b}\n",
                   ["styles:\n  - widget: Rect\n    style: {width: 99, height: 40, corner_radius: 4}\n"])
    assert style(comp, "root.a") == {"width": 5, "height": 40, "corner_radius": 4}  # inline width over the rule; the rest from the rule
    assert style(comp, "root.b") == {}


def test_a_later_layer_beats_an_earlier_one_whatever_the_specificity_and_a_later_rule_wins_a_tie():
    comp = compose("widget: Rect\nname: root\nclasses: [big]\n",
                   ["styles:\n  - widget: Rect\n    classes: [big]\n    name: root\n    style: {width: 1, height: 1}\n",
                    "styles:\n  - widget: Rect\n    style: {width: 2}\n  - widget: Rect\n    style: {width: 3}\n"])
    assert style(comp) == {"width": 3, "height": 1}  # the upper layer's later rule; height only the lower layer gave


def test_inside_a_layer_the_most_specific_rule_wins_whatever_the_order():
    comp = compose("widget: Rect\nname: me\nclasses: [big]\n",
                   ["styles:\n  - name: me\n    style: {width: 1}\n  - widget: Rect\n    classes: [big]\n    style: {width: 2, height: 2}\n"
                    "  - widget: Rect\n    style: {width: 3, height: 3, opacity: 0.5}\n  - classes: [big]\n    style: {opacity: 0.1, corner_radius: 7}\n"])
    assert style(comp) == {"width": 1, "height": 2, "opacity": 0.1, "corner_radius": 7}  # a class rule beats a widget rule alone


def test_classes_must_all_be_on_the_node():
    comp = compose("widget: Container\nchildren:\n  - {widget: Rect, name: a, classes: [x]}\n  - {widget: Rect, name: b, classes: [x, y]}\n",
                   ["styles:\n  - widget: Rect\n    classes: [x, y]\n    style: {width: 9}\n"])
    assert style(comp, "root.a") == {} and style(comp, "root.b") == {"width": 9}


BTN = ("params:\n  label: {type: str, default: ''}\n  variant: {type: str, default: filled}\n  height: {type: int, default: 40}\n"
       "  selected: {type: bool, default: false}\nwidget: Rect\nstyle: {width: 100}\nchildren:\n  - {widget: Text, name: label, text: '{{ label }}'}\n"
       "  - {widget: Icon, name: icon, icon: home}\n")


def test_a_variant_selects_on_the_params_of_a_view_call_and_follows_them():
    vm = VM()
    comp = compose("widget: Container\nchildren:\n  - {widget: Btn, name: b, variant: '{{ mode }}'}\n  - {widget: Btn, name: c, variant: text}\n",
                   ["styles:\n  - widget: Btn\n    style: {corner_radius: 4}\n  - widget: Btn\n    variant: filled\n    style: {background: primary}\n"
                    "  - widget: Btn\n    variant: text\n    style: {background: transparent}\n"], {"Btn": BTN}, vm)
    assert style(comp, "root.b") == {"width": 100, "corner_radius": 4, "background": "primary"}   # inline width, rules for the rest
    assert style(comp, "root.c")["background"] == "transparent"
    vm.mode.set("text")  # the variant is a Signal: the look changes with it
    assert style(comp, "root.b")["background"] == "transparent"
    vm.mode.set("filled")
    assert style(comp, "root.b")["background"] == "primary"


def test_a_part_rule_styles_the_named_node_inside_that_widget_only():
    comp = compose("widget: Container\nchildren:\n  - {widget: Btn, name: b, label: Go}\n  - {widget: Text, name: label, text: x}\n",
                   ["styles:\n  - widget: Btn\n    part: label\n    style: {foreground: on_primary}\n  - widget: Btn\n    part: icon\n    style: {foreground: red}\n"],
                   {"Btn": BTN})
    assert style(comp, "root.b.label") == {"foreground": "on_primary"} and style(comp, "root.b.icon") == {"foreground": "red"}
    assert style(comp, "root.label") == {} and style(comp, "root.b") == {"width": 100}


def test_slot_content_belongs_to_the_caller_not_to_the_widget_it_is_passed_to():
    box = "widget: Container\nchildren:\n  - widget: Slot\n"
    comp = compose("widget: Container\nchildren:\n  - widget: Box\n    name: b\n    children:\n      - {widget: Text, name: label, text: x}\n",
                   ["styles:\n  - widget: Box\n    part: label\n    style: {opacity: 0.5}\n"], {"Box": box})
    assert style(comp, "root.b.label") == {}


def test_a_rule_value_may_read_the_widgets_own_params():
    comp = compose("widget: Container\nchildren:\n  - {widget: Btn, name: b, height: 30}\n",
                   ["styles:\n  - widget: Btn\n    style: {corner_radius: '{{ height / 2 }}'}\n"], {"Btn": BTN})
    assert style(comp, "root.b")["corner_radius"] == 15


def test_a_call_site_style_beats_the_rules_and_a_rule_beats_nothing_inline():
    comp = compose("widget: Container\nchildren:\n  - {widget: Btn, name: b, style: {width: 7, background: red}}\n",
                   ["styles:\n  - widget: Btn\n    style: {width: 1, background: primary, corner_radius: 4}\n"], {"Btn": BTN})
    assert style(comp, "root.b") == {"width": 7, "background": "red", "corner_radius": 4}


def test_state_rules_follow_the_interaction_signals_and_the_widgets_own_properties():
    comp = compose("widget: Container\nchildren:\n  - {widget: Btn, name: b, selected: '{{ on }}'}\n",
                   ["styles:\n  - widget: Btn\n    style: {background: surface}\n  - widget: Btn\n    state: hovered\n    style: {background: hover}\n"
                    "  - widget: Btn\n    state: selected\n    style: {opacity: 0.5}\n  - widget: Btn\n    state: pressed\n    style: {background: down}\n"],
                   {"Btn": BTN})
    inst = comp.find("root.b")
    assert style(comp, "root.b")["background"] == "surface" and "opacity" not in style(comp, "root.b")
    inst.interaction_signal("hovered").set(True)
    assert style(comp, "root.b")["background"] == "hover"
    inst.interaction_signal("pressed").set(True)
    assert style(comp, "root.b")["background"] == "down"   # pressed and hovered: the later rule of the same specificity
    inst.interaction_signal("pressed").set(False)
    inst.interaction_signal("hovered").set(False)
    comp.root.children  # noqa: B018
    comp2 = compose("widget: Btn\nname: b\nselected: true\n", ["styles:\n  - widget: Btn\n    state: selected\n    style: {opacity: 0.5}\n"], {"Btn": BTN})
    assert style(comp2)["opacity"] == 0.5


def test_hovered_focused_and_pressed_are_names_an_expression_can_read_but_not_write():
    comp = compose("widget: Rect\ninteraction: true\nstyle: {background: \"{{ 'hover' if hovered else 'rest' }}\"}\n"
                   "handlers: {on_click: 'hovered = True'}\n", [])
    assert style(comp)["background"] == "rest"
    comp.root.interaction_signal("hovered").set(True)
    assert style(comp)["background"] == "hover"
    with pytest.raises(Exception, match="not writable"):
        comp.root.fire("on_click")
    with pytest.raises(LoadError, match="reserved name"):
        compose("widget: Rect\nstate: {hovered: false}\n", [])


def test_every_state_a_rule_can_name_is_documented():
    assert STATES == ("hovered", "focused", "focus_visible", "pressed", "disabled", "selected", "checked", "expanded", "error", "read_only", "visited")


def test_an_instance_with_no_matching_rule_makes_no_computed_and_rules_are_released_on_dispose():
    comp = compose("widget: Container\nchildren:\n  - {widget: Rect, name: a}\n  - {widget: Text, name: t}\n", ["styles:\n  - widget: Rect\n    style: {width: 4}\n"])
    assert comp.find("root.a")._rules is not None and comp.find("root.t")._rules is None and comp.root._rules is None
    comp2 = compose("widget: Rect\nclasses: [x]\n", ["styles:\n  - widget: Rect\n    style: {width: '{{ mode.upper() and 4 }}'}\n"])
    vm = comp2.root.identities[0].scope.root
    assert vm.mode._subscribers
    comp2.dispose()
    assert vm.mode._subscribers == []


# -- on screen -------------------------------------------------------------------------------------------------------------


def test_a_hover_rule_changes_the_drawn_node_when_the_pointer_enters_and_leaves():
    s = sheet("styles:\n  - widget: Rect\n    style: {background: '#112233'}\n  - widget: Rect\n    state: hovered\n    style: {background: '#AABBCC'}\n")
    doc = parse_view("widget: Rect\nstyle: {width: 100, height: 60}\n", "Main_View.yaml")
    bindings = Bindings()
    view = open_composed(doc, bindings, rules=[s], theme_seed=(103, 80, 164, 255))
    rest = view.node("root").get("fill")
    view.window.advance(16)
    view.window.simulate("pointer_move", x=20, y=20)
    hovered = view.node("root").get("fill")
    assert hovered != rest
    view.window.simulate("pointer_move", x=900, y=900)
    assert view.node("root").get("fill") == rest


def test_the_app_uses_a_stylesheet_in_the_rule_shape_for_new_views(tmp_path):
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text("widget: Rect\nstyle: {width: 50, height: 20}\n")
    app = App(root=tmp_path, stylesheet_spec={"styles": [{"widget": "Rect", "style": {"background": "#112233"}}]})
    opened = app.open_view("Main")
    assert opened.node("root").get("fill") == (17, 34, 51, 255)


def test_a_name_selector_matches_only_the_node_with_that_name():
    comp = compose("widget: Container\nchildren:\n  - {widget: Rect, name: a}\n  - {widget: Rect, name: b}\n  - widget: Rect\n",
                   ["styles:\n  - widget: Rect\n    name: a\n    style: {width: 9}\n"])
    assert style(comp, "root.a") == {"width": 9} and style(comp, "root.b") == {} and style(comp, "root.children[2]") == {}


def test_the_root_of_a_view_is_the_widget_itself_not_a_part_of_it():
    named = "params: []\nname: tag\nwidget: Rect\nchildren:\n  - {widget: Text, name: inner, text: x}\n"
    comp = compose("widget: Container\nchildren:\n  - {widget: Named, name: n}\n",
                   ["styles:\n  - widget: Named\n    part: tag\n    style: {width: 1}\n  - widget: Named\n    style: {height: 2}\n  - widget: Named\n    part: inner\n    style: {opacity: 0.5}\n"],
                   {"Named": named})
    assert style(comp, "root.n") == {"height": 2} and style(comp, "root.n.inner") == {"opacity": 0.5}


def test_a_pressed_rule_follows_the_pointer_down_and_up_on_screen():
    s = sheet("styles:\n  - widget: Rect\n    style: {background: '#112233'}\n  - widget: Rect\n    state: pressed\n    style: {background: '#AABBCC'}\n")
    view = open_composed(parse_view("widget: Rect\nstyle: {width: 100, height: 60}\n", "Main_View.yaml"), Bindings(), rules=[s], theme_seed=(103, 80, 164, 255))
    rest = view.node("root").get("fill")
    view.window.advance(16)
    view.window.simulate("pointer_move", x=20, y=20)
    view.window.simulate("pointer_down", x=20, y=20)
    assert view.node("root").get("fill") != rest
    view.window.simulate("pointer_up", x=20, y=20)
    assert view.node("root").get("fill") == rest
