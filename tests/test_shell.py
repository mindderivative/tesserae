"""M45 Phase 3: `tesserae.shell.AppShell` and `App.use_shell` -- the frame
around an app's screens (what `tre` 0.3.4's `build_shell` did): a top app
bar, navigation, docked zones with resize handles around the content, a
status bar; and `layout()`/`restore()` (M45 Q3-Q4).
"""

import pytest

from tesserae import App, Theme, View, tokens
from tesserae.shell import MIN_ZONE, STEP, AppShell
from tesserae.widgets import navigation_rail, status_bar, top_app_bar

BASE = tokens.baseline_scheme()


def _app(**shell_args):
    app = App(width=1000, height=600)
    w = app.window
    parts = dict(top_bar=top_app_bar(w, "Studio", width=1000), navigation=navigation_rail(w, ["Home", "Files"],
                 ["home", "search"]), status_bar=status_bar(w, "Ready", width=1000))
    parts.update(shell_args)
    shell = AppShell(w, zones={"left": 240, "right": 260, "bottom": 160}, **parts)
    for side, title in (("left", "Files"), ("left", "Search"), ("right", "Properties"), ("bottom", "Console")):
        shell.dock.add_panel(side, w.create("box", width=10, height=10), title)
    w.advance(16)
    return app, shell


def _box(node):
    return tuple(round(node.get(k)) for k in ("layout_x", "layout_y", "layout_width", "layout_height"))


def _screen(app, name="Main"):
    view = View({"id": "root", "kind": "Rect", "style": {"width": 100, "height": 50, "background": "#112233"}},
                window=app.window)
    app.register(name, view, None)
    return view


def test_the_shell_frames_the_content_with_bars_navigation_and_zones():
    app, shell = _app()
    assert _box(shell.node) == (0, 0, 1000, 600)
    assert _box(shell.top_bar.node) == (0, 0, 1000, 64) and _box(shell.status_bar.node) == (0, 576, 1000, 24)
    assert _box(shell.navigation.node)[:2] == (0, 64)  # the rail at the start, under the bar
    left, right, bottom = (shell._zone_nodes[s] for s in ("left", "right", "bottom"))
    assert _box(left) == (80, 64, 240, 512) and _box(right) == (740, 64, 260, 512)
    content = _box(shell.content)
    assert content == (80 + 240 + 16, 64, 1000 - 80 - 240 - 16 - 16 - 260, 512 - 16 - 160)
    assert _box(bottom) == (content[0], 64 + content[3] + 16, content[2], 160)
    assert shell.node.get("fill") == BASE["surface"]


def test_use_shell_shows_screens_in_the_content_and_moves_one_already_shown():
    app, shell = _app()
    home = _screen(app, "Home")
    app.show("Home")
    assert home.root.parent() == app.window.root  # before a shell
    app.use_shell(shell)
    assert home.root.parent() == shell.content
    other = _screen(app, "Other")
    app.show("Other")
    assert other.root.parent() == shell.content and home.root.parent() is None
    with pytest.raises(ValueError, match="build the shell on this app's window"):
        App().use_shell(shell)


def test_the_shell_follows_the_window_as_it_resizes():
    app, shell = _app()
    app.window.resize(1200, 700)
    app.window.advance(16)
    assert _box(shell.node) == (0, 0, 1200, 700)
    assert shell._zone_nodes["left"].get("layout_width") == 240.0  # zones keep their size
    assert shell.content.get("layout_width") == 1200 - 80 - 240 - 16 - 16 - 260  # the content takes the rest


@pytest.mark.parametrize("side, dx, dy, grows", [
    ("left", 60, 0, 60), ("right", -60, 0, 60), ("bottom", 0, -40, 40), ("right", 30, 0, -30),
])
def test_dragging_a_handle_resizes_its_zone(side, dx, dy, grows):
    app, shell = _app()
    before = shell.size(side)
    handle = shell._handles[side]
    x = handle.node.get("layout_x") + 8
    y = handle.node.get("layout_y") + 8
    app.window.simulate("pointer_down", x=x, y=y)
    assert handle.interaction.dragged
    app.window.simulate("pointer_move", x=x + dx, y=y + dy)
    app.window.simulate("pointer_up", x=x + dx, y=y + dy)
    app.window.advance(16)
    assert shell.size(side) == before + grows and not handle.interaction.dragged
    across = "layout_width" if side in ("left", "right") else "layout_height"
    assert shell._zone_nodes[side].get(across) == before + grows


