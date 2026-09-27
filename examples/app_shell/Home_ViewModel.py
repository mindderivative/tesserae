"""The Home screen: it needs the app (to open the Notes screen), so
`app.py` builds it with `app.build_view` and `app.register`s it."""

from tesserae import Computed, Signal, ViewModel


class HomeViewModel(ViewModel):
    def __init__(self, view, app):
        self.app = app
        self.panels_moved = Signal(0)
        self.summary = Computed(lambda: f"Panels moved this session: {self.panels_moved.get()}")
        super().__init__(view)

    def open_notes(self):
        self.app.show("Notes")
