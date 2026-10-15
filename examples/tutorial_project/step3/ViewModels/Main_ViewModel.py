from tesserae import Computed, Signal, ViewModel


class MainViewModel(ViewModel):
    views = "Main"

    def __init__(self):
        super().__init__()
        self.tasks = Signal([])  # a list of {"id", "text", "done"}: the one source of truth
        self._next_id = 1
        self.summary = Computed(lambda: f"{len(self.tasks.get())} tasks")

    def add_task(self):
        task = {"id": self._next_id, "text": f"Task {self._next_id}", "done": False}
        self._next_id += 1
        self.tasks.update(lambda tasks: [*tasks, task])

    def toggle(self, task_id):
        self.tasks.update(lambda tasks: [{**t, "done": not t["done"]} if t["id"] == task_id else t for t in tasks])

    def remove(self, task_id):
        self.tasks.update(lambda tasks: [t for t in tasks if t["id"] != task_id])
