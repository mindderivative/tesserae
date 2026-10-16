"""#268: `ViewDialog` reads its view with the older loader. A view in the current language used to fail inside it with `every widget needs an id`; it is now refused up
front with what to write instead (a modal `widget: Overlay` in a view), by path and by name, and a view in the older syntax still works."""

import pytest

from tesserae import App
from tesserae.overlays import ViewDialog

CURRENT = "name: Settings\nwidget: Container\nchildren:\n  - {widget: Text, name: t, text: hi, typography_role: body_large, style: {foreground: on_surface}}\n"
OLDER = "id: root\nkind: Container\nchildren:\n  - id: body\n    kind: Text\n    text: {content: Hello, typography_role: body_large}\n    style: {foreground: on_surface}\n"


def _app(tmp_path=None):
    return App(width=480, height=320, root=tmp_path) if tmp_path is not None else App(width=480, height=320)


def test_a_current_language_view_by_path_is_refused_and_says_what_to_do(tmp_path):
    (tmp_path / "Settings_View.yaml").write_text(CURRENT)
    app = _app()
    with pytest.raises(ValueError) as caught:
        ViewDialog(app.window, tmp_path / "Settings_View.yaml")
    text = str(caught.value)
    assert "Settings_View.yaml" in text and "widget: Overlay" in text and "surface.dismiss" in text and "current language" in text


def test_a_current_language_view_by_name_is_refused_too(tmp_path):
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Settings_View.yaml").write_text(CURRENT)
    app = _app(tmp_path)
    with pytest.raises(ValueError, match="widget: Overlay"):
        ViewDialog(app.window, "Settings")


def test_a_view_in_the_older_syntax_still_opens_in_it(tmp_path):
    (tmp_path / "Settings_View.yaml").write_text(OLDER)
    app = _app()
    dialog = ViewDialog(app.window, tmp_path / "Settings_View.yaml", width=320, height=200)
    dialog.open()
    app.window.advance(16)
    assert dialog.is_open and dialog.content.node("body").get("text") == "Hello"


def test_a_file_that_is_missing_or_broken_still_gets_the_older_loaders_own_message(tmp_path):
    app = _app()
    with pytest.raises(Exception) as missing:
        ViewDialog(app.window, tmp_path / "Nope_View.yaml")
    assert "widget: Overlay" not in str(missing.value)
    (tmp_path / "Bad_View.yaml").write_text("widget: [")
    with pytest.raises(Exception) as broken:
        ViewDialog(app.window, tmp_path / "Bad_View.yaml")
    assert "widget: Overlay" not in str(broken.value)


def test_the_replacement_the_message_names_works(tmp_path):
    """A modal `widget: Overlay` bound to `open`, closed by `surface.dismiss`, is the dialog the message points to."""
    from tesserae import Signal, ViewModel

    class VM(ViewModel):
        views = "main"

        def __init__(self):
            super().__init__()
            self.show = Signal(True)

    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        "name: main\nwidget: Container\nstyle: {width: 300, height: 200, background: surface}\nchildren:\n"
        "  - widget: Overlay\n    name: dlg\n    open: \"{{ show }}\"\n    modal: true\n    style: {width: 200, height: 100, background: surface_container_high}\n"
        "    children:\n      - {widget: Button, name: close, label: Close, handlers: {on_click: surface.dismiss}}\n")
    app = App(root=tmp_path, width=300, height=200)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    view.window.advance(50)
    vm = app.bindings.viewmodel_for("main")
    assert vm.show.get() is True
    view.window.simulate("click", node=view.node("root.dlg.close"))
    view.window.advance(50)
    assert vm.show.get() is False
