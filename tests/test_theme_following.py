"""M50 Phases 2-3: `tesserae.widgets` widgets and controls, views, the
shell and dock, and overlays follow the app's theme (M50 Q1-Q3). Made with no `theme=` on an `App`'s window, they take
the app's theme and are re-coloured with its views by `set_dark`, the OS
switching light and dark, and `set_theme_specs`; an explicit `theme=`
pins one; on a bare window they keep MD3's baseline.
"""

import gc

import pytest
import tre

from tesserae import App, Theme, View, tokens
from tesserae.controls import Checkbox, SpinBox
from tesserae.docking import Dock
from tesserae.follow import app_of, initial_theme
from tesserae.overlays import NavigationDrawer
from tesserae.shell import AppShell
from tesserae.widgets import button, dialog, linear_progress, navigation_rail, top_app_bar

SEED = (0x67, 0x50, 0xA4, 0xFF)
OTHER = (0x00, 0x66, 0x88, 0xFF)
BASE = tokens.baseline_scheme()


def _app():
    return App(width=600, height=400, theme_seed=SEED, dark=False)


def _dark(app):
    return Theme.resolve(theme_seed=SEED, dark=True).roles


def test_a_widget_with_no_theme_takes_the_apps_and_follows_set_dark():
    app = _app()
    save = button(app.window, "Save", 120, 40, variant="filled")
    assert save.node.get("fill") == app.theme.role("primary") != BASE["primary"]
    app.set_dark(True)
    assert save.node.get("fill") == _dark(app)["primary"] and save.theme.dark is True
    app.set_dark(False)
    assert save.node.get("fill") == Theme.resolve(theme_seed=SEED).role("primary")


def test_controls_spin_boxes_and_indicators_follow_too():
    app = _app()
    box = Checkbox(app.window, checked=True)
    spin = SpinBox(app.window, value=1)
    bar = linear_progress(app.window, 200, value=0.5)
    assert box.box.get("fill") == app.theme.role("primary")
    app.set_dark(True)
    assert box.box.get("fill") == _dark(app)["primary"]
    assert spin.theme.dark is True and bar.theme.dark is True


def test_the_os_switching_and_set_theme_specs_reach_followers():
    app = App(width=600, height=400, theme_seed=SEED)  # "system": starts dark, follows the OS
    save = button(app.window, "Save", 120, 40, variant="filled")
    app._on_color_scheme(type("E", (), {"dark": False})())
    assert save.theme.dark is False
    app.set_theme_specs(None, {"colors": {"primary": "#123456"}})
    assert save.node.get("fill") == (0x12, 0x34, 0x56, 0xFF)


def test_an_explicit_theme_pins_the_widget():
    app = _app()
    fixed = Theme.resolve(theme_seed=OTHER)
    save = button(app.window, "Save", 120, 40, variant="filled", theme=fixed)
    box = Checkbox(app.window, checked=True, theme=fixed)
    app.set_dark(True)
    assert save.node.get("fill") == fixed.role("primary") and box.theme is fixed
    assert save not in app._followers and box not in app._followers


def test_on_a_bare_window_a_widget_keeps_mds_baseline():
    window = tre.Window(width=400, height=300)
    save = button(window, "Save", 120, 40, variant="filled")
    assert app_of(window) is None and save.node.get("fill") == BASE["primary"]


def test_a_destroyed_widget_stops_following():
    app = _app()
    save = button(app.window, "Save", 120, 40, variant="filled")
    box, spin = Checkbox(app.window), SpinBox(app.window)
    bar = linear_progress(app.window, 200)
    for thing in (save, box, spin, bar):
        assert thing in app._followers
        thing.destroy()
        assert thing not in app._followers
    app.set_dark(True)  # nothing left to re-colour, and nothing raises


def test_a_widget_whose_node_was_destroyed_under_it_is_dropped_at_the_next_switch():
    app = _app()
    save = button(app.window, "Save", 120, 40, variant="filled")
    save.node.destroy()  # not save.destroy()
    app.set_dark(True)
    assert save not in app._followers


def test_a_widget_no_one_kept_still_follows():
    app = _app()
    node = button(app.window, "Save", 120, 40, variant="filled").node
    gc.collect()
    app.set_dark(True)
    assert node.get("fill") == _dark(app)["primary"]


