from tesserae import Computed, Signal, ViewModel


class MainViewModel(ViewModel):
    views = "Main"  # the view it serves: the `name:` at the top of Tasks_View.yaml

    def __init__(self):
        super().__init__()
        self.tasks = Signal([])
        self.summary = Computed(lambda: f"{len(self.tasks.get())} tasks")

    def add_task(self):
        self.tasks.update(lambda tasks: [*tasks, f"Task {len(tasks) + 1}"])
