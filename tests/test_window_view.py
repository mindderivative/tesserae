"""0.4.4 (#98): `kind: Window`, the root of a view that is the OS window, and `borderless`."""

import sys

import pytest
import yaml

from tesserae import App, View
from tesserae.spec.window import WindowError, expand_windows, window_of
from tesserae.window_view import WindowViewModel

SEED = (0x67, 0x50, 0xA4, 0xFF)
WINDOW = """
id: root
kind: Window
title: Tasks
borderless: true
min_width: 320
min_height: 200
style: {width: 640, height: 400, background: surface, flex_direction: vertical}
title_bar: {icon: home}
children:
  - {id: hello, kind: Text, text: {content: "Hello", typography_role: headline_small}, style: {foreground: on_surface}}
"""


def _project(tmp_path, text=WINDOW, name="Window"):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / f"{name}_View.yaml").write_text(text)
    return tmp_path


def _app(tmp_path, **kwargs):
    return App(root=tmp_path, theme_seed=SEED, dark=True, **kwargs)


# -- the spec ------------------------------------------------------------------------------------

def test_a_window_becomes_a_container_with_its_title_bar_and_content():
    spec = expand_windows(yaml.safe_load(WINDOW))
    assert spec["kind"] == "Container" and spec["window"] == {"title": "Tasks", "borderless": True, "min_width": 320.0,
                                                            "min_height": 200.0, "size": (640.0, 400.0)}
    assert spec["style"] == {"width": "100%", "height": "100%", "flex_direction": "vertical", "background": "surface"}
    bar, content = spec["children"]
    assert bar["kind"] == "TitleBar" and bar["id"] == "root.title_bar" and bar["title"] == "Tasks" and bar["icon"] == "home"
    assert "buttons" not in bar  # a borderless window has the window buttons
    assert content["id"] == "root.content" and content["children"][0]["id"] == "hello"
    assert content["style"] == {"flex": "fill", "flex_direction": "vertical"}  # the size and background are the window's
    assert window_of(spec) is spec["window"]


def test_a_bordered_windows_bar_is_a_plain_header():
    spec = expand_windows({"id": "w", "kind": "Window", "title": "T", "title_bar": {"title": "Mine"}})
    assert spec["window"]["borderless"] is False
    assert spec["children"][0]["buttons"] == [] and spec["children"][0]["title"] == "Mine"


def test_no_title_bar_means_just_the_content():
    spec = expand_windows({"id": "w", "kind": "Window", "children": [{"id": "a", "kind": "Rect"}]})
    assert [c["id"] for c in spec["children"]] == ["w.content"]


def test_a_view_that_is_not_a_window_passes_through():
    spec = {"id": "r", "kind": "Container", "children": []}
    assert expand_windows(spec) == spec and window_of(spec) is None


@pytest.mark.parametrize("node, message", [
    ({"kind": "Window"}, "needs an `id:`"),
    ({"id": "w", "kind": "Window", "bogus": 1}, "takes .*not bogus"),
    ({"id": "w", "kind": "Window", "title": 3}, "title is text"),
    ({"id": "w", "kind": "Window", "borderless": "yes"}, "borderless is true or false"),
    ({"id": "w", "kind": "Window", "min_width": -1}, "min_width is a number of pixels"),
    ({"id": "w", "kind": "Window", "style": {"width": "50%", "height": 10}}, "a width and a height in pixels"),
    ({"id": "w", "kind": "Window", "title_bar": {"bogus": 1}}, "title_bar takes"),
])
def test_a_badly_written_window_is_refused(node, message):
    with pytest.raises(WindowError, match=message):
        expand_windows(node)


def test_a_window_is_the_root_only():
    spec = {"id": "r", "kind": "Container", "children": [{"id": "c", "kind": "Container",
                                                          "children": [{"id": "w", "kind": "Window"}]}]}
    with pytest.raises(WindowError, match=r"widget 'w': a Window is the root of its view .* inside 'c'"):
        expand_windows(spec)


# -- the app ----------------------------------------------------------------------------------

def test_loading_a_window_view_sets_the_os_window(tmp_path):
    app = _app(_project(tmp_path))
    view, viewmodel = app.load("Window")
    app.window.advance(16)
    assert isinstance(viewmodel, WindowViewModel)
    assert app.borderless is True and app.resize_border == 6
    assert (app.min_width, app.min_height) == (320, 200)
    assert app.window.get("title") == "Tasks"
    assert (app.window.get("width"), app.window.get("height")) == (640.0, 400.0)
    assert view.node("root").get("layout_height") == 400.0 and view.node("root.title_bar").get("layout_height") == 40.0
    assert view.node("hello").get("text") == "Hello" and app.current == "Window"


def test_the_title_bars_window_buttons_work_in_a_window_view(tmp_path, monkeypatch):
    app = _app(_project(tmp_path))
    view, _ = app.load("Window")
    closed = []
    monkeypatch.setattr(app, "close", lambda: closed.append(True))
    app.window.advance(16)
    app.window.simulate("click", view.node("root.title_bar.close"))
    assert closed == [True]


