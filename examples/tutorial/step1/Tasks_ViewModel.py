from tesserae import Computed, Signal, ViewModel


class TasksViewModel(ViewModel):
    def __init__(self, view):
        self.tasks = Signal([])
        self.summary = Computed(lambda: f"{len(self.tasks.get())} tasks")
        super().__init__(view)  # last: it reads the Signals the view refers to

    def add_task(self):
        self.tasks.update(lambda tasks: [*tasks, f"Task {len(tasks) + 1}"])
