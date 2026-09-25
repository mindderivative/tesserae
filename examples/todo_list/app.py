#!/usr/bin/env python3
"""Tesserae's own real fourth vertical slice: a dynamic to-do list
driven by `tesserae.Repeater` -- one list `Signal` (`TodoViewModel
.items`) is the single source of truth, and the `Repeater` keeps
exactly one real, independent `TodoItem` `Component` + `ViewModel`
alive per item id currently present, adding/removing them
automatically. Adding is `items.update(lambda lst: [*lst, new_id])`
(`TodoViewModel.add_item`); removing is the *same* pattern from the
item's own side (`TodoItemViewModel.remove_self`) -- neither one ever
calls `Component.remove()`/`tesserae.instantiate` directly anymore.

Toggling a checkbox and the whole real render loop prove the same real
stack this repo's earlier, pre-`Repeater` version already did --
`Repeater` is a real, additive convenience over `tesserae.instantiate`/
`Component.remove()` (TRE M43), not a replacement for them.
"""

from pathlib import Path

from loguru import logger

from tesserae import App, configure_logging

from Todo_ViewModel import TodoViewModel

configure_logging()  # Tesserae's console format; configure_logging("DEBUG") shows more

directory = Path(__file__).parent

app = App(width=300, height=300, title="Tesserae Todo List")
view, vm = app.load(directory / "Todo_View.yaml", TodoViewModel)
window = app.show("Todo")

add_button = view.node("add_button")


def item_texts():
    return [item_vm.text.get() for _key, _component, item_vm in vm.repeater]


# Three real, dispatched clicks on "Add" -- each appending a new id to
# `vm.items`, which the Repeater turns into a fresh, independent
# TodoItem component + ViewModel automatically.
for _ in range(3):
    window.click(add_button)
assert len(vm.repeater) == 3
assert item_texts() == ["Item 1", "Item 2", "Item 3"]

# Toggle the first item's checkbox -- a real two-way binding write-back.
# `Node.set_checked` (not `window.click`) is the real, Python-reachable
# Change source for a Checkbox (tre's own `examples/two_way_binding.py`
# documents this precedent: a real click routes through the same real
# method, but a synthetic `click()` dispatch alone doesn't include a
# Checkbox's own toggle behavior).
first_component, first_vm = vm.repeater[1]
first_component.node("check").set_checked(True)
assert first_vm.done.get() is True

# Remove the second item via its own dispatched "remove" click --
# TodoItemViewModel.remove_self mutates the shared `items` Signal;
# the Repeater notices id 2 is gone and tears its Component down.
window.click(vm.repeater[2][0].node("remove_button"))
assert len(vm.repeater) == 2
assert item_texts() == ["Item 1", "Item 3"]

# The list stays healthy after a real removal -- one more "Add" works.
window.click(add_button)
assert len(vm.repeater) == 3

logger.info(
    f"final items: "
    f"{[(item_vm.text.get(), item_vm.done.get()) for _k, _c, item_vm in vm.repeater]!r}"
)

app.run(max_frames=20)
logger.info("todo_list/app.py: exited cleanly after a real 20-frame render loop")
