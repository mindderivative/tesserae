"""The real, first Tesserae `ViewModel` -- pairs with `Counter_View.yaml`
by the enforced-by-convention `*_View.yaml`/`*_ViewModel.py` naming.
"""

from tesserae import Computed, Signal, ViewModel


class CounterViewModel(ViewModel):
    def __init__(self, view):
        self.count = Signal(0)
        self.label = Computed(lambda: f"Count: {self.count.get()}")
        # the button's accessible name, bound in the view's `a11y:` (M47)
        self.button_label = Computed(lambda: f"Increment, count is {self.count.get()}")
        super().__init__(view)

    def increment(self):
        self.count.set(self.count.get() + 1)
