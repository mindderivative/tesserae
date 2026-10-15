from tesserae import Computed, Signal, ViewModel


class TasksViewModel(ViewModel):
    views = "Tasks"

    def __init__(self):
        super().__init__()
        self.tasks = Signal([])  # a list of {"id", "text", "done"}: the one source of truth
        self._next_id = 1
        # a text property wants a string, so the counts are strings
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
