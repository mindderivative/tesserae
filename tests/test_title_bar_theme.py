"""0.3.0 M3 Phase 3 (#51): a TitleBar's look. Material 3 roles on its
parts' classes, in the cascade's first layer, so a theme or stylesheet
restyles any part; the title, icon and buttons fade while the window
isn't the focused one; close's hover and pressed layers are red.
"""

import yaml

from tesserae import App, Theme, ViewModel
from tesserae.spec.title_bar import INACTIVE

SEED = (0x67, 0x50, 0xA4, 0xFF)
BAR = {"id": "bar", "kind": "TitleBar", "title": "Notes", "icon": "home", "style": {"width": 600}}


def _app_with(tmp_path, **app_kwargs):
    path = tmp_path / "Home_View.yaml"
    path.write_text(yaml.safe_dump({"id": "root", "kind": "Container", "style": {"width": 600, "height": 400},
                                    "children": [BAR]}), encoding="utf-8")
    app = App(width=600, height=400, theme_seed=SEED, decorations=False, **app_kwargs)
    view = app.build_view(path)
    app.register("Home", view, None)
    app.show("Home")
    ViewModel(view)
    app.window.advance(16)
    return app, view


def test_the_parts_are_the_themes_roles(tmp_path):
    app, view = _app_with(tmp_path)
    theme = Theme.resolve(theme_seed=SEED, dark=app.dark)  # the app follows the OS's appearance
    assert view.node("bar").get("fill") == theme.role("surface")
    for part in ("bar.title", "bar.icon", "bar.close.close", "bar.maximize.window_maximize"):
        assert view.node(part).get("fill") == theme.role("on_surface"), part


def test_a_stylesheet_restyles_any_part(tmp_path):
    sheet = {"styles": [{"classes": ["title_bar"], "style": {"background": "#102030"}},
                        {"classes": ["title_bar_title"], "style": {"foreground": "#FF8800"}},
                        {"classes": ["title_bar_glyph"], "style": {"foreground": "#00FF00"}}]}
    app, view = _app_with(tmp_path, stylesheet_spec=sheet)
    assert view.node("bar").get("fill") == (0x10, 0x20, 0x30, 255)
    assert view.node("bar.title").get("fill") == (0xFF, 0x88, 0x00, 255)
    assert view.node("bar.minimize.window_minimize").get("fill") == (0x00, 0xFF, 0x00, 255)


def test_an_apps_own_default_theme_keeps_the_bars_look(tmp_path):
    """An app's `default_theme` replaces Tesserae's shipped one entirely;
    the bar's look is under it, so its parts still have their colours."""
    app, view = _app_with(tmp_path, default_theme_spec={"styles": [{"kind": "Rect", "style": {"corner_radius": 4}}]})
    assert view.node("bar.title").get("fill") == Theme.resolve(theme_seed=SEED, dark=app.dark).role("on_surface")


def test_it_fades_while_the_window_isnt_focused(tmp_path):
    app, view = _app_with(tmp_path)
    parts = ("bar.title", "bar.icon", "bar.buttons")
    assert all(view.node(p).get("opacity") == INACTIVE for p in parts)  # not focused before it opens
    app.window.simulate("active", active=True)
    assert all(view.node(p).get("opacity") == 1.0 for p in parts)
    app.window.simulate("active", active=False)
    assert all(view.node(p).get("opacity") == INACTIVE for p in parts)
    assert view.node("bar.content").get("opacity") == 1.0  # the app's own content isn't faded


def test_close_is_red_and_the_others_are_not(tmp_path):
    app, view = _app_with(tmp_path)
    theme = Theme.resolve(theme_seed=SEED, dark=app.dark)  # the app follows the OS's appearance
    assert view.interaction("bar.close").tint == theme.role("error")
    assert view.interaction("bar.minimize").tint == theme.role("on_surface")


def test_it_rethemes_with_the_app(tmp_path):
    app, view = _app_with(tmp_path)
    for dark in (not app.dark, app.dark):
        app.set_dark(dark)
        theme = Theme.resolve(theme_seed=SEED, dark=dark)
        assert view.node("bar").get("fill") == theme.role("surface")
        assert view.node("bar.title").get("fill") == theme.role("on_surface")
        assert view.interaction("bar.close").tint == theme.role("error")


def test_a_theme_restyles_it_too(tmp_path):
    """The bar's look is under every theme, not just under stylesheets."""
    theme = {"styles": [{"classes": ["title_bar_title"], "style": {"foreground": "#123456"}}]}
    app, view = _app_with(tmp_path, default_theme_spec=theme)
    assert view.node("bar.title").get("fill") == (0x12, 0x34, 0x56, 255)


def test_a_title_bar_works_in_an_app_with_no_theme_seed(tmp_path):
    """0.3.3 (#82): a bare `App(decorations=False)` failed with "unknown color identifier"; the bar's
    roles are MD3's baseline palette now, and close is still red."""
    from tesserae import tokens

    path = tmp_path / "Home_View.yaml"
    path.write_text(yaml.safe_dump({"id": "root", "kind": "Container", "style": {"width": 600, "height": 400},
                                    "children": [BAR]}), encoding="utf-8")
    app = App(width=600, height=400, decorations=False)
    view = app.build_view(path)
    app.register("Home", view, None)
    app.show("Home")
    ViewModel(view)
    app.window.advance(16)
    baseline = tokens.baseline_scheme()
    assert view.node("bar").get("fill") == baseline["surface"]
    assert view.node("bar.title").get("fill") == baseline["on_surface"]
    assert view.interaction("bar.close").tint == baseline["error"]
