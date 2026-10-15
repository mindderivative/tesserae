"""The Home screen's ViewModel: it serves `Home_View.yaml` (`views = "Home"`). It holds the title bar's own content (a search field's text) and
nothing else: the window buttons need nothing here, their handlers are the app's window actions."""

from tesserae import Signal, ViewModel


class HomeViewModel(ViewModel):
    views = "Home"

    def __init__(self):
        super().__init__()
        self.query = Signal("")
