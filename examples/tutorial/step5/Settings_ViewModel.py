from tesserae import ViewModel


class SettingsViewModel(ViewModel):
    views = "Settings"

    def __init__(self, state):
        super().__init__()
        self.name = state.user  # the shared Signal itself: a bare reference to a Signal is two-way

    def toggle_dark(self):
        self.app.set_dark(not self.app.dark)  # every screen switches, in place

    def go_back(self):
        self.app.back()
