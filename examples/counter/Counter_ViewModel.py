"""The counter's ViewModel: it serves `Counter_View.yaml` (`views = "Counter"`), which shows `label` and calls `increment`."""

from tesserae import Computed, Signal, ViewModel


class CounterViewModel(ViewModel):
    views = "Counter"

    def __init__(self):
        super().__init__()
        self.count = Signal(0)
        self.label = Computed(lambda: f"Count: {self.count.get()}")
        # the button's accessible name, bound in the view's `a11y:`
        self.button_label = Computed(lambda: f"Increment, count is {self.count.get()}")

    def increment(self):
        self.count.set(self.count.get() + 1)
