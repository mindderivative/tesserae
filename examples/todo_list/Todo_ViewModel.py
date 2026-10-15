"""Serves `Todo_View.yaml`. `items` is the single source of truth: a list of `{"id", "text", "done"}`. The view builds one `TodoItem` row for each, by
`for:` and `key:`, so adding, toggling and removing are only changes to this list: there is nothing to keep in step by hand."""

from tesserae import Signal, ViewModel


class TodoViewModel(ViewModel):
    views = "Todo"

    def __init__(self):
        super().__init__()
        self._counter = 0
        self.items = Signal([])

    def add_item(self):
        self._counter += 1
        item = {"id": self._counter, "text": f"Item {self._counter}", "done": False}
        self.items.update(lambda items: [*items, item])

    def toggle(self, item_id):
        self.items.update(lambda items: [{**i, "done": not i["done"]} if i["id"] == item_id else i for i in items])

    def remove(self, item_id):
        self.items.update(lambda items: [i for i in items if i["id"] != item_id])
