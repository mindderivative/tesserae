"""The Home screen's ViewModel: the title bar's own content (a search
field) and the hand-built bar's state. The window buttons need nothing
here -- their handlers are the app's window actions."""

from tesserae import Signal, ViewModel


class HomeViewModel(ViewModel):
    def __init__(self, view):
        self.query = Signal("")
        super().__init__(view)