def test_a_failing_follower_rolls_back_every_view_and_widget():
    app = _app()
    save = button(app.window, "Save", 120, 40, variant="filled")
    light = save.node.get("fill")

    class Broken:
        node = save.node

        def set_theme(self, theme):
            if theme.dark:
                raise RuntimeError("no")

    initial_theme(app.window, None, Broken())
    with pytest.raises(RuntimeError):
        app.set_dark(True)
    assert app.dark is False and save.node.get("fill") == light and save.theme.dark is False


def test_an_app_is_found_by_its_own_window_only():
    app, other = _app(), _app()
    assert app_of(app.window) is app and app_of(other.window) is other
    assert app_of(tre.Window(width=10, height=10)) is None


# -- M50 Phase 3: views, the shell and dock, overlays (Q3) ---------------------


def _panel(window, color="on_surface", **theme):
    return View({"id": "root", "kind": "Text", "text": {"content": "Files", "typography_role": "body_medium"},
                 "style": {"foreground": color}}, window=window, **theme)


def test_a_view_on_the_apps_window_with_no_theme_follows_and_any_theme_argument_pins_it():
    app = _app()
    follows, seeded, light = _panel(app.window), _panel(app.window, theme_seed=OTHER), _panel(app.window, theme_seed=SEED, dark=False)
    assert follows.root.get("fill") == app.theme.role("on_surface")
    app.set_dark(True)
    assert follows.root.get("fill") == _dark(app)["on_surface"] and follows.theme.dark is True
    assert seeded.root.get("fill") == Theme.resolve(theme_seed=OTHER).role("on_surface")
    assert light.theme.dark is False and seeded not in app._followers and light not in app._followers
    only_dark = _panel(app.window, color="#112233", dark=False)  # `dark=` alone pins it too
    assert only_dark not in app._followers and only_dark.theme.dark is False


def test_a_view_on_its_own_window_keeps_its_theme():
    view = _panel(None, color="#112233")  # no theme: literal colours, as before
    assert view.theme.dark is False and app_of(view.window) is None


def test_a_view_whose_root_was_destroyed_is_dropped():
    app = _app()
    view = _panel(app.window)
    view.root.destroy()
    app.set_dark(True)
    assert view not in app._followers


def test_the_shell_and_its_dock_follow_but_leave_a_pinned_bar_alone():
    app = _app()
    fixed = Theme.resolve(theme_seed=OTHER)
    bar = top_app_bar(app.window, "Studio", width=600, theme=fixed)
    rail = navigation_rail(app.window, ["Home"], ["home"])
    shell = AppShell(app.window, top_bar=bar, navigation=rail, zones={"left": 200})
    app.set_dark(True)
    dark = _dark(app)
    assert shell.node.get("fill") == dark["surface"]
    assert shell.dock._zones["left"].node.get("fill") == dark["surface_container_low"]
    assert shell._handles["left"].grip.get("fill") == dark["outline"]
    assert rail.theme.dark is True  # it follows by itself
    assert bar.node.get("fill") == fixed.role("surface") and bar.theme is fixed


def test_a_shell_given_a_pinned_dock_leaves_it_alone_and_a_dock_alone_follows():
    app = _app()
    fixed = Theme.resolve(theme_seed=OTHER)
    pinned = Dock(app.window, theme=fixed)
    AppShell(app.window, zones={"left": 200}, dock=pinned)
    lone = Dock(app.window)
    lone_zone = lone.add_zone("right", 200)
    app.set_dark(True)
    assert pinned.theme is fixed and pinned._zones["left"].node.get("fill") == fixed.role("surface_container_low")
    assert lone_zone.get("fill") == _dark(app)["surface_container_low"]


def test_overlays_follow_through_their_widgets():
    app = _app()
    d = dialog(app.window, "Discard?", "Your draft will be lost.", 312, 180, actions=[("Cancel", None)])
    drawer = NavigationDrawer(app.window, ["Home"], ["home"])
    app.set_dark(True)
    dark = _dark(app)
    assert d.widget.part("panel").get("fill") == dark["surface_container_high"]
    assert drawer.drawer.node.get("fill") == dark["surface_container_low"]


def test_a_failing_follower_rolls_back_a_following_view_and_shell():
    app = _app()
    view = _panel(app.window)
    shell = AppShell(app.window, zones={"left": 200})
    light = (view.root.get("fill"), shell.node.get("fill"))

    class Broken:
        node = view.root

        def set_theme(self, theme):
            if theme.dark:
                raise RuntimeError("no")

    initial_theme(app.window, None, Broken())
    with pytest.raises(RuntimeError):
        app.set_dark(True)
    assert (view.root.get("fill"), shell.node.get("fill")) == light and view.theme.dark is False
