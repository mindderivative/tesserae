"""The Console panel's ViewModel: found beside Console_View.yaml and built with just the view."""

from tesserae import Signal, ViewModel


class ConsoleViewModel(ViewModel):
    def __init__(self, view):
        self.last = Signal("tesserae: window started")
        super().__init__(view)

    def log(self, line: str) -> None:
        self.last.set(line)
