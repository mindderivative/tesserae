"""0.3.0 M2 (#40): the window on `App`, for a title bar the app draws
(`tre` 0.5.0's custom windowing). Phase 1 (#45): the window's options.
They're the window's own properties, so each is read back from `tre`.
"""

import pytest
from PIL import Image

from tesserae import App


def test_the_defaults_are_a_native_window():
    app = App()
    assert (app.borderless, app.resize_border, app.min_width, app.min_height) == (False, 0, 0, 0)
    assert (app.fullscreen, app.system_menu) == (False, False)
    assert app.platform in ("wayland", "x11", "windows", "macos")


def test_a_borderless_window_resizes_from_a_6_px_border():
    app = App(borderless=True)
    assert app.borderless is True and app.resize_border == App.DEFAULT_RESIZE_BORDER == 6
    app.borderless = False  # live: the border follows, since the app gave none
    assert (app.borderless, app.resize_border) == (False, 0)
    app.borderless = True
    assert app.resize_border == 6


def test_the_apps_own_border_wins():
    app = App(borderless=True, resize_border=10)
    assert app.resize_border == 10
    app.borderless = False
    assert app.resize_border == 10  # given, so kept whatever the borderless setting
    app.resize_border = None  # back to the default
    assert app.resize_border == 0
    app.borderless = True
    assert app.resize_border == 6
    app.resize_border = 0  # none, even borderless
    assert app.resize_border == 0


def test_the_other_options_at_start_and_live():
    app = App(min_width=320, min_height=200, fullscreen=True, system_menu=True)
    assert (app.min_width, app.min_height, app.fullscreen, app.system_menu) == (320, 200, True, True)
    app.min_width, app.min_height, app.fullscreen, app.system_menu = 400, 240, False, False
    assert (app.min_width, app.min_height, app.fullscreen, app.system_menu) == (400, 240, False, False)
    assert app.window.get("min_width") == 400.0  # tre's own


@pytest.mark.parametrize("name, value", [("resize_border", -1), ("min_width", -5), ("min_height", "wide"),
                                         ("min_width", True)])
def test_sizes_must_be_pixels(name, value):
    with pytest.raises(ValueError, match=f"App: {name} must be a number of pixels, 0 or more, got"):
        App(**{name: value})
    app = App()
    with pytest.raises(ValueError, match=f"App: {name} must be a number of pixels"):
        setattr(app, name, value)


def test_the_icon_is_an_image_file(tmp_path, monkeypatch):
    png = tmp_path / "icon.png"
    Image.new("RGBA", (4, 2), (103, 80, 164, 255)).save(png)
    handed = []
    app = App()

    class Recording:  # tre's Window is native: its `set` can't be patched, so wrap it
        def __init__(self, window):
            self._window = window

        def __getattr__(self, name):
            return getattr(self._window, name)

        def set(self, **props):
            if "icon" in props:
                handed.append(props["icon"])
            return self._window.set(**props)

    monkeypatch.setattr(app, "_window", Recording(app._window))
    app.set_icon(png)
    rgba, width, height = handed[-1]
    assert (width, height, len(rgba)) == (4, 2, 4 * 2 * 4) and rgba[:4] == bytes((103, 80, 164, 255))
    rgb = tmp_path / "rgb.png"
    Image.new("RGB", (2, 2), (1, 2, 3)).save(rgb)  # converted to RGBA
    app.set_icon(rgb)
    assert handed[-1][0][:4] == bytes((1, 2, 3, 255))
    app.set_icon(None)
    assert handed[-1] is None
    (tmp_path / "not.png").write_text("text")
    with pytest.raises(ValueError, match="App: icon '.*not.png' isn't an image file"):
        app.set_icon(tmp_path / "not.png")


def test_an_icon_given_at_start(tmp_path):
    png = tmp_path / "icon.png"
    Image.new("RGBA", (8, 8), (0, 0, 0, 255)).save(png)
    App(icon=png)  # tre accepts it (it checks the byte count)
    with pytest.raises(ValueError, match="isn't an image file"):
        App(icon=tmp_path / "missing.png")


# -- Phase 2 (#46): the window's actions and state ----------------------------------

def test_maximized_and_active_follow_the_window():
    app = App()
    assert app.maximized.get() is False and app.active.get() is False
    app.window.simulate("maximized", maximized=True)
    assert app.maximized.get() is True
    app.window.simulate("active", active=True)
    assert app.active.get() is True
    app.window.simulate("maximized", maximized=False)
    app.window.simulate("active", active=False)
    assert (app.maximized.get(), app.active.get()) == (False, False)
    assert not hasattr(app.maximized, "set") and not hasattr(app.active, "set")  # read-only


def test_a_binding_follows_maximized():
    from tesserae import View, ViewModel

    app = App()
    view = View({"id": "root", "kind": "Text", "text": {"content": "", "font_family": "Roboto", "font_size": 12},
                 "style": {"width": 100, "height": 20, "foreground": "#000000"},
                 "bindings": {"text": "{{ app.maximized.get() and 'restore' or 'maximize' }}"}},
                window=app.window)
    ViewModel(view)  # a ViewModel reaches the app as `app` (M65)
    assert view.node("root").get("text") == "maximize"
    app.window.simulate("maximized", maximized=True)
    assert view.node("root").get("text") == "restore"


def test_the_actions_before_the_window_opens():
    app = App()
    app.maximize()  # before run(): how it opens, and no event says so
    assert app.window.get("maximized") is True and app.maximized.get() is True
    app.toggle_maximized()
    assert app.window.get("maximized") is False and app.maximized.get() is False
    app.toggle_maximized()
    assert app.maximized.get() is True
    app.restore()
    assert app.maximized.get() is False
    app.minimize()
    assert app.window.get("minimized") is True
    app.restore()
    assert app.window.get("minimized") is False


def test_close_asks_first(monkeypatch):
    app = App()
    closed = []

    class Recording:
        def __init__(self, window):
            self._window = window

        def __getattr__(self, name):
            return getattr(self._window, name)

        def close(self):
            closed.append(True)  # tre's own: close_requested first, on the next turn

    monkeypatch.setattr(app, "_window", Recording(app._window))
    app.close()
    assert closed == [True]
