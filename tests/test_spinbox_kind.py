"""M58 (#5): `SpinBox` is a YAML control kind, built with
`tesserae.controls.SpinBox` as the other controls are (M40): `value`,
`min`, `max` and `step`; `value` bindable, clamped to the bounds, and
`two_way:`; `on_change` hears the user's steps; `a11y:` goes to its text
input. The `SpinBox` fragment is now this kind, with its behaviour.
"""

import tesserae
from tesserae import Signal, Theme, View, interaction

SEED = (0x67, 0x50, 0xA4, 0xFF)


class VM(tesserae.ViewModel):
    def __init__(self, view):
        self.count = Signal(3)
        self.off = Signal(False)
        self.changes = 0
        super().__init__(view)

    def changed(self):
        self.changes += 1


def _spin(**fields):
    return {"id": "sb", "kind": "SpinBox", "style": {}, **fields}


def _view(*nodes, **kwargs):
    view = View({"id": "root", "kind": "Container", "children": list(nodes)}, theme_seed=SEED, **kwargs)
    view.window.advance(16)
    return view, VM(view), view.window


def test_a_spin_box_kind_is_the_control_with_its_bounds():
    view, _, _ = _view(_spin(value=5, min=0, max=10, step=5))
    control = view.control("sb")
    assert (control.value.get(), control.min, control.max, control.step) == (5, 0, 10, 5)
    assert control.input.get("text") == "5" and control.node == view.node("sb")
    view.click(control.increment)
    assert control.value.get() == 10
    assert control.increment.get("disabled")  # another step would pass max


def test_value_binds_clamped_and_two_way_writes_back():
    view, vm, window = _view(_spin(value=0, max=10, bindings={"value": "{{ count.get() }}"}, two_way="value",
                                   handlers={"on_change": "changed"}))
    control = view.control("sb")
    assert control.value.get() == 3
    vm.count.set(42)  # past max: the control keeps to its bounds
    assert control.value.get() == 10
    vm.count.set(4)
    assert vm.changes == 0  # a programmatic update isn't a change
    view.click(control.increment)
    assert control.value.get() == 5 and vm.count.get() == 5 and vm.changes == 1  # the user's step, written back


def test_disabled_binds_and_a11y_labels_the_input():
    view, vm, _ = _view(_spin(value=1, bindings={"disabled": "{{ off.get() }}"}, a11y={"label": "Copies"}))
    control = view.control("sb")
    assert control.input.get("label") == "Copies"
    vm.off.set(True)
    view.click(control.increment)
    assert control.value.get() == 1


def test_reconcile_patches_the_value_and_rebuilds_for_new_bounds():
    view, _, _ = _view(_spin(value=2, max=10))
    control = view.control("sb")
    view.reconcile({"id": "root", "kind": "Container", "children": [_spin(value=7, max=10)]})
    assert view.control("sb") is control and control.value.get() == 7  # the same control, patched
    view.reconcile({"id": "root", "kind": "Container", "children": [_spin(value=7, max=5)]})
    rebuilt = view.control("sb")
    assert rebuilt is not control and rebuilt.max == 5 and rebuilt.value.get() == 5
    # the old one was disposed: its buttons' state layers let go of their nodes
    assert all(button not in interaction._INTERACTIVE for button in (control.increment, control.decrement))


def test_it_follows_the_views_theme():
    view, _, _ = _view(_spin(value=1))
    control = view.control("sb")
    light = control.field.get("fill")
    view.set_theme(theme_seed=SEED, dark=True)
    assert control.field.get("fill") != light
    assert control.field.get("fill") == Theme.resolve(theme_seed=SEED, dark=True).role("surface_container_highest")


def test_a_text_value_reads_as_spin_box_does():
    view, _, _ = _view(_spin(value="4"))
    assert view.control("sb").value.get() == 4 and isinstance(view.control("sb").value.get(), int)
