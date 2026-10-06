from tesserae import Computed, Repeater, Signal, ViewModel


class MainViewModel(ViewModel):
    def __init__(self, view):
        self.tasks = Signal([])  # the ids of the tasks: the one source of truth
        self._next_id = 1
        self.rows = Repeater(view, self.tasks, "TaskItem", into=view.node("list"),
                             args=lambda task_id: (task_id, self.tasks))
        self.done_text = Computed(lambda: str(self._done()))  # a binding to text needs a string
        self.open_text = Computed(lambda: str(len(self.tasks.get()) - self._done()))
        super().__init__(view)

    def _done(self):
        self.tasks.get()  # recount when tasks come or go, and when a row's checkbox changes
        return sum(1 for _key, _component, row in self.rows if row.done.get())

    def add_task(self):
        self.tasks.update(lambda ids: [*ids, self._next_id])
        self._next_id += 1
