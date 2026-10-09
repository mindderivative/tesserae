"""#230: the window's size and MD3 size classes as names a view can read -- `app.width_class`, `app.height_class`, `app.window_width`."""

import pytest

from tesserae import App, ViewModel, tokens


@pytest.mark.parametrize("width, expected", [
    (0, "compact"), (599.9, "compact"), (600, "medium"), (839.9, "medium"), (840, "expanded"), (1199.9, "expanded"),
    (1200, "large"), (1599.9, "large"), (1600, "extra_large"), (4000, "extra_large"),
])
def test_width_classes_start_where_md3_says(width, expected):
    assert tokens.width_class(width) == expected


@pytest.mark.parametrize("height, expected", [(0, "compact"), (479.9, "compact"), (480, "medium"), (899.9, "medium"), (900, "expanded"), (2000, "expanded")])
def test_height_classes_start_where_md3_says(height, expected):
    assert tokens.height_class(height) == expected


class VM(ViewModel):
    views = "main"


VIEW = """name: main
widget: Container
style: {flex_direction: vertical, width: 400, height: 300}
children:
  - widget: Text
    name: kind
    text: "{{ app.width_class }} {{ app.height_class }} {{ app.window_width }}"
    typography_role: body_large
    style: {foreground: on_surface}
  - {widget: Container, name: rail, if: "app.width_class != 'compact'", style: {width: 80, height: 40, background: primary}}
  - {widget: Container, name: bar, if: "app.width_class == 'compact'", style: {width: 80, height: 40, background: secondary}}
"""


def opened(tmp_path, **kwargs):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(VIEW)
    app = App(root=tmp_path, **kwargs)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    view.window.advance(16)
    return app, view


def shown(view, name):
    return f"root.{name}" in view._built.specs


def test_the_app_starts_with_the_window_s_size(tmp_path):
    app, _ = opened(tmp_path, width=500, height=700)
    assert (app.window_width.get(), app.window_height.get()) == (500.0, 700.0)
    assert (app.width_class.get(), app.height_class.get()) == ("compact", "medium")


def test_a_view_reads_the_classes(tmp_path):
    _, view = opened(tmp_path, width=500, height=700)
    assert view.node("root.kind").get("text") == "compact medium 500.0"


def test_resizing_the_window_changes_what_a_view_shows(tmp_path):
    app, view = opened(tmp_path, width=500, height=400)
    assert shown(view, "bar") and not shown(view, "rail")
    view.window.simulate("resize", width=900, height=400)
    view.window.advance(16)
    assert app.width_class.get() == "expanded"
    assert shown(view, "rail") and not shown(view, "bar") and view.node("root.kind").get("text") == "expanded compact 900.0"
    view.window.simulate("resize", width=300, height=400)
    view.window.advance(16)
    assert shown(view, "bar") and not shown(view, "rail")


def test_the_view_checks_clean(tmp_path):
    app, _ = opened(tmp_path)
    assert app.check() == []


def test_a_viewmodel_that_has_its_own_app_keeps_it(tmp_path):
    class Own(ViewModel):
        views = "main"
        app = type("Mine", (), {"width_class": "mine", "height_class": "mine", "window_width": 1})()

    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text(VIEW.replace("if: \"app.width_class != 'compact'\"", "if: \"True\"").replace("if: \"app.width_class == 'compact'\"", "if: \"False\""))
    app = App(root=tmp_path)
    app.bind(Own)
    view = app.open_view("Main")
    view.window.advance(16)
    assert view.node("root.kind").get("text") == "mine mine 1"
