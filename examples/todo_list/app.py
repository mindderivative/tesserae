#!/usr/bin/env python3
"""Tesserae's fourth vertical slice: a dynamic to-do list. One list `Signal` (`TodoViewModel.items`) is the single source of truth, and the view builds
one `TodoItem` row for each item by `for: item in items` with a `key:`, so rows are added, kept and removed as the list changes. Adding is
`items.update(...)` in the ViewModel; so are toggling and removing, called from the row's own handlers.

Real dispatched clicks add three items, tick one, remove one, and add again, then the app renders 20 frames and exits.

Hot reload: run it with `app.run(hot_reload=True)` (and no `max_frames`), then edit `TodoItem_View.yaml` -- every row changes in place, its items kept.
"""

from pathlib import Path

from loguru import logger

from tesserae import App, configure_logging

from Todo_ViewModel import TodoViewModel

configure_logging()  # Tesserae's console format; configure_logging("DEBUG") shows more

directory = Path(__file__).parent

app = App(width=300, height=300, title="Tesserae Todo List", root=directory, search=["."])
app.bind(TodoViewModel)
view = app.open_view("Todo")
vm = app.bindings.viewmodel_for("Todo")
window = app.show("Todo")

add_button = view.node("root.add_button")


def rows():
    """The row nodes, in order (a node's id is its path; each row under a `for:` has its `key`)."""
    return [i for i in view.handle.composition.walk() if i.name == "row"]


def row_node(item_id, part):
    return view.node(f"root.item_list.row[{item_id}].{part}")


def item_texts():
    return [item["text"] for item in vm.items.get()]


# Three real, dispatched clicks on "Add" -- each appending an item to `vm.items`, which the view turns into a fresh row.
for _ in range(3):
    window.simulate("click", node=add_button)
window.advance(16)
assert len(rows()) == 3 and item_texts() == ["Item 1", "Item 2", "Item 3"]

# Tick the first item's checkbox with a real dispatched click: its `on_change` calls `toggle(item.id)`.
window.simulate("click", node=row_node(1, "check"))
assert vm.items.get()[0]["done"] is True

# Remove the second item with its own "remove" click: the row's `on_remove` calls `remove(item.id)`, and the row is gone.
window.simulate("click", node=row_node(2, "remove_button"))
window.advance(16)
assert len(rows()) == 2 and item_texts() == ["Item 1", "Item 3"]

# The list stays healthy after a real removal -- one more "Add" works, and the first row is still ticked.
window.simulate("click", node=add_button)
window.advance(16)
assert len(rows()) == 3 and vm.items.get()[0]["done"] is True

logger.info(f"final items: {[(i['text'], i['done']) for i in vm.items.get()]!r}")

app.run(max_frames=20)
logger.info("todo_list/app.py: exited cleanly after a real 20-frame render loop")
