from tesserae import Signal, ViewModel


class CounterViewModel(ViewModel):
    def __init__(self, view):
        self.count = 0
        self.label_text = Signal("Count: 0")
        super().__init__(view)  # last: it reads the Signals above

    def increment(self):
        self.count += 1
        self.label_text.set(f"Count: {self.count}")
