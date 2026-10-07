"""#93: a TextField's text is the theme's `on_surface`, so it is light in a dark scheme and dark in a light one."""

import yaml

from tesserae import App, View

SEED = (0x67, 0x50, 0xA4, 0xFF)
SPEC = """
id: root
kind: Container
style: {width: 300, height: 120, background: surface}
children:
  - id: name
    kind: TextField
    text: {content: "Hello", typography_role: body_large}
    style: {width: 240, height: 48, background: surface_container_highest, corner_radius: 4}
"""


def _view(dark, extra=None):
    spec = yaml.safe_load(SPEC)
    if extra:
        spec["children"][0]["style"].update(extra)
    app = App(width=300, height=120, theme_seed=SEED, dark=dark)
    view = View(spec, window=app.window)
    app.window.root.add_child(view.root)
    app.window.advance(32)
    return app, view


def _ink(view):
    return view.node("name").get("fill")


def test_the_text_is_light_in_dark_mode_and_dark_in_light_mode():
    for dark in (True, False):
        app, view = _view(dark)
        assert _ink(view) == app.theme.role("on_surface")
    assert min(_ink(_view(True)[1])[:3]) > 150 and max(_ink(_view(False)[1])[:3]) < 100


def test_it_follows_the_app_when_it_switches():
    app, view = _view(False)
    light = _ink(view)
    app.set_dark(True)
    app.window.advance(16)
    assert _ink(view) == app.theme.role("on_surface") != light


def test_a_foreground_style_is_the_ink():
    _, view = _view(True, {"foreground": "#FF0000"})
    assert _ink(view) == (255, 0, 0, 255)


def test_the_caret_is_the_themes_primary():
    app, view = _view(True)
    assert view.node("name").get("caret_color") == app.theme.role("primary")


def test_the_text_shows_light_on_the_dark_field():
    app, view = _view(True)
    rgba, width, _ = app.window.snapshot()
    brightest = max(max(rgba[(y * width + x) * 4:(y * width + x) * 4 + 3]) for y in range(0, 40) for x in range(0, 60))
    assert brightest > 180  # the dark field and its dark ink would be nothing above ~60
