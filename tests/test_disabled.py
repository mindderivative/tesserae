"""M70 (#19): `disabled` on any node, as a `disabled:` key or a binding.
Disabled, a node is announced disabled, isn't focusable, shows no state
layer or ring, fades to 38% of its style's opacity, and its handlers don't
run (the click is still taken, as a disabled button swallows it). The View
holds the state and applies it after every build and patch, so a re-theme,
restyle or reconcile never undoes it. A control keeps its own `disabled`.
"""

import pytest
import yaml

from tesserae import App, Signal, View, ViewModel
from tesserae.spec import expand_components_to_spec

DISABLED_OPACITY = 0.38  # MD3's disabled content opacity

SEED = (0x67, 0x50, 0xA4, 0xFF)


def _button(node_id="b", **extra):
    return {"id": node_id, "kind": "Rect", "style": {"width": 40, "height": 40, "background": "#6750A4"},
            "handlers": {"on_click": "go"}, **extra}


def _spec(*children, **root):
    return {"id": "root", "kind": "Container", "style": {"width": 200, "height": 100}, "children": list(children), **root}


class VM(ViewModel):
    def __init__(self, view, off=True):
        self.off, self.clicks = Signal(off), []
        super().__init__(view)

    def go(self):
        self.clicks.append(1)


def _state(view, node_id="b"):
    node = view.node(node_id)
    interaction = view.interaction(node_id)
    return (node.get("disabled"), node.get("focusable"), round(node.get("opacity"), 3),
            interaction.enabled if interaction is not None else None)


OFF = (True, False, DISABLED_OPACITY, False)
ON = (False, True, 1.0, True)


def test_a_disabled_key_disables_a_clickable():
    view = View(_spec(_button(disabled=True)), theme_seed=SEED)
    vm = VM(view)
    assert _state(view) == OFF
    view.click(view.node("b"))
    assert vm.clicks == []


def test_a_binding_disables_and_enables_it():
    view = View(_spec(_button(bindings={"disabled": "{{ off.get() }}"})), theme_seed=SEED)
    vm = VM(view)
    assert _state(view) == OFF
    view.click(view.node("b"))
    vm.off.set(False)
    assert _state(view) == ON
    view.click(view.node("b"))
    assert vm.clicks == [1]
    vm.off.set(True)
    view.node("b").focus()
    view.window.simulate("key_down", key="enter")
    assert _state(view) == OFF and vm.clicks == [1]  # no focus, no keyboard click


def test_a_disabled_child_swallows_the_click():
    card = {"id": "card", "kind": "Container", "style": {"width": 100, "height": 100},
            "handlers": {"on_click": "go"}, "children": [_button(disabled=True)]}
    view = View(_spec(card), theme_seed=SEED)
    vm = VM(view)
    view.click(view.node("b"))
    assert vm.clicks == []  # neither the button nor the card behind it


def test_it_fades_from_the_styles_opacity_and_back():
    view = View(_spec(_button(bindings={"disabled": "{{ off.get() }}"}, style={
        "width": 40, "height": 40, "background": "#6750A4", "opacity": 0.5})), theme_seed=SEED)
    vm = VM(view)
    assert view.node("b").get("opacity") == pytest.approx(0.5 * DISABLED_OPACITY)
    vm.off.set(False)
    assert view.node("b").get("opacity") == pytest.approx(0.5)


def test_a_re_theme_restyle_and_reconcile_keep_it_disabled():
    spec = _spec(_button(bindings={"disabled": "{{ off.get() }}"}))
    view = View(spec, theme_seed=SEED)
    VM(view)
    view.set_theme(theme_seed=SEED, dark=True)
    assert _state(view) == OFF
    view.set_stylesheet({"styles": [{"kind": "Rect", "style": {"corner_radius": 4}}]})
    assert _state(view) == OFF
    view.reconcile(_spec(_button(bindings={"disabled": "{{ off.get() }}"}, style={
        "width": 60, "height": 40, "background": "#6750A4"})))
    assert _state(view) == OFF


def test_a_binding_that_goes_falls_back_to_the_key():
    view = View(_spec(_button(bindings={"disabled": "{{ off.get() }}"})), theme_seed=SEED)
    VM(view)
    view.reconcile(_spec(_button()))  # no key, no binding: enabled
    assert _state(view) == ON
    view.reconcile(_spec(_button(disabled=True)))
    assert _state(view) == OFF
    view.reconcile(_spec(_button()))
    assert _state(view) == ON


def test_a_plain_node_and_a_text_field():
    rect = {"id": "r", "kind": "Rect", "style": {"width": 10, "height": 10, "background": "#000000"}, "disabled": True}
    field = {"id": "f", "kind": "TextField", "text": {"content": "", "font_family": "Roboto", "font_size": 14},
             "style": {"width": 100, "height": 30, "foreground": "#000000", "background": "#FFFFFF"},
             "bindings": {"disabled": "{{ off.get() }}"}}
    view = View(_spec(rect, field), theme_seed=SEED)
    vm = VM(view)
    assert view.node("r").get("disabled") is True and view.node("r").get("focusable") is False
    view.reconcile(_spec({**rect, "disabled": False}, field))
    assert view.node("r").get("disabled") is False and view.node("r").get("focusable") is False  # not a Tab stop
    assert view.node("f").get("disabled") is True and view.node("f").get("focusable") is False  # its input
    vm.off.set(False)
    assert view.node("f").get("focusable") is True and view.node("f").get("disabled") is False


def test_a_fragment_button_binds_it_through_its_call():  # with M69
    spec = expand_components_to_spec(yaml.safe_dump(_spec({
        "id": "b", "component": "ButtonFilled", "with": {"label": "Back", "width": 96, "height": 40, "corner_radius": 20},
        "handlers": {"on_click": "go"}, "bindings": {"disabled": "{{ off.get() }}"}})))
    view = View(spec, theme_seed=SEED)
    vm = VM(view)
    view.click(view.node("b"))
    assert _state(view) == OFF and vm.clicks == []
    vm.off.set(False)
    view.click(view.node("b"))
    assert vm.clicks == [1]


def test_a_back_button_follows_can_go_back():  # the case M66 found
    app = App(width=300, height=200)

    class Home(ViewModel):
        def go(self):
            self.app.back()

    home = View(_spec(_button(bindings={"disabled": "{{ not app.can_go_back.get() }}"})), window=app.window)
    app.register("Home", home, Home(home))
    other = View(_spec(), window=app.window)
    app.register("Other", other, ViewModel(other))
    app.show("Home")
    assert home.node("b").get("disabled") is True  # nothing to go back to
    app.navigate("Other")
    assert home.node("b").get("disabled") is False
    app.back()  # Home is the first entry again
    assert home.node("b").get("disabled") is True


def test_a_controls_key_is_its_own():
    view = View(_spec({"id": "s", "kind": "Switch", "style": {}, "disabled": True}), theme_seed=SEED)
    assert view.control("s").disabled.get() is True
    assert view.control("s").node.get("opacity") == 1.0  # its own disabled look, not the View's fade
    view.reconcile(_spec({"id": "s", "kind": "Switch", "style": {}}))
    assert view.control("s").disabled.get() is False


def test_a_non_boolean_binding_is_named():
    view = View(_spec(_button(bindings={"disabled": "{{ 1 }}"})), theme_seed=SEED)
    with pytest.raises(ValueError, match='widget property "disabled" expects a boolean binding'):
        VM(view)
