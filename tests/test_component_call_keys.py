"""M69 (#18): a `component:` call also takes `handlers:`, `bindings:`,
`two_way:`, `a11y:`, `interaction:` and `classes:`, put on the fragment's
root: mappings merged key by key (the call's win), `two_way:` replaced,
`classes:` added. They're the view's, so their `{{ }}` stay the
ViewModel's bindings. So `component: ButtonFilled` can be clicked.
"""

from pathlib import Path

import pytest
import yaml

import tesserae.spec.expand as expand_module

from tesserae import Signal, View, ViewModel
from tesserae.spec import expand_components_to_spec
from tesserae.spec.expand import ComponentError

SEED = (0x67, 0x50, 0xA4, 0xFF)
SAVE = {"id": "save", "component": "ButtonFilled", "with": {"label": "Save", "width": 120, "height": 40, "corner_radius": 20}}


def _expand(*children, **kwargs):
    return expand_components_to_spec(yaml.safe_dump({"id": "root", "kind": "Container", "children": list(children)}),
                                     **kwargs)


class VM(ViewModel):
    def __init__(self, view):
        self.saved, self.fade, self.note = [], Signal(0.5), Signal("hi")
        super().__init__(view)

    def save(self):
        self.saved.append(1)


def test_a_button_fragment_takes_a_click_handler():
    view = View(_expand({**SAVE, "handlers": {"on_click": "save"}, "a11y": {"label": "Save the note"}}), theme_seed=SEED)
    vm = VM(view)
    node = view.node("save")
    assert (node.get("role"), node.get("focusable"), node.get("label")) == ("button", True, "Save the note")
    view.click(node)
    node.focus()
    view.window.simulate("key_down", key="enter")
    assert vm.saved == [1, 1]
    assert view.interaction("save") is not None  # the state layer and ripple come with it


def test_bindings_and_classes_reach_the_root_and_the_calls_braces_are_the_viewmodels():
    spec = _expand({**SAVE, "bindings": {"opacity": "{{ fade.get() }}"}, "classes": ["primary"],
                    "a11y": {"label": "{{ label }}"}})
    root = spec["children"][0]
    assert root["a11y"] == {"label": "{{ label }}"}  # not the fragment's `label` param: the view's own
    assert root["bindings"] == {"opacity": "{{ fade.get() }}"} and root["classes"] == ["primary"]
    view = View(_expand({**SAVE, "bindings": {"opacity": "{{ fade.get() }}"}}), theme_seed=SEED)
    vm = VM(view)
    assert view.node("save").get("opacity") == 0.5
    vm.fade.set(1.0)
    assert view.node("save").get("opacity") == 1.0


def test_they_merge_with_the_roots_own_and_the_call_wins(tmp_path):
    (tmp_path / "Chip_Component.yaml").write_text(yaml.safe_dump({
        "params": ["text"], "id": "root", "kind": "Rect", "classes": ["chip"],
        "style": {"width": 60, "height": 24, "background": "surface"},
        "a11y": {"label": "Chip", "role": "button"}, "handlers": {"on_hover_enter": "hovered"},
        "bindings": {"opacity": "{{ text }}"},
    }))
    spec = _expand({"id": "c", "component": "Chip", "with": {"text": 0.7},
                    "a11y": {"label": "Filter"}, "handlers": {"on_click": "pick"}, "classes": ["active", "chip"]},
                   component_dirs=[tmp_path])
    root = spec["children"][0]
    assert root["a11y"] == {"label": "Filter", "role": "button"}  # merged, the call's label winning
    assert root["handlers"] == {"on_hover_enter": "hovered", "on_click": "pick"}
    assert root["classes"] == ["chip", "active"]  # added after the root's own, not repeated
    assert root["bindings"] == {"opacity": 0.7}  # the fragment's own, substituted as before


def test_interaction_sets_the_feedback_colour():
    view = View(_expand({**SAVE, "handlers": {"on_click": "save"}, "interaction": {"color": "#FF0000"}}), theme_seed=SEED)
    VM(view)
    assert view.interaction("save").tint == (255, 0, 0, 255)


def test_two_way_replaces_the_roots(tmp_path):
    (tmp_path / "Field_Component.yaml").write_text(yaml.safe_dump({
        "params": [], "id": "root", "kind": "TextField", "two_way": "text",
        "text": {"content": "", "font_family": "Roboto", "font_size": 14},
        "style": {"width": 120, "height": 32, "foreground": "#000000", "background": "#FFFFFF"},
    }))
    spec = _expand({"id": "f", "component": "Field", "bindings": {"text": "{{ note.get() }}"}, "two_way": "text"},
                   component_dirs=[tmp_path])
    view = View(spec, theme_seed=SEED)
    vm = VM(view)
    field = view.node("f")
    assert field.get("text") == "hi"
    field.focus()
    view.window.simulate("input", text="!")
    assert vm.note.get() == field.get("text") and vm.note.get() != "hi"


def test_every_repeated_item_gets_them():
    spec = _expand({"id": "b", "component": "ButtonFilled", "with": {"width": 80, "height": 40, "corner_radius": 20},
                    "repeat": [{"label": "One"}, {"label": "Two"}], "handlers": {"on_click": "save"}})
    assert [c["handlers"] for c in spec["children"]] == [{"on_click": "save"}] * 2
    view = View(spec, theme_seed=SEED)
    vm = VM(view)
    view.click(view.node("b.1"))
    assert vm.saved == [1]


def test_a_call_inside_a_fragment_takes_them_too(tmp_path):
    (tmp_path / "Toolbar_Component.yaml").write_text(yaml.safe_dump({
        "params": [], "id": "root", "kind": "Container",
        "children": [{**SAVE, "handlers": {"on_click": "save"}}],
    }))
    built_in = Path(expand_module.__file__).parent / "components"
    spec = _expand({"id": "t", "component": "Toolbar"}, component_dirs=[tmp_path, built_in])
    assert spec["children"][0]["children"][0]["handlers"] == {"on_click": "save"}


def test_a_reconcile_rewires_a_changed_handler():
    class Two(VM):
        def other(self):
            self.saved.append(2)

    view = View(_expand({**SAVE, "handlers": {"on_click": "save"}}), theme_seed=SEED)
    vm = Two(view)
    view.reconcile(_expand({**SAVE, "handlers": {"on_click": "other"}}))
    view.click(view.node("save"))
    assert vm.saved == [2]


@pytest.mark.parametrize("extra, message", [
    ({"handlers": ["save"]}, "`handlers:` on a `component:` node must be a mapping"),
    ({"a11y": "Save"}, "`a11y:` on a `component:` node must be a mapping"),
    ({"two_way": ["text"]}, "`two_way:` on a `component:` node must be a property name"),
    ({"classes": "primary"}, "`classes:` on a `component:` node must be a list of names"),
    ({"style": {"width": 10}}, r"takes `id:`, `with:`, `repeat:`, and `handlers:`, .* got \['style'\]"),
])
def test_bad_call_keys_are_named(extra, message):
    with pytest.raises(ComponentError, match=message):
        _expand({**SAVE, **extra})
