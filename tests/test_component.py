"""Real, repeatable coverage for `tesserae.instantiate` -- the real,
enforced-naming counterpart to `tre.View.instantiate`/`Component
.instantiate` (TRE M43), used by `examples/todo_list/` for a real
dynamic list of independently-`ViewModel`'d components.
"""

import importlib.util
import sys

import pytest

from tesserae import View, instantiate

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


def test_instantiate_embeds_a_component_with_its_own_viewmodel(tmp_path):
    parent_path = write(tmp_path, PARENT_VIEW, "Parent_View.yaml")
    item_path = write(tmp_path, ITEM_VIEW, "Item_View.yaml")
    vm_cls = load_viewmodel_class(tmp_path, "Item_ViewModel.py", "ItemViewModel")

    view = View(parent_path)
    container = view.node("item_list")

    component, vm = instantiate(view, item_path, vm_cls, container)

    assert component is not None
    assert vm.value.get() == 0


def test_instantiate_rejects_a_mismatched_naming_pair(tmp_path):
    parent_path = write(tmp_path, PARENT_VIEW, "Parent_View.yaml")
    item_path = write(tmp_path, ITEM_VIEW, "item.yaml")  # missing _View suffix
    vm_cls = load_viewmodel_class(tmp_path, "Item_ViewModel.py", "ItemViewModel")

    view = View(parent_path)
    container = view.node("item_list")

    with pytest.raises(ValueError, match="_View.yaml"):
        instantiate(view, item_path, vm_cls, container)


def test_instantiate_forwards_extra_constructor_args_to_the_viewmodel(tmp_path):
    parent_path = write(tmp_path, PARENT_VIEW, "Parent_View.yaml")
    item_path = write(tmp_path, ITEM_VIEW, "Item_View.yaml")
    vm_cls = load_viewmodel_class(
        tmp_path, "Item_ViewModel.py", "ItemViewModel", extra_params=("label", "on_remove")
    )

    view = View(parent_path)
    container = view.node("item_list")

    removed = []
    component, vm = instantiate(view, item_path, vm_cls, container, "hello", removed.append)

    assert vm.label == "hello"
    vm.on_remove(vm)
    assert removed == [vm]


def test_multiple_instances_are_independent_and_removable(tmp_path):
    parent_path = write(tmp_path, PARENT_VIEW, "Parent_View.yaml")
    item_path = write(tmp_path, ITEM_VIEW, "Item_View.yaml")
    vm_cls = load_viewmodel_class(tmp_path, "Item_ViewModel.py", "ItemViewModel")

    view = View(parent_path)
    container = view.node("item_list")

    component_a, vm_a = instantiate(view, item_path, vm_cls, container)
    component_b, vm_b = instantiate(view, item_path, vm_cls, container)

    # Removing one instance must not disturb its sibling -- a real
    # click on the survivor's own node must still dispatch without
    # raising after the neighbor is gone.
    component_a.remove()
    view.click(component_b.node("root"))
