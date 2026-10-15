"""The window's ViewModel. It serves `Window_View.yaml`, and so the views the window calls: the Console panel reads `last`, the Notes screen
reads `note` and `echo` (a called view has no ViewModel of its own)."""

from tesserae import Computed, Signal, ViewModel


class WindowViewModel(ViewModel):
    views = "Window"

    def __init__(self):
        super().__init__()
        self.last = Signal("tesserae: window started")  # Console
        self.note = Signal("")  # Notes: a two-way text field and a live echo of it
        self.echo = Computed(lambda: f"{len(self.note.get())} characters")

    def log(self, line: str) -> None:
        self.last.set(line)
