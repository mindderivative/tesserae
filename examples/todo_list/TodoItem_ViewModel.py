"""Pairs with `TodoItem_View.yaml`. Each instance is a real, independent
`Component` embedded into `Todo_View.yaml`'s own `item_list` container
(TRE M43) -- `view` here is actually a `tre.Component`, not a `tre.View`
(the base `ViewModel.__init__` stores whatever it's given as `self.
_view`, so `self._view.remove()` below correctly calls `Component.
remove()`).
"""

from tesserae import Signal, ViewModel


class TodoItemViewModel(ViewModel):
    def __init__(self, view, text, on_remove):
        self.text = Signal(text)
        self.done = Signal(False)
        self._on_remove = on_remove
        super().__init__(view)

    def remove_self(self):
        # The real M43 Phase 2 proof: unsubscribes this instance's own
        # Signal subscriptions, then removes its subtree from the Tree.
        self._view.remove()
        self._on_remove(self)
