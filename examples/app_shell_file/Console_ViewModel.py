"""The Console panel's ViewModel. `load_shell` finds it by name and builds
it with just the view, as it does for any panel file (M52)."""

from tesserae import Signal, ViewModel


class ConsoleViewModel(ViewModel):
    def __init__(self, view):
        self.last = Signal("tesserae: app shell started")
        super().__init__(view)

    def log(self, line: str) -> None:
        self.last.set(line)
