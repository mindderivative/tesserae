"""M52 Phase 4: hot reload of the shell file (M52 Q4). An edit patches
what can change in place -- the bars, the status text, zone sizes, the
rail's items, panels added or moved -- keeping the user's own drags and
sizes where the file didn't change them. A structural edit (a zone or
bar added or removed, `center`, a panel removed) is logged as needing a
restart. A panel or handler it can't find fails before anything changes.
"""

import queue

import pytest
from loguru import logger

from tesserae import App, Theme, View
from tesserae.shell_file import ShellSpecError, load_shell_spec

SEED = (0x67, 0x50, 0xA4, 0xFF)

SHELL = """
top_bar: {title: Studio, trailing_icons: [settings]}
navigation:
  items:
    - {screen: Home, icon: home}
    - {screen: Notes, icon: search}
status_bar: {text: Ready}
zones: {left: 220, bottom: 160}
panels: {left: [Files, Outline], bottom: [Console]}
"""

PLAIN = 'id: root\nkind: Rect\nstyle: {width: 100, height: 40, background: "#112233"}\n'


@pytest.fixture
def studio(tmp_path):
    for name in ("Files", "Outline", "Search"):
        (tmp_path / f"{name}_View.yaml").write_text(PLAIN)
    app = App(width=1000, height=600, theme_seed=SEED, dark=False)
    for name in ("Home", "Notes", "Console", "Settings"):
        app.register(name, View({"id": "root", "kind": "Rect",
                                 "style": {"width": 50, "height": 50, "background": "#445566"}},
                                window=app.window), None)
    path = tmp_path / "Studio_Shell.yaml"
    path.write_text(SHELL)
    app.show("Home")
    shell = app.load_shell(path)
    app.window.advance(16)
    yield app, shell, path
    app._stop_watchers()


def _edit(app, path, text):
    """What the watcher does: re-read the file, then apply it."""
    path.write_text(text)
    app._reload_shell(load_shell_spec(path))
    app.window.advance(16)


def _logs(fn):
    messages = []
    sink = logger.add(lambda m: messages.append((m.record["level"].name, m.record["message"])), level="INFO")
    try:
        fn()
    finally:
        logger.remove(sink)
    return messages


def test_a_new_title_or_icons_rebuild_the_top_bar_in_its_place(studio):
    app, shell, path = studio
    old = shell.top_bar
    _edit(app, path, SHELL.replace("title: Studio, trailing_icons: [settings]",
                                   "title: Studio 2, trailing_icons: [settings, search]"))
    bar = shell.top_bar
    assert bar is not old and shell.node.children()[0] == bar.node
    assert bar.part("title").get("text") == "Studio 2" and bar.part("trailing1")
    with pytest.raises(ValueError):
        old.node.get("visible")  # the old bar is gone
    assert bar.node.get("layout_width") == 1000.0
    app.set_dark(True)  # the new bar follows the app's theme too
    assert bar.node.get("fill") == Theme.resolve(theme_seed=SEED, dark=True).role("surface")


def test_the_status_text_changes_in_place(studio):
    app, shell, path = studio
    node, bar, rail = shell.status_bar.node, shell.top_bar, shell.navigation
    _edit(app, path, SHELL.replace("text: Ready", "text: Saved"))
    assert shell.status_bar.node == node and shell.status_bar.part("text").get("text") == "Saved"
    assert shell.top_bar is bar and shell.navigation is rail  # untouched parts aren't rebuilt


def test_a_zone_size_the_file_changes_is_set_and_one_it_doesnt_is_left_as_the_user_made_it(studio):
    app, shell, path = studio
    shell.set_size("bottom", 200)  # the user dragged it
    _edit(app, path, SHELL.replace("left: 220", "left: 260"))
    assert shell.size("left") == 260 and shell.size("bottom") == 200


def test_new_navigation_items_rebuild_the_rail_keeping_the_current_screen_selected(studio):
    app, shell, path = studio
    app.show("Notes")
    _edit(app, path, SHELL.replace("    - {screen: Notes, icon: search}",
                                   "    - {screen: Notes, icon: search}\n    - {screen: Settings, icon: settings}"))
    rail = shell.navigation
    assert shell.middle.children()[0] == rail.node and rail.part("item2.label").get("text") == "Settings"
    assert rail.selected.get() == 1
    app.window.simulate("click", node=rail.part("item2"))
    assert app.current == "Settings"


