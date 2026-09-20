"""Pairs with `Todo_View.yaml` -- the real, top-level screen `App.load`
registers. Owns the real dynamic list: each "Add" click instantiates a
new, independent `TodoItem` component (TRE M43) with its own
`TodoItemViewModel`, via `tesserae.instantiate` (the enforced-naming
counterpart to `Component.instantiate` this repo's own `README.md`
documents).
"""

from pathlib import Path

from tesserae import ViewModel, instantiate

from TodoItem_ViewModel import TodoItemViewModel

_ITEM_PATH = Path(__file__).parent / "TodoItem_View.yaml"


class TodoViewModel(ViewModel):
    def __init__(self, view):
        self.items = []  # list of (Component, TodoItemViewModel), display order
        self._counter = 0
        self._container = view.node("item_list")
        super().__init__(view)

    def add_item(self):
        self._counter += 1
        component, item_vm = instantiate(
            self._view,
            _ITEM_PATH,
            TodoItemViewModel,
            self._container,
            f"Item {self._counter}",
            self._discard_item,
        )
        self.items.append((component, item_vm))

    def _discard_item(self, item_vm):
        for index, (_component, existing_vm) in enumerate(self.items):
            if existing_vm is item_vm:
                del self.items[index]
                return