def test_the_window_view_can_have_a_viewmodel_of_its_own(tmp_path):
    name = f"Chrome{abs(hash(str(tmp_path))) % 10**8}"
    _project(tmp_path, WINDOW.replace("children:", "children:\n  - {id: shown, kind: Text, text: {content: '', typography_role: body_large}, style: {foreground: on_surface}, bindings: {text: \"{{ label.get() }}\"}}"), name)
    (tmp_path / "ViewModels").mkdir()
    (tmp_path / "ViewModels" / f"{name}_ViewModel.py").write_text(
        f"from tesserae import Signal, ViewModel\n\n\nclass {name}ViewModel(ViewModel):\n    def __init__(self, view):\n"
        "        self.label = Signal('mine')\n        super().__init__(view)\n")
    sys.path.insert(0, str(tmp_path / "ViewModels"))
    try:
        app = _app(tmp_path)
        view, viewmodel = app.load(name)
        assert type(viewmodel).__name__ == f"{name}ViewModel" and view.node("shown").get("text") == "mine"
    finally:
        sys.path.remove(str(tmp_path / "ViewModels"))
        sys.modules.pop(f"{name}_ViewModel", None)


def test_window_view_names_the_view_at_construction(tmp_path):
    _project(tmp_path, name="Frame")
    app = _app(tmp_path, window_view="Frame")
    assert app.current == "Frame" and app.borderless


def test_a_second_window_view_is_an_error(tmp_path):
    _project(tmp_path)
    _project(tmp_path, name="Other")
    app = _app(tmp_path)
    app.load("Window")
    with pytest.raises(ValueError, match=r"already has a window view \('Window'\); 'Other' is a second"):
        app.load("Other")


def test_a_window_view_is_not_embedded(tmp_path):
    _project(tmp_path)
    (tmp_path / "Views" / "Host_View.yaml").write_text(
        "id: root\nkind: Container\nchildren:\n  - {id: w, view: Window}\n")
    app = _app(tmp_path)
    with pytest.raises(ValueError, match="can't be embedded"):
        View(tmp_path / "Views" / "Host_View.yaml", window=app.window)


def test_another_screen_has_no_place_in_a_window_view_yet(tmp_path):
    name = f"Side{abs(hash(str(tmp_path))) % 10**8}"
    _project(tmp_path)
    (tmp_path / "Views" / f"{name}_View.yaml").write_text("id: root\nkind: Container\n")
    (tmp_path / "ViewModels").mkdir()
    (tmp_path / "ViewModels" / f"{name}_ViewModel.py").write_text(
        f"from tesserae import ViewModel\n\n\nclass {name}ViewModel(ViewModel):\n    pass\n")
    app = _app(tmp_path)
    app.load("Window")
    try:
        app.load(name)
        with pytest.raises(ValueError, match=f"has no place for the screen '{name}'"):
            app.show(name)
    finally:
        sys.modules.pop(f"{name}_ViewModel", None)


def test_a_non_window_view_with_no_viewmodel_is_still_an_error(tmp_path):
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Plain_View.yaml").write_text("id: root\nkind: Container\n")
    app = _app(tmp_path)
    with pytest.raises(Exception, match="ViewModel"):
        app.load("Plain")


def test_editing_the_window_view_while_running_sets_the_window_again(tmp_path):
    app = _app(_project(tmp_path))
    view, _ = app.load("Window")
    spec = yaml.safe_load(WINDOW)
    spec["title"], spec["borderless"], spec["min_width"] = "Renamed", False, 100
    view.reconcile(spec)
    assert app.window.get("title") == "Renamed" and app.borderless is False and app.min_width == 100


# -- borderless on App -------------------------------------------------------------------------

def test_borderless_sets_the_os_window_and_its_resize_border():
    app = App(theme_seed=SEED, borderless=True)
    assert app.borderless is True and app.window.get("decorations") is False and app.resize_border == 6
    app.borderless = False
    assert app.borderless is False and app.window.get("decorations") is True and app.resize_border == 0
    app.borderless = True
    assert app.borderless is True and app.resize_border == 6
    assert App(theme_seed=SEED).borderless is False


def test_a_window_view_with_no_app_is_just_a_container():
    view = View(yaml.safe_load(WINDOW))
    assert view.node("root").get("kind") == "box" and view.node("hello").get("text") == "Hello"


# -- the OS window's options (#204) ---------------------------------------------------------------

FLAGS = "fullscreen: true\nmaximized: true\ntransparent: true\nblur_behind: true\nclick_through: true\n"


def test_the_flags_reach_the_window_spec_and_a_wrong_one_is_named():
    spec = expand_windows(yaml.safe_load(WINDOW + FLAGS.replace("\n", "\n", 1)))
    assert window_of(spec) == {"title": "Tasks", "borderless": True, "min_width": 320.0, "min_height": 200.0, "size": (640.0, 400.0),
                               "fullscreen": True, "maximized": True, "transparent": True, "blur_behind": True, "click_through": True}
    with pytest.raises(WindowError, match="fullscreen is true or false, got 'yes'"):
        expand_windows({"id": "w", "kind": "Window", "fullscreen": "yes"})


def test_a_window_without_flags_leaves_the_os_window_alone():
    assert "fullscreen" not in window_of(expand_windows(yaml.safe_load(WINDOW)))


def test_loading_a_window_with_flags_sets_the_os_window(tmp_path):
    app = _app(_project(tmp_path, WINDOW + "fullscreen: true\ntransparent: true\nclick_through: true\n"))
    app.load("Window")
    assert app.fullscreen is True and app.window.get("transparent") is True and app.window.get("click_through") is True


def test_a_window_view_in_the_new_syntax_takes_the_flags(tmp_path):
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        "name: main\nwidget: Window\ntitle: Tasks\nfullscreen: true\nmaximized: true\nstyle: {width: 300, height: 200}\nchildren:\n"
        "  - {widget: Text, text: Hi, typography_role: body_medium, style: {foreground: on_surface}}\n")
    app = _app(tmp_path)
    app.open_view("Main")
    assert app.fullscreen is True and app.maximized.get() is True
