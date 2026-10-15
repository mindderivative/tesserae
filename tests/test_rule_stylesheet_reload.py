"""#272: the app's stylesheet of `widget:` rules is applied again when it changes while the app runs (`set_stylesheet_spec`, and the file watcher
that calls it). It used to raise `unknown field(s) ['widget', 'variant']`, from the older view's own check, and keep the old rules."""

import os
import time

import pytest

from tesserae import App, Signal, ViewModel
from tesserae.spec import load_stylesheet


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.n = Signal(1)


VIEW = ("name: main\nwidget: Container\nstyle: {width: 300, height: 200, flex_direction: vertical, background: surface}\nstate: {open: false}\n"
        "children:\n  - {widget: Button, name: box, label: A}\n  - {widget: Button, name: other, variant: outlined, label: B}\n")


def sheet(radius, outlined=2):
    """Two rules: every Button, and the outlined ones over it."""
    return {"styles": [{"widget": "Button", "style": {"corner_radius": radius}},
                       {"widget": "Button", "variant": "outlined", "style": {"corner_radius": outlined}}]}


@pytest.fixture
def opened(tmp_path):
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text(VIEW)
    app = App(root=tmp_path, stylesheet_spec=sheet(7))
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    view.window.advance(16)
    return app, view


def radius(view, name):
    return view.node(f"root.{name}").get("corner_radius")


def test_the_rules_apply_before_any_change(opened):
    app, view = opened
    assert (radius(view, "box"), radius(view, "other")) == (7.0, 2.0)


def test_a_new_rule_sheet_restyles_an_open_view(opened):
    app, view = opened
    app.set_stylesheet_spec(sheet(11, 5))
    view.window.advance(600)  # a Button eases its corners
    assert (radius(view, "box"), radius(view, "other")) == (11.0, 5.0)


def test_the_old_rules_stay_if_the_new_sheet_is_wrong(opened):
    app, view = opened
    with pytest.raises(Exception):
        app.set_stylesheet_spec({"styles": [{"widget": "Button", "style": {"corner_radius": "wide"}}]})
    view.window.advance(16)
    assert radius(view, "box") == 7.0 and app._stylesheet_spec == sheet(7)
    view.handle.state("open").set(True)  # and the view is alive: its effect was put back
    assert app.bindings.viewmodel_for("main").n.get() == 1


def test_a_view_opened_after_a_change_uses_the_new_rules(opened, tmp_path):
    app, view = opened
    app.set_stylesheet_spec(sheet(11, 5))
    (tmp_path / "Views" / "Second_View.yaml").write_text(VIEW.replace("name: main", "name: second"))

    class Second(VM):
        views = "second"

    app.bind(Second)
    second = app.open_view("Second")
    assert (radius(second, "box"), radius(second, "other")) == (11.0, 5.0)


def test_state_and_the_viewmodel_survive_a_restyle(opened):
    app, view = opened
    view.handle.state("open").set(True)
    vm = app.bindings.viewmodel_for("main")
    app.set_stylesheet_spec(sheet(11))
    assert view.handle.state("open").get() is True and app.bindings.viewmodel_for("main") is vm


def test_taking_the_sheet_away_goes_back_to_the_shipped_looks(opened):
    app, view = opened
    app.set_stylesheet_spec(None)
    view.window.advance(600)
    assert radius(view, "box") not in (7.0, None) and app._stylesheet_spec is None


def test_a_sheet_one_view_rejects_leaves_every_view_with_the_old_rules(tmp_path):
    """The first view takes the new rules, the second rejects them: the first is put back."""
    (tmp_path / "Views").mkdir()
    plain = VIEW.replace("name: main", "name: first").replace(
        "  - {widget: Button, name: other, variant: outlined, label: B}\n", "")
    (tmp_path / "Views" / "First_View.yaml").write_text(plain)
    (tmp_path / "Views" / "Main_View.yaml").write_text(VIEW)

    class First(VM):
        views = "first"

    app = App(root=tmp_path, stylesheet_spec=sheet(7))
    app.bind(First)
    app.bind(VM)
    first, second = app.open_view("First"), app.open_view("Main")
    app.show("main")
    first.window.advance(16)
    broken = {"styles": [{"widget": "Button", "style": {"corner_radius": 11}},
                         {"widget": "Button", "variant": "outlined", "style": {"corner_radius": "wide"}}]}
    with pytest.raises(Exception):
        app.set_stylesheet_spec(broken)
    first.window.advance(600)
    assert radius(first, "box") == 7.0 and radius(second, "box") == 7.0
    app.set_stylesheet_spec(sheet(11, 5))  # and a good one is still taken
    first.window.advance(600)
    assert radius(first, "box") == 11.0 and radius(second, "other") == 5.0


def test_saving_the_stylesheet_file_restyles_the_open_view(tmp_path):
    import queue
    import yaml

    class Loop:
        def __init__(self):
            self.calls = queue.Queue()

        def call_soon(self, fn):
            self.calls.put(fn)

    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text(VIEW)
    sheet_file = tmp_path / "App_Stylesheet.yaml"
    sheet_file.write_text(yaml.safe_dump(sheet(7)))
    app = App(root=tmp_path, stylesheet=sheet_file)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    view.window.advance(16)
    loop = Loop()
    watchers = app._start_watchers(loop)
    try:
        time.sleep(0.3)
        sheet_file.write_text(yaml.safe_dump(sheet(13, 4)))
        stat = sheet_file.stat()
        os.utime(sheet_file, ns=(stat.st_atime_ns, stat.st_mtime_ns + 5_000_000_000))
        loop.calls.get(timeout=10)()
        view.window.advance(600)
        assert (radius(view, "box"), radius(view, "other")) == (13.0, 4.0)
    finally:
        app._stop_watchers()
