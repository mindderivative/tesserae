from tesserae import Signal, ViewModel


class CounterViewModel(ViewModel):
    views = "Counter"  # the view it serves: the `name:` at the top of Counter_View.yaml

    def __init__(self):
        super().__init__()
        self.count = Signal(0)

    def increment(self):
        self.count.update(lambda n: n + 1)
