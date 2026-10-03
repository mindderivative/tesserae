from pathlib import Path

from tesserae import Computed, Repeater, Signal, ViewModel

from TaskItem_ViewModel import TaskItemViewModel

HERE = Path(__file__).parent


class TasksViewModel(ViewModel):
    def __init__(self, view):
        self.tasks = Signal([])  # the ids of the tasks: the one source of truth
        self._next_id = 1
        self.summary = Computed(lambda: f"{len(self.tasks.get())} tasks")
        # One TaskItem component, with a ViewModel of its own, for each id in `tasks`.
        self.rows = Repeater(view, self.tasks, HERE / "TaskItem_View.yaml", TaskItemViewModel,
                             view.node("list"), args=lambda task_id: (task_id, self.tasks))
        super().__init__(view)

    def add_task(self):
        self.tasks.update(lambda ids: [*ids, self._next_id])
        self._next_id += 1
