from tesserae import Computed, Signal, ViewModel


class WindowViewModel(ViewModel):
    """Serves Window_View.yaml, and so the Tasks and Settings screens in it: they read these names."""

    views = "Window"

    def __init__(self, state):
        super().__init__()
        self.name = state.user  # Settings: the shared Signal itself, so the field is two-way
        self.tasks = Signal([])  # Tasks: a list of {"id", "text", "done"}
        self._next_id = 1
        self.open_text = Computed(lambda: str(sum(1 for t in self.tasks.get() if not t["done"])))
        self.done_text = Computed(lambda: str(sum(1 for t in self.tasks.get() if t["done"])))

    def add_task(self):
        task = {"id": self._next_id, "text": f"Task {self._next_id}", "done": False}
        self._next_id += 1
        self.tasks.update(lambda tasks: [*tasks, task])

    def toggle(self, task_id):
        self.tasks.update(lambda tasks: [{**t, "done": not t["done"]} if t["id"] == task_id else t for t in tasks])

    def remove(self, task_id):
        self.tasks.update(lambda tasks: [t for t in tasks if t["id"] != task_id])

    def toggle_dark(self):
        self.app.set_dark(not self.app.dark)
