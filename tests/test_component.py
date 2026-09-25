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
style: {flex_direction: vertical, width: 300, height: 200, gap: 8, padding: 8}
children:
  - id: item_list
    kind: Container
    style: {flex_direction: vertical, gap: 4, width: 280, height: 180}
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


def test_instantiate_with_no_component_usage_still_works_unchanged(tmp_path):
    """Real regression proof: `instantiate()` now expands `path`'s
    content and hands it off via `spec=` (M29; `source=` before that)
    instead of letting `parent.instantiate` read the file itself -- a
    `*_Component.yaml` with zero `component:` usage must still embed
    exactly as it always did (`expand_components`'s own real "true
    no-op" design)."""
    parent_path = write(tmp_path, PARENT_VIEW, "Parent_View.yaml")
    item_path = write(tmp_path, ITEM_VIEW, "Item_View.yaml")
    vm_cls = load_viewmodel_class(tmp_path, "Item_ViewModel.py", "ItemViewModel")

    view = View(parent_path)
    container = view.node("item_list")
    component, vm = instantiate(view, item_path, vm_cls, container)

    assert component.node("root") is not None


NESTED_COMPONENT_USING_ITEM_VIEW = """
id: root
kind: Container
style: {width: 260, height: 40}
children:
  - id: action_button
    component: ButtonFilled
    with: {label: Go, width: 100, height: 32, corner_radius: 16}
"""


def test_instantiate_genuinely_expands_component_usage(tmp_path):
    """Real, distinguishing proof `tesserae.instantiate()` (an embedded
    component, not a top-level `View`) genuinely applies `component:`
    macro-expansion -- the real gap `tre`'s own M73 closed
    (`Component.instantiate`/`View.instantiate` had no `source=`
    override at all before it). Before M73 + this wiring, a
    `component:`-using `*_Component.yaml` would fail with `tre`'s own
    schema error (`component` is not a real `WidgetSpec` field). After,
    it fails later, at MD3 color resolution (no `theme_seed` given --
    `View` itself supports one, but this test constructs a plain,
    unthemed `View` on purpose to isolate this one real, distinguishing
    proof) -- confirming `component:`/`with:` were genuinely replaced
    before `tre` ever parsed this component's own YAML.
    """
    parent_path = write(tmp_path, PARENT_VIEW, "Parent_View.yaml")
    item_path = write(tmp_path, NESTED_COMPONENT_USING_ITEM_VIEW, "Item_View.yaml")
    vm_cls = load_viewmodel_class(tmp_path, "Item_ViewModel.py", "ItemViewModel")

    view = View(parent_path)
    container = view.node("item_list")

    with pytest.raises(ValueError, match="unknown color identifier"):
        instantiate(view, item_path, vm_cls, container)


BOGUS_ITEM_VIEW = """
id: root
kind: NotARealKind
"""


def test_instantiate_names_the_source_file_when_tre_rejects_the_spec(tmp_path):
    """M29: `tre` only sees a dict via `spec=`, so it can't know which
    file a bad spec came from -- `instantiate` must say."""
    parent_path = write(tmp_path, PARENT_VIEW, "Parent_View.yaml")
    item_path = write(tmp_path, BOGUS_ITEM_VIEW, "Item_View.yaml")
    vm_cls = load_viewmodel_class(tmp_path, "Item_ViewModel.py", "ItemViewModel")

    view = View(parent_path)
    with pytest.raises(ValueError) as exc_info:
        instantiate(view, item_path, vm_cls, view.node("item_list"))
    assert str(exc_info.value).startswith(item_path)
    assert "NotARealKind" in str(exc_info.value)


def test_instantiate_resolves_include_relative_to_the_component_file(tmp_path):
    parts = tmp_path / "parts"
    parts.mkdir()
    (parts / "body.yaml").write_text(
        'id: body\nkind: Rect\nstyle: {width: 10, height: 10, background: "#112233"}\n'
    )
    parent_path = write(tmp_path, PARENT_VIEW, "Parent_View.yaml")
    item_path = write(
        tmp_path,
        "id: root\nkind: Container\nchildren:\n  - include: parts/body.yaml\n",
        "Item_View.yaml",
    )
    vm_cls = load_viewmodel_class(tmp_path, "Item_ViewModel.py", "ItemViewModel")

    view = View(parent_path)
    component, _ = instantiate(view, item_path, vm_cls, view.node("item_list"))
    assert component.node("body") is not None
