"""Pairs with `Home_View.yaml`. Its handler switches screens with
`self.app.show(...)` and records where the user came from in the app's
shared state (M65): `self.app` and `self.state` are found through the
view's window, so `App.load()`'s plain `HomeViewModel(view)` is enough.
Switching from inside a real dispatched handler is the reentrant case
`tre`'s own M42 Phase 2 had to fix a borrow panic for.
"""

from tesserae import ViewModel


class HomeViewModel(ViewModel):
    def go_to_settings(self):
        self.state.came_from.set("from Home")
        self.app.show("Settings")
