"""0.3.0 M2 (#40): the window on `App`, for a title bar the app draws
(`tre` 0.5.0's custom windowing). Phase 1 (#45): the window's options.
They're the window's own properties, so each is read back from `tre`.
"""

import pytest
from PIL import Image

from tesserae import App


def test_the_defaults_are_a_decorated_window():
    app = App()
    assert (app.decorations, app.resize_border, app.min_width, app.min_height) == (True, 0, 0, 0)
    assert (app.fullscreen, app.system_menu) == (False, False)
    assert app.platform in ("wayland", "x11", "windows", "macos")


def test_an_undecorated_window_resizes_from_a_6_px_border():
    app = App(decorations=False)
    assert app.decorations is False and app.resize_border == App.DEFAULT_RESIZE_BORDER == 6
    app.decorations = True  # live: the border follows, since the app gave none
    assert (app.decorations, app.resize_border) == (True, 0)
    app.decorations = False
    assert app.resize_border == 6


def test_the_apps_own_border_wins():
    app = App(decorations=False, resize_border=10)
    assert app.resize_border == 10
    app.decorations = True
    assert app.resize_border == 10  # given, so kept whatever the decorations
    app.resize_border = None  # back to the default
    assert app.resize_border == 0
    app.decorations = False
    assert app.resize_border == 6
    app.resize_border = 0  # none, even undecorated
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
