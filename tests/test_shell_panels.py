"""M52 Phase 3: a shell file's panels and navigation (M52 Q2-Q3).

A panel is a view named like a screen: the screen registered under that
name, or else `<Name>_View.yaml` (with `<Name>_ViewModel.py`, if any)
next to the shell file, loaded and registered under it. The rail's items
name screens: choosing one shows it (or calls `on_navigate`), and
`app.show` from anywhere moves the rail's selection.
"""

import sys

import pytest

from tesserae import App, View
from tesserae.shell_file import ShellSpecError
from tesserae.spec import ViewWatcher

SHELL = """
navigation:
  items:
    - {screen: Home, icon: home}
    - {screen: Notes, icon: search}
zones: {left: 220, bottom: 160}
center: %s
panels: {left: [Files, Outline], bottom: [Console]}
"""

PANEL = """
id: root
kind: Container
children:
  - id: label
    kind: Text
    text: {content: "", font_family: Roboto, font_size: 14}
    style: {foreground: "#000000", width: 100, height: 20}
    bindings: {text: "{{ title.get() }}"}
"""

PANEL_VM = '''
from tesserae import Signal, ViewModel


class FilesViewModel(ViewModel):
    def __init__(self, view):
        self.title = Signal("3 files")
        super().__init__(view)
'''

PLAIN = 'id: root\nkind: Rect\nstyle: {width: 100, height: 40, background: "#112233"}\n'


class Nav:
    def __init__(self):
        self.calls = []

    def go(self, screen):
        self.calls.append(screen)


@pytest.fixture
def studio(tmp_path):
    """`Files` (a view and a ViewModel) and `Outline` (a view alone) as
    files next to the shell file; `Console` is registered in Python."""
    (tmp_path / "Files_View.yaml").write_text(PANEL)
    (tmp_path / "Files_ViewModel.py").write_text(PANEL_VM)
    (tmp_path / "Outline_View.yaml").write_text(PLAIN)
    sys.modules.pop("Files_ViewModel", None)
    yield tmp_path
    sys.modules.pop("Files_ViewModel", None)


def _app(tmp_path, text=None, center=False, **load):
    app = App(width=1000, height=600)
    for name in ("Home", "Notes", "Console"):
        app.register(name, View({"id": "root", "kind": "Rect",
                                 "style": {"width": 50, "height": 50, "background": "#445566"}},
                                window=app.window), None)
    shell_file = tmp_path / "Studio_Shell.yaml"
    shell_file.write_text(text if text is not None else SHELL % ("true" if center else "false"))
    app.show("Home")
    shell = app.load_shell(shell_file, **load)
    app.window.advance(16)
    return app, shell


def _root(app, name):
    return app._registered[name].view.root


def test_panels_come_from_files_or_registered_screens_titled_by_name(studio):
    app, shell = _app(studio)
    assert shell.dock.titles("left") == ["Files", "Outline"] and shell.dock.titles("bottom") == ["Console"]
    files = app._registered["Files"]
    assert shell.dock.panel("Files") == files.view.root
    assert files.view.node("label").get("text") == "3 files"  # its ViewModel, wired
    files.viewmodel.title.set("4 files")
    assert files.view.node("label").get("text") == "4 files"
    assert app._registered["Outline"].viewmodel is None  # no ViewModel file: none
    assert shell.dock.panel("Console") == _root(app, "Console")  # the Python-registered one


def test_a_layout_names_panels_by_their_screen_names(studio):
    app, shell = _app(studio)
    shell.dock.move(shell.dock.panel("Outline"), "bottom")
    saved = shell.layout()
    assert saved["zones"]["left"]["panels"] == ["Files"]
    assert saved["zones"]["bottom"]["panels"] == ["Console", "Outline"]
    _, fresh = _app(studio)
    fresh.restore(saved)
    assert fresh.dock.titles("bottom") == ["Console", "Outline"]


def test_panels_are_screens_so_hot_reload_watches_their_files(studio):
    app, shell = _app(studio)

    class Handle:
        def call_soon(self, fn):
            pass

    watchers = app._start_watchers(Handle())
    try:
        watched = {w._path.name for w in watchers if isinstance(w, ViewWatcher)}
        assert {"Files_View.yaml", "Outline_View.yaml"} <= watched
    finally:
        app._stop_watchers()


