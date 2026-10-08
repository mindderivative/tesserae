"""0.3.0 M4 Phase 2 (#55; the design's Q9, the user's addition): an
undecorated window's 1 px border, in the theme's `outline_variant`, over
the whole window and never in the way of a press. Hidden while
maximized or fullscreen, and on macOS (its frame); restylable by class.
"""

import sys

import pytest
import yaml

from tesserae import App, Theme, ViewModel, tokens

SEED = (0x67, 0x50, 0xA4, 0xFF)
pytestmark = pytest.mark.skipif(sys.platform == "darwin", reason="no border on macOS: the OS draws the frame")


def _app(**kwargs):
    app = App(width=400, height=300, theme_seed=SEED, **kwargs)
    app.window.advance(16)
    return app


def _border(app):
    return app._border.root if app._border is not None else None


def test_an_undecorated_window_has_a_border_around_it():
    app = _app(borderless=True)
    border = _border(app)
    assert border.get("visible") is True and app.window_border is True
    assert (border.get("layout_x"), border.get("layout_y")) == (0.0, 0.0)
    assert (border.get("layout_width"), border.get("layout_height")) == (400.0, 300.0)
    theme = Theme.resolve(theme_seed=SEED, dark=app.dark)
    assert border.get("stroke_color") == theme.role("outline_variant") and border.get("stroke_width") == 1.0


def test_a_decorated_window_has_none():
    assert _border(_app()) is None  # not even built


def test_it_hides_while_maximized_fullscreen_or_decorated_or_turned_off():
    app = _app(borderless=True)
    border = _border(app)
    app.window.simulate("maximized", maximized=True)
    assert border.get("visible") is False
    app.window.simulate("maximized", maximized=False)
    assert border.get("visible") is True
    app.fullscreen = True
    assert border.get("visible") is False
    app.fullscreen = False
    app.borderless = False
    assert border.get("visible") is False
    app.borderless = True
    app.window_border = False
    assert border.get("visible") is False
    app.window_border = True
    assert border.get("visible") is True
    assert _border(_app(borderless=True, window_border=False)) is None


def test_it_shows_when_a_decorated_window_loses_its_decorations():
    app = _app()
    app.borderless = True
    assert _border(app).get("visible") is True


def test_it_lies_over_the_screens_and_presses_go_through(tmp_path):
    path = tmp_path / "Home_View.yaml"
    path.write_text(yaml.safe_dump({"id": "root", "kind": "Container", "style": {"width": 400, "height": 300},
                                    "children": [{"id": "edge", "kind": "Rect", "handlers": {"on_click": "go"},
                                                  "style": {"width": 400, "height": 300, "background": "surface"}}]}),
                    encoding="utf-8")

    class VM(ViewModel):
        clicks = 0

        def go(self):
            self.clicks += 1

    app = _app(borderless=True)
    view = app.build_view(path)
    app.register("Home", view, None)
    app.show("Home")  # a screen shown after the border was made
    vm = VM(view)
    app.window.advance(16)
    assert _border(app).get("z_index") > (view.root.get("z_index") or 0)
    # The border is a full-window box (its line drawn at the edge): a press
    # anywhere in it reaches the screen. (A press at the very edge is the
    # window's, for resizing: `resize_border`.)
    app.window.simulate("pointer_down", x=200, y=150)
    app.window.simulate("pointer_up", x=200, y=150)
    assert vm.clicks == 1


def test_a_stylesheet_restyles_or_removes_it():
    red = {"styles": [{"classes": ["window_border"], "style": {"border_color": "#FF0000", "border_width": 2}}]}
    app = _app(borderless=True, stylesheet_spec=red)
    assert _border(app).get("stroke_color") == (255, 0, 0, 255) and _border(app).get("stroke_width") == 2.0
    none = {"styles": [{"classes": ["window_border"], "style": {"border_width": 0}}]}
    assert _border(_app(borderless=True, stylesheet_spec=none)).get("stroke_width") == 0.0


def test_it_rethemes_with_the_app():
    app = _app(borderless=True)
    for dark in (not app.dark, app.dark):
        app.set_dark(dark)
        assert _border(app).get("stroke_color") == Theme.resolve(theme_seed=SEED, dark=dark).role("outline_variant")


def test_an_unthemed_app_gets_the_baseline_colour():
    app = App(borderless=True)
    assert _border(app).get("stroke_color") == tokens.BASELINE["outline_variant"]
    assert _border(app).get("stroke_width") == 1.0