def test_on_navigate_added_by_an_edit_calls_the_viewmodel(tmp_path):
    calls = []

    class Nav:
        def go(self, screen):
            calls.append(screen)

    app = App(width=800, height=500)
    for name in ("Home", "Notes"):
        app.register(name, View({"id": "root", "kind": "Rect",
                                 "style": {"width": 5, "height": 5, "background": "#000000"}}, window=app.window), None)
    path = tmp_path / "Studio_Shell.yaml"
    text = "navigation:\n  items: [{screen: Home, icon: home}, {screen: Notes, icon: search}]\n"
    path.write_text(text)
    shell = app.load_shell(path, viewmodel=Nav())
    _edit(app, path, text + "  on_navigate: go\n")
    app.window.simulate("click", node=shell.navigation.part("item1"))
    assert calls == ["Notes"]


def test_panels_the_file_adds_or_moves_are_placed_and_the_users_drags_are_kept(studio):
    app, shell, path = studio
    shell.dock.move(shell.dock.panel("Outline"), "bottom")  # the user dragged Outline
    _edit(app, path, SHELL.replace("panels: {left: [Files, Outline], bottom: [Console]}",
                                   "panels: {left: [Files, Outline, Search, Console], bottom: []}"))
    assert shell.dock.side_of(shell.dock.panel("Search")) == "left"  # added
    assert shell.dock.side_of(shell.dock.panel("Console")) == "left"  # moved by the file
    assert shell.dock.side_of(shell.dock.panel("Outline")) == "bottom"  # the file didn't move it: the user's drag kept


def test_structural_edits_are_logged_as_needing_a_restart_and_the_rest_applies(studio):
    app, shell, path = studio
    text = (SHELL.replace("top_bar: {title: Studio, trailing_icons: [settings]}\n", "")
            .replace("zones: {left: 220, bottom: 160}", "zones: {left: 220, right: 200}\ncenter: true")
            .replace("panels: {left: [Files, Outline], bottom: [Console]}", "panels: {left: [Files]}")
            .replace("text: Ready", "text: Saved"))
    logs = _logs(lambda: _edit(app, path, text))
    warnings = [m for level, m in logs if level == "WARNING"]
    assert warnings == [
        "the shell file Studio_Shell.yaml changed (top_bar removed): restart the app to see it",
        "the shell file Studio_Shell.yaml changed (zones right added, bottom removed): restart the app to see it",
        "the shell file Studio_Shell.yaml changed (center changed to true): restart the app to see it",
        "the shell file Studio_Shell.yaml changed (panels removed (Console, Outline)): restart the app to see it",
    ]
    assert shell.top_bar is not None and set(shell._zone_nodes) == {"left", "bottom"} and not shell.center
    assert shell.dock.titles("bottom") == ["Console"]  # a removed panel stays until a restart
    assert shell.status_bar.part("text").get("text") == "Saved"  # what could change did
    assert ("INFO", f"reloaded the shell from {path}") in logs


def test_an_edit_naming_a_missing_panel_changes_nothing(studio):
    app, shell, path = studio
    path.write_text(SHELL.replace("text: Ready", "text: Saved").replace("[Console]", "[Console, Nowhere]"))
    with pytest.raises(ShellSpecError, match="panels.bottom: no screen is registered as 'Nowhere'"):
        app._reload_shell(load_shell_spec(path))
    assert shell.status_bar.part("text").get("text") == "Ready" and "Nowhere" not in str(app._shell_spec)


def test_each_edit_is_compared_with_the_last_one_applied(studio):
    """The file moves Console left; the user drags it back; a later edit
    that doesn't mention a move leaves it where the user put it."""
    app, shell, path = studio
    moved = SHELL.replace("panels: {left: [Files, Outline], bottom: [Console]}",
                          "panels: {left: [Files, Outline, Console], bottom: []}")
    _edit(app, path, moved)
    assert shell.dock.side_of(shell.dock.panel("Console")) == "left"
    shell.dock.move(shell.dock.panel("Console"), "bottom")
    _edit(app, path, moved.replace("text: Ready", "text: Saved"))
    assert shell.dock.side_of(shell.dock.panel("Console")) == "bottom"


class FakeHandle:
    def __init__(self):
        self.queued = queue.Queue()

    def call_soon(self, fn):
        self.queued.put(fn)


def test_hot_reload_watches_the_shell_file(studio):
    app, shell, path = studio
    handle = FakeHandle()
    logs = _logs(lambda: app._start_watchers(handle))
    assert ("INFO", "hot reload: watching the shell file Studio_Shell.yaml") in logs
    assert any("and 0 theme/stylesheet file(s)" in m for _, m in logs)  # the shell file isn't counted there
    for _ in range(40):
        path.write_text(SHELL.replace("text: Ready", "text: Watched"))
        try:
            reload = handle.queued.get(timeout=0.25)
            break
        except queue.Empty:
            continue
    else:
        raise AssertionError("the shell file's edit was never queued")
    reload()
    assert shell.status_bar.part("text").get("text") == "Watched"
