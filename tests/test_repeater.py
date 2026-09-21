"""Real, repeatable coverage for `tesserae.Repeater` -- automatic, keyed
add/remove diffing over a list `Signal`, built on top of `tesserae
.instantiate`/`Component.remove()` (TRE M43).
"""

import importlib.util
import sys

import pytest

from tesserae import Repeater, Signal, View

PARENT_VIEW = """
id: root
kind: Container
style: {flex_direction: Column, width: 300, height: 200, gap: 8, padding: 8}
children:
  - id: item_list
    kind: Container
    style: {flex_direction: Column, gap: 4, width: 280, height: 180}
"""

ITEM_VIEW = """
id: root
kind: Rect
style: {width: 260, height: 32, background: "#112233"}
"""


def write(tmp_path, yaml, name):
    path = tmp_path / name
    path.write_text(yaml)
    return str(path)


def load_viewmodel_class(tmp_path, filename, class_name, extra_params=()):
    assigns = "".join(f"        self.{name} = {name}\n" for name in extra_params)
    extra_args = "".join(f", {name}" for name in extra_params)
    path = tmp_path / filename
    path.write_text(
        f"from tesserae import Signal, ViewModel\n\n\n"
        f"class {class_name}(ViewModel):\n"
        f"    def __init__(self, view{extra_args}):\n"
        f"        self.value = Signal(0)\n"
        f"{assigns}"
        f"        super().__init__(view)\n"
    )
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return getattr(module, class_name)


def make_repeater(tmp_path, items):
    parent_path = write(tmp_path, PARENT_VIEW, "Parent_View.yaml")
    item_path = write(tmp_path, ITEM_VIEW, "Item_View.yaml")
    # `Repeater`'s own default `args=lambda item: (item,)` forwards the
    # item itself, matching this fixture's own extra `item` param.
    vm_cls = load_viewmodel_class(
        tmp_path, "Item_ViewModel.py", "ItemViewModel", extra_params=("item",)
    )

    view = View(parent_path)
    container = view.node("item_list")
    items_signal = Signal(items)

    repeater = Repeater(view, items_signal, item_path, vm_cls, container)
    return repeater, items_signal


def test_initial_sync_creates_one_instance_per_item(tmp_path):
    repeater, _items = make_repeater(tmp_path, ["a", "b", "c"])
    assert len(repeater) == 3
    assert {key for key, _c, _vm in repeater} == {"a", "b", "c"}


def test_adding_a_key_instantiates_a_new_component(tmp_path):
    repeater, items = make_repeater(tmp_path, ["a", "b"])
    items.update(lambda lst: [*lst, "c"])
    assert len(repeater) == 3
    assert repeater["c"] is not None


def test_removing_a_key_removes_its_component(tmp_path):
    repeater, items = make_repeater(tmp_path, ["a", "b", "c"])
    items.update(lambda lst: [i for i in lst if i != "b"])
    assert len(repeater) == 2
    assert {key for key, _c, _vm in repeater} == {"a", "c"}
    with pytest.raises(KeyError):
        repeater["b"]


def test_surviving_instances_keep_their_identity_across_a_sync(tmp_path):
    repeater, items = make_repeater(tmp_path, ["a", "b"])
    component_a_before, vm_a_before = repeater["a"]

    items.update(lambda lst: [*lst, "c"])

    component_a_after, vm_a_after = repeater["a"]
    assert component_a_after is component_a_before
    assert vm_a_after is vm_a_before


def test_a_sync_with_the_same_key_set_touches_nothing(tmp_path):
    repeater, items = make_repeater(tmp_path, ["a", "b"])
    before = dict(repeater._by_key)

    items.set(["b", "a"])  # same keys, different order -- no add/remove

    after = dict(repeater._by_key)
    assert before == after


def test_remove_tears_down_every_instance_and_stops_syncing(tmp_path):
    repeater, items = make_repeater(tmp_path, ["a", "b"])
    repeater.remove()
    assert len(repeater) == 0

    items.update(lambda lst: [*lst, "c"])  # must not resurrect the repeater
    assert len(repeater) == 0


def test_args_forwards_per_item_data_to_the_viewmodel(tmp_path):
    parent_path = write(tmp_path, PARENT_VIEW, "Parent_View.yaml")
    item_path = write(tmp_path, ITEM_VIEW, "Item_View.yaml")
    vm_cls = load_viewmodel_class(
        tmp_path, "Item_ViewModel.py", "ItemViewModel", extra_params=("label",)
    )

    view = View(parent_path)
    container = view.node("item_list")
    items_signal = Signal([{"id": "a", "label": "Alpha"}])

    repeater = Repeater(
        view,
        items_signal,
        item_path,
        vm_cls,
        container,
        key=lambda item: item["id"],
        args=lambda item: (item["label"],),
    )

    _component, vm = repeater["a"]
    assert vm.label == "Alpha"


def test_repeater_rejects_a_mismatched_naming_pair(tmp_path):
    parent_path = write(tmp_path, PARENT_VIEW, "Parent_View.yaml")
    item_path = write(tmp_path, ITEM_VIEW, "item.yaml")  # missing _View suffix
    vm_cls = load_viewmodel_class(tmp_path, "Item_ViewModel.py", "ItemViewModel")

    view = View(parent_path)
    container = view.node("item_list")
    items_signal = Signal([])

    with pytest.raises(ValueError, match="_View.yaml"):
        Repeater(view, items_signal, item_path, vm_cls, container)
