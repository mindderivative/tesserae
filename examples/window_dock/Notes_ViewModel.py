"""The Notes screen: a two-way text field and a live echo of it."""

from tesserae import Computed, Signal, ViewModel


class NotesViewModel(ViewModel):
    def __init__(self, view):
        self.note = Signal("")
        self.echo = Computed(lambda: f"{len(self.note.get())} characters")
        super().__init__(view)
