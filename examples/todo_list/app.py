#!/usr/bin/env python3
"""Tesserae's own real third vertical slice: a dynamic to-do list,
showcasing TRE M43's real multi-instance, independent-`ViewModel`
component embedding through Tesserae's own real conventions --
`tesserae.instantiate` (the `*_View.yaml`/`*_ViewModel.py`-enforced
counterpart to `Component.instantiate`), used from inside a real
dispatched `on_click` handler (`TodoViewModel.add_item`).

Each to-do item is its own real, independent `Component` + `ViewModel`
(`TodoItem_View.yaml`/`TodoItem_ViewModel.py`) -- adding one, toggling
its checkbox, and removing it are all real, dispatched interactions
through the same live window, proving the whole real stack end to end:
`App.load` -> `Todo_ViewModel` -> `tesserae.instantiate` -> a real,
embedded `Component` with its own `Signal`-bound state.
"""

from pathlib import Path

from tesserae import App

from Todo_ViewModel import TodoViewModel

directory = Path(__file__).parent

app = App(width=300, height=300, title="Tesserae Todo List")
view, vm = app.load(directory / "Todo_View.yaml", TodoViewModel)
window = app.show("Todo")

add_button = view.node("add_button")

# Three real, dispatched clicks on "Add" -- each instantiating a fresh,
# independent TodoItem component with its own ViewModel.
for _ in range(3):
    window.click(add_button)
assert len(vm.items) == 3
assert [item_vm.text.get() for _, item_vm in vm.items] == ["Item 1", "Item 2", "Item 3"]

# Toggle the first item's checkbox -- a real two-way binding write-back.
# `Node.set_checked` (not `window.click`) is the real, Python-reachable
# Change source for a Checkbox (tre's own `examples/two_way_binding.py`
# documents this precedent: a real click routes through the same real
# method, but a synthetic `click()` dispatch alone doesn't include a
# Checkbox's own toggle behavior).
first_component, first_vm = vm.items[0]
first_component.node("check").set_checked(True)
assert first_vm.done.get() is True

# Remove the second item via its own dispatched "remove" click.
window.click(vm.items[1][0].node("remove_button"))
assert len(vm.items) == 2
assert [item_vm.text.get() for _, item_vm in vm.items] == ["Item 1", "Item 3"]

# The list stays healthy after a real removal -- one more "Add" works.
window.click(add_button)
assert len(vm.items) == 3

print(f"final items: {[(item_vm.text.get(), item_vm.done.get()) for _, item_vm in vm.items]!r}")

app.run(max_frames=20)
print("todo_list/app.py: exited cleanly after a real 20-frame render loop")