@pytest.mark.parametrize("center", [False, True])
def test_showing_a_panel_brings_its_tab_forward_and_leaves_it_docked(studio, center):
    app, shell = _app(studio, center=center)
    assert shell.dock.shown("left") == _root(app, "Outline")  # the last one docked is in front
    app.show("Files")
    assert shell.dock.shown("left") == _root(app, "Files") and shell.dock.side_of(_root(app, "Files")) == "left"
    app.show("Notes")  # the next screen doesn't take a panel out of its zone
    assert shell.dock.side_of(_root(app, "Files")) == "left"
    if center:
        assert shell.dock.shown("center") == _root(app, "Notes")
    else:
        assert shell.content.children()[-1] == _root(app, "Notes") and _root(app, "Home").parent() is None


def test_choosing_a_rail_item_shows_its_screen(studio):
    app, shell = _app(studio, center=True)
    app.window.simulate("click", node=shell.navigation.part("item1"))
    assert app.current == "Notes" and shell.dock.shown("center") == _root(app, "Notes")


def test_the_rail_follows_app_show_without_calling_its_handler(studio):
    nav = Nav()
    app, shell = _app(studio, text=(SHELL % "false").replace("items:", "on_navigate: go\n  items:"), viewmodel=nav)
    app.show("Notes")  # from code, not the rail
    assert shell.navigation.selected.get() == 1 and nav.calls == []
    app.show("Files")  # not a navigation item: the rail stays put
    assert shell.navigation.selected.get() == 1


def test_on_navigate_calls_the_viewmodel_instead_of_showing(studio):
    nav = Nav()
    app, shell = _app(studio, text=(SHELL % "false").replace("items:", "on_navigate: go\n  items:"), viewmodel=nav)
    app.window.simulate("click", node=shell.navigation.part("item1"))
    assert nav.calls == ["Notes"] and app.current == "Home"


def test_a_missing_panel_or_handler_fails_before_anything_is_built(studio):
    app = App(width=800, height=500)
    shell_file = studio / "Studio_Shell.yaml"
    shell_file.write_text("zones: {left: 200}\npanels: {left: [Nowhere]}\n")
    with pytest.raises(ShellSpecError, match=r"Studio_Shell.yaml: panels.left: no screen is registered as 'Nowhere'"):
        app.load_shell(shell_file)
    shell_file.write_text("navigation: {items: [{screen: Home, icon: home}], on_navigate: go}\n")
    with pytest.raises(ShellSpecError, match="navigation.on_navigate: names 'go', but load_shell was given no"):
        app.load_shell(shell_file)
    with pytest.raises(ShellSpecError, match="navigation.on_navigate: object has no method 'go'"):
        app.load_shell(shell_file, viewmodel=object())
    assert app._shell is None and app.window.root.children() == []  # nothing was built


def test_a_viewmodel_file_without_its_class_is_named(studio):
    (studio / "Files_ViewModel.py").write_text("class Other:\n    pass\n")
    with pytest.raises(ShellSpecError, match="Files_ViewModel.py has no class FilesViewModel"):
        _app(studio)


def test_center_panels_join_the_screens(studio):
    app, shell = _app(studio, text="center: true\npanels: {center: [Files]}\n")
    assert shell.dock.titles("center") == ["Home", "Files"]


@pytest.mark.parametrize("center", [False, True])
def test_the_screen_showing_can_be_placed_as_a_panel(studio, center):
    """`Home` is showing -- in `content`, or as a center tab -- when the
    file places it in the left zone: it moves there, and stays there when
    the next screen shows."""
    text = f"zones: {{left: 220}}\ncenter: {'true' if center else 'false'}\npanels: {{left: [Home]}}\n"
    app, shell = _app(studio, text=text)
    home = _root(app, "Home")
    assert shell.dock.side_of(home) == "left" and home.parent() != shell.content
    app.show("Notes")
    assert shell.dock.side_of(home) == "left" and home.parent() is not None  # still in the tree, not just the dock's list
    if not center:
        assert shell.content.children()[-1] == _root(app, "Notes")


def test_a_viewmodel_module_the_app_already_imported_is_reused(studio):
    import importlib.util

    spec = importlib.util.spec_from_file_location("Files_ViewModel", studio / "Files_ViewModel.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["Files_ViewModel"] = module  # as `from Files_ViewModel import FilesViewModel` in app.py would
    spec.loader.exec_module(module)
    app, _ = _app(studio)
    assert type(app._registered["Files"].viewmodel) is module.FilesViewModel
