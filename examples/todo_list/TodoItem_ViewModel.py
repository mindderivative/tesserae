"""Pairs with `TodoItem_View.yaml`. Each instance is a real, independent
`Component` embedded into `Todo_View.yaml`'s own `item_list` container
(TRE M43), managed by `Todo_ViewModel.py`'s own `tesserae.Repeater`.

`remove_self` mutates the *shared* `items` list `Signal` directly
(rather than calling `self._view.remove()` and a private callback the
way an earlier, pre-`Repeater` draft of this example did) -- the real
single-source-of-truth pattern a `Repeater` is for: the `Repeater`
itself notices this item's own id is gone from `items` and tears its
`Component` down automatically, the caller never touches `Component
.remove()` directly.
"""

from tesserae import Signal, ViewModel


class TodoItemViewModel(ViewModel):
    def __init__(self, view, item_id, items_signal):
        self.item_id = item_id
        self.text = Signal(f"Item {item_id}")
        self.done = Signal(False)
        self._items_signal = items_signal
        super().__init__(view)

    def remove_self(self):
        self._items_signal.update(lambda ids: [i for i in ids if i != self.item_id])
