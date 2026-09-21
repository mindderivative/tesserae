"""Pairs with `Todo_View.yaml` -- the real, top-level screen `App.load`
registers. Owns the real dynamic list via `tesserae.Repeater`: `items`
is the single source of truth (a plain list of stable item ids) -- the
`Repeater` keeps exactly one `TodoItem` component + `TodoItemViewModel`
alive per id currently present, added/removed automatically whenever
`items` changes, with zero manual bookkeeping here.
"""

from pathlib import Path

from tesserae import Repeater, Signal, ViewModel

from TodoItem_ViewModel import TodoItemViewModel

_ITEM_PATH = Path(__file__).parent / "TodoItem_View.yaml"


class TodoViewModel(ViewModel):
    def __init__(self, view):
        self._counter = 0
        self.items = Signal([])  # the single source of truth: stable item ids
        container = view.node("item_list")
        self.repeater = Repeater(
            view,
            self.items,
            _ITEM_PATH,
            TodoItemViewModel,
            container,
            args=lambda item_id: (item_id, self.items),
        )
        super().__init__(view)

    def add_item(self):
        self._counter += 1
        self.items.update(lambda lst: [*lst, self._counter])
