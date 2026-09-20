"""The real, first Tesserae `ViewModel` -- pairs with `Counter_View.yaml`
by the enforced-by-convention `*_View.yaml`/`*_ViewModel.py` naming.
"""

from tesserae import Signal, ViewModel


class CounterViewModel(ViewModel):
    def __init__(self, view):
        self._count = 0
        self.label = Signal("Count: 0")
        super().__init__(view)

    def increment(self):
        self._count += 1
        self.label.set(f"Count: {self._count}")
