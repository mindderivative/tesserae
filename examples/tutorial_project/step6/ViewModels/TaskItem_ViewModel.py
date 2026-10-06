from tesserae import Signal, ViewModel


class TaskItemViewModel(ViewModel):
    def __init__(self, view, task_id, tasks):
        self.task_id = task_id
        self.tasks = tasks
        self.text = Signal(f"Task {task_id}")
        self.done = Signal(False)
        super().__init__(view)

    def remove_self(self):
        # The row removes itself by changing the list; the Repeater tears it down.
        self.tasks.update(lambda ids: [i for i in ids if i != self.task_id])