def test_sizes_are_clamped_and_the_keyboard_moves_a_handle():
    app, shell = _app()
    handle = shell._handles["left"].node
    assert (handle.get("role"), handle.get("label")) == ("slider", "Resize the left panels")
    assert handle.get("cursor") == "col_resize" and shell._handles["bottom"].node.get("cursor") == "row_resize"
    assert shell.set_size("left", 10) == MIN_ZONE
    high = shell.set_size("left", 10_000)
    assert high == pytest.approx(0.7 * shell.middle.get("layout_width"))
    assert (handle.get("value"), handle.get("value_min"), handle.get("value_max")) == (high, MIN_ZONE, high)
    shell.set_size("left", 240)
    handle.focus()
    app.window.simulate("key_down", key="arrow_right")
    assert shell.size("left") == 240 + STEP
    app.window.simulate("key_down", key="home")
    assert shell.size("left") == MIN_ZONE
    shell._handles["right"].node.focus()
    app.window.simulate("key_down", key="arrow_left")  # a right zone grows leftwards
    assert shell.size("right") == 260 + STEP


def test_a_layout_is_plain_data_and_restores_panels_shown_ones_and_sizes():
    app, shell = _app()
    shell.dock.move(shell.dock.panel("Files"), "right")
    shell.dock.show(shell.dock.panel("Properties"))
    shell.set_size("bottom", 200)
    saved = shell.layout()
    assert saved == {"zones": {
        "left": {"panels": ["Search"], "shown": "Search", "size": 240.0},
        "right": {"panels": ["Properties", "Files"], "shown": "Properties", "size": 260.0},
        "bottom": {"panels": ["Console"], "shown": "Console", "size": 200.0},
    }}
    fresh_app, fresh = _app()
    saved["zones"]["top"] = {"panels": ["Nope"], "shown": None, "size": 100}  # a zone it hasn't: skipped
    saved["zones"]["left"]["panels"].append("Gone")  # a panel no longer there: skipped
    fresh.restore(saved)
    fresh_app.window.advance(16)
    assert fresh.dock.titles("right") == ["Properties", "Files"] and fresh.dock.titles("left") == ["Search"]
    assert fresh.dock.shown_title("right") == "Properties" and fresh.size("bottom") == 200.0


def test_a_shell_re_colours_itself_its_dock_and_its_widgets():
    app, shell = _app()
    theme = Theme.resolve(theme_seed=(0x00, 0x66, 0x88, 0xFF))
    shell.set_theme(theme)
    assert shell.node.get("fill") == theme.role("surface")
    assert shell.dock._zones["left"].node.get("fill") == theme.role("surface_container_low")
    assert shell._handles["left"].grip.get("fill") == theme.role("outline")
    assert shell.top_bar.node.get("fill") == theme.role("surface")
    assert shell.status_bar.node.get("fill") == theme.role("surface_container")


def test_a_shell_rejects_an_unknown_zone():
    with pytest.raises(ValueError, match="zones are left, right, top and bottom"):
        AppShell(App().window, zones={"centre": 100})


# -- center=True: the middle is a dock zone, screens are its tabs ---------------


def _center_app():
    app = App(width=1000, height=600)
    shell = AppShell(app.window, zones={"left": 200, "bottom": 150}, center=True)
    shell.dock.add_panel("left", app.window.create("box", width=10, height=10), "Files")
    home, settings = _screen(app, "Home"), _screen(app, "Settings")
    app.use_shell(shell)
    return app, shell, home, settings


def test_with_center_the_content_is_a_dock_zone_and_screens_are_its_tabs():
    app, shell, home, settings = _center_app()
    assert shell.content == shell.dock._zones["center"].node  # a tab strip over the center
    app.show("Home")
    app.show("Settings")
    app.window.advance(16)
    assert shell.dock.titles("center") == ["Home", "Settings"] and shell.dock.shown_title("center") == "Settings"
    app.show("Home")  # its tab comes forward; Settings stays docked, alive
    assert shell.dock.shown_title("center") == "Home" and shell.dock.side_of(settings.root) == "center"
    assert _box(shell.content)[2] == 1000 - 200 - 16  # the center takes what the left zone leaves


def test_a_center_screen_or_panel_moves_like_any_panel_and_layouts_include_the_center():
    app, shell, home, settings = _center_app()
    app.show("Home")
    app.show("Settings")
    shell.dock.move(shell.dock.panel("Files"), "center")  # a panel can join the screens
    shell.dock.move(settings.root, "bottom")  # and a screen can be docked at an edge
    app.window.advance(16)
    saved = shell.layout()
    assert saved["zones"]["center"] == {"panels": ["Home", "Files"], "shown": "Files", "size": None}
    assert saved["zones"]["bottom"]["panels"] == ["Settings"]
    fresh_app, fresh, _, _ = _center_app()
    fresh_app.show("Home")
    fresh_app.show("Settings")
    fresh.restore(saved)
    assert fresh.dock.titles("center") == ["Home", "Files"] and fresh.dock.titles("bottom") == ["Settings"]
    assert fresh.dock.shown_title("center") == "Files"


def test_use_shell_with_center_docks_a_screen_already_showing():
    app = App(width=800, height=500)
    home = _screen(app, "Home")
    app.show("Home")
    shell = AppShell(app.window, center=True)
    app.use_shell(shell)
    assert shell.dock.titles("center") == ["Home"] and shell.dock.shown(("center")) == home.root
