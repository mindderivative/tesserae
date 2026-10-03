from tesserae import App, ViewModel


class SettingsViewModel(ViewModel):
    def __init__(self, view):
        self.name = App.of(view).state.user  # the shared Signal itself: a two_way binding needs one
        super().__init__(view)

    def toggle_dark(self):
        self.app.set_dark(not self.app.dark)  # every screen switches, in place
