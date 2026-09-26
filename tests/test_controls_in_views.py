"""M40 Phase 5: the eight YAML control kinds are Tesserae's MD3 controls
inside a `View` -- bindings, `two_way:`, handlers, reconcile, re-theming
and teardown go to the controls (`tesserae.controls`).
"""

import math

import pytest

import tesserae
from tesserae import App, Signal, View, tokens

SEED = (0x67, 0x50, 0xA4, 0xFF)


def _root(*children):
    return {"id": "root", "kind": "Container", "style": {"flex_direction": "vertical"}, "children": list(children)}


class VM(tesserae.ViewModel):
    def __init__(self, view):
        self.on = Signal(False)
        self.level = Signal(0.25)
        self.hour = Signal(9)
        self.changes = 0
        self.clicks = 0
        super().__init__(view)

    def changed(self):
        self.changes += 1

    def clicked(self):
        self.clicks += 1


def _view(*children, **kwargs):
    view = View(_root(*children), **kwargs)
    view.window.advance(16)
    return view, VM(view), view.window


def _frames(window, ms):
    for _ in range(math.ceil(ms / 16)):
        window.advance(16)


def test_a_yaml_switch_toggles_writes_back_and_fires_on_change_for_the_user_only():
    switch = {"id": "s", "kind": "Switch", "selected": False, "style": {},
              "bindings": {"selected": "{{ on.get() }}"}, "two_way": "selected", "handlers": {"on_change": "changed"}}
    view, vm, window = _view(switch)
    vm.on.set(True)
    assert view.control("s").selected.get() is True and vm.changes == 0
    window.simulate("click", node=view.node("s"))
    assert vm.on.get() is False and vm.changes == 1


def test_a_yaml_slider_binds_its_value_both_ways():
    slider = {"id": "sl", "kind": "Slider", "value": 0.0, "style": {"width": 220},
              "bindings": {"value": "{{ level.get() }}"}, "two_way": "value"}
    view, vm, window = _view(slider)
    control = view.control("sl")
    assert control.value.get() == 0.25
    x, y = view.node("sl").get("layout_x"), view.node("sl").get("layout_y")
    window.simulate("pointer_down", x=x + 10 + 200 * 0.75, y=y + 24)
    window.simulate("pointer_up", x=x + 10 + 200 * 0.75, y=y + 24)
    assert vm.level.get() == pytest.approx(0.75)


def test_a_yaml_dial_binds_its_hour():
    dial = {"id": "d", "kind": "TimePickerDial", "hour": 0, "minute": 0, "style": {"width": 256, "height": 256},
            "bindings": {"hour": "{{ hour.get() }}"}, "two_way": "hour"}
    view, vm, window = _view(dial)
    control = view.control("d")
    assert control.hour.get() == 9
    vm.hour.set(11.0)  # a float bound to an hour is held as a whole number
    assert control.hour.get() == 11 and type(control.hour.get()) is int
    view.node("d").focus()
    window.simulate("key_down", key="arrow_up")
    assert vm.hour.get() == 0  # 11 steps round to 12 AM, and two_way writes it back


def test_a_bad_binding_type_reads_as_tres():
    cb = {"id": "cb", "kind": "Checkbox", "checked": False, "style": {}, "bindings": {"checked": "{{ level.get() }}"}}
    with pytest.raises(ValueError, match='"checked" expects a boolean binding'):
        _view(cb)


def test_on_click_and_the_control_share_the_node():
    cb = {"id": "cb", "kind": "Checkbox", "checked": False, "style": {}, "handlers": {"on_click": "clicked"}}
    view, vm, window = _view(cb)
    window.simulate("click", node=view.node("cb"))
    assert vm.clicks == 1 and view.control("cb").checked.get() is True


def test_radios_with_a_group_exclude_each_other():
    radios = [{"id": f"r{i}", "kind": "RadioButton", "selected": i == 0, "group": "size", "style": {}}
              for i in range(3)]
    loner = {"id": "x", "kind": "RadioButton", "selected": True, "style": {}}
    view, vm, window = _view(*radios, loner)
    window.simulate("click", node=view.node("r2"))
    assert [view.control(f"r{i}").selected.get() for i in range(3)] == [False, False, True]
    assert view.control("x").selected.get() is True  # no group: on its own
    assert [view.node(f"r{i}").get("focusable") for i in range(3)] == [False, False, True]  # one Tab stop


