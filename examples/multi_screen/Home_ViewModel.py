"""Pairs with `Home_View.yaml`. Takes `app` alongside `view` (widening
`tre.ViewModel`'s own real `__init__(self, view)` contract) so its
`on_click` handler can call `app.show(...)` -- the real, decisive proof
this example exists for: switching screens *from inside a real
dispatched handler*, the same reentrant scenario `tre`'s own M42 Phase 2
had to catch and fix a real borrow-panic bug for.
"""

from tesserae import ViewModel


class HomeViewModel(ViewModel):
    def __init__(self, view, app):
        self._app = app
        super().__init__(view)

    def go_to_settings(self):
        self._app.show("Settings")