def test_group_is_for_radio_buttons():
    with pytest.raises(ValueError, match="`group:` is a RadioButton's"):
        View(_root({"id": "c", "kind": "Checkbox", "checked": False, "group": "g", "style": {}}))


def test_reconcile_sets_state_from_yaml_and_rebuilds_a_resized_control():
    view, vm, window = _view({"id": "cb", "kind": "Checkbox", "checked": False, "style": {}})
    first = view.control("cb")
    view.reconcile(_root({"id": "cb", "kind": "Checkbox", "checked": True, "style": {}}))
    assert view.control("cb") is first and first.checked.get() is True  # patched in place
    view.reconcile(_root({"id": "cb", "kind": "Checkbox", "checked": True, "style": {"width": 40, "height": 40}}))
    second = view.control("cb")
    assert second is not first and second.node.get("width") == 40.0 and second.checked.get() is True
    assert first._undo == []  # the old one was disposed


def test_removing_a_control_disposes_it_and_frees_its_listeners():
    view, vm, window = _view({"id": "cb", "kind": "Checkbox", "checked": False, "style": {}})
    control = view.control("cb")
    view.reconcile(_root())
    assert control._undo == [] and not any(key[0] == id(control.node) for key in view._events._slots)


def test_a_trial_build_leaves_no_listeners_behind():
    cb = {"id": "cb", "kind": "Checkbox", "checked": False, "style": {}}
    view, vm, window = _view(cb)
    before = set(view._events._slots)
    view.reconcile(_root(cb))  # nothing changes, but it trial-builds a second checkbox first
    assert set(view._events._slots) == before


def test_controls_follow_the_views_theme_and_the_apps_dark_mode():
    cb = {"id": "cb", "kind": "Checkbox", "checked": True, "style": {}}
    view, vm, window = _view(cb, theme_seed=SEED)
    light = tokens.color_scheme(SEED)["primary"]
    assert view.control("cb").box.get("fill") == light
    view.set_theme(theme_seed=SEED, dark=True)
    assert view.control("cb").box.get("fill") == tokens.color_scheme(SEED, dark=True)["primary"] != light


def test_a_restyle_keeps_what_the_user_did():
    view, vm, window = _view({"id": "cb", "kind": "Checkbox", "checked": False, "style": {}})
    window.simulate("click", node=view.node("cb"))
    view.set_stylesheet({"styles": [{"kind": "Checkbox", "style": {"margin": 4}}]})
    assert view.control("cb").checked.get() is True  # not the YAML's `false`
    assert view.node("cb").get("margin_top") == 4.0


def test_the_indicators_bind_their_value():
    bar = {"id": "p", "kind": "LinearProgress", "value": 0.0, "style": {"width": 200, "height": 4},
           "bindings": {"value": "{{ level.get() }}"}}
    view, vm, window = _view(bar)
    vm.level.set(0.5)
    _frames(window, 300)
    assert view.control("p").value.get() == 0.5 and view.node("p").get("value") == 0.5


def test_the_todo_list_checkbox_ticks(tmp_path):
    import importlib.util
    import sys
    from pathlib import Path

    directory = Path(__file__).resolve().parent.parent / "examples" / "todo_list"
    for name in ("TodoItem_ViewModel", "Todo_ViewModel"):
        spec = importlib.util.spec_from_file_location(name, directory / f"{name}.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    app = App(width=300, height=300)
    view, vm = app.load(directory / "Todo_View.yaml", sys.modules["Todo_ViewModel"].TodoViewModel)
    window = app.show("Todo")
    window.simulate("click", node=view.node("add_button"))
    window.advance(16)
    (key, component, item_vm), = list(vm.repeater)
    window.simulate("click", node=component.node("check"))
    assert item_vm.done.get() is True
    window.simulate("key_down", key="space")  # focused by the click; the keyboard works too
    window.simulate("key_up", key="space")
    assert item_vm.done.get() is False
