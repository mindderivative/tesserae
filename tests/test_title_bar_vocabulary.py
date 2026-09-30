"""0.3.0 M3 Phase 1 (#49): a title bar's vocabulary in YAML views.
`window_region: drag | none` on any node, and the handler names
`window.minimize`, `window.maximize`, `window.restore`,
`window.toggle_maximized` and `window.close`, which call the app's
window actions without a ViewModel method.
"""

import pytest
import yaml

from tesserae import App, View, ViewModel
from tesserae.spec.build import SpecBuildError

SEED = (0x67, 0x50, 0xA4, 0xFF)

BAR = {"id": "root", "kind": "Container", "style": {"width": 400, "height": 300, "flex_direction": "vertical"},
       "children": [{"id": "bar", "kind": "Rect", "window_region": "drag",
                     "style": {"width": 400, "height": 40, "background": "#6750A4"}},
                    {"id": "body", "kind": "Rect", "style": {"width": 400, "height": 200, "background": "#FFFFFF"}}]}


def _file(tmp_path, spec, name="Home_View.yaml"):
    path = tmp_path / name
    path.write_text(yaml.safe_dump(spec), encoding="utf-8")
    return path


def _shown(app, path, name):
    """A view in the window (a built view isn't, until it's shown), so
    presses and clicks reach it."""
    view = app.build_view(path)
    app.register(name, view, None)
    app.show(name)
    return view


def test_window_region_reaches_tre(tmp_path):
    app = App()
    view = app.build_view(_file(tmp_path, BAR))
    assert view.node("bar").get("window_region") == "drag" and view.node("body").get("window_region") is None
    none = {**BAR, "children": [{**BAR["children"][0], "window_region": "none"}]}
    assert app.build_view(_file(tmp_path, none, "Other_View.yaml")).node("bar").get("window_region") == "none"


def test_a_press_on_the_bar_moves_the_window(tmp_path):
    """`tre` takes a primary press on a drag region: the pressed node gets
    `pointer_cancel`, not `pointer_up` or a click."""
    app = App()
    view = _shown(app, _file(tmp_path, BAR), "Home")
    seen = []
    for event in ("pointer_up", "pointer_cancel"):
        view.node("bar").on(event, lambda e, event=event: seen.append(event))
    app.window.advance(0)
    app.window.simulate("pointer_down", node=view.node("bar"))
    app.window.simulate("pointer_up", node=view.node("bar"))
    assert seen == ["pointer_cancel"]


def test_a_wrong_window_region_is_one_line(tmp_path):
    bad = {**BAR, "children": [{**BAR["children"][0], "window_region": "title"}]}
    with pytest.raises((SpecBuildError, ValueError), match='widget "bar": window_region is "drag" or "none", got '):
        App().build_view(_file(tmp_path, bad))


def test_reconcile_follows_window_region(tmp_path):
    view = App().build_view(_file(tmp_path, BAR))
    dropped = {**BAR, "children": [{k: v for k, v in BAR["children"][0].items() if k != "window_region"},
                                   BAR["children"][1]]}
    view.reconcile(spec=dropped)
    assert view.node("bar").get("window_region") is None  # dropped: back to tre's default
    view.reconcile(spec=BAR)
    assert view.node("bar").get("window_region") == "drag"


def test_a_component_call_can_be_the_title_bar(tmp_path):
    spec = {"id": "root", "kind": "Container", "style": {"width": 400, "height": 300},
            "children": [{"id": "top", "component": "TopAppBar", "with": {"title": "Notes", "width": 400},
                          "window_region": "drag"}]}
    view = App(theme_seed=SEED).build_view(_file(tmp_path, spec))  # TopAppBar's colours are theme roles
    assert view.node("top").get("window_region") == "drag"


# -- the window.* handlers ----------------------------------------------------------

def _button(action):
    return {"id": "root", "kind": "Container", "style": {"width": 400, "height": 300},
            "children": [{"id": "button", "kind": "Rect", "handlers": {"on_click": f"window.{action}"},
                          "style": {"width": 40, "height": 40, "background": "#6750A4"}}]}


def test_the_handlers_call_the_apps_actions(tmp_path, monkeypatch):
    app = App()
    view = _shown(app, _file(tmp_path, _button("toggle_maximized")), "Home")
    ViewModel(view)  # handlers are wired with the ViewModel; this one has no method for them
    app.window.simulate("click", node=view.node("button"))
    assert app.maximized.get() is True  # before run(): how the window opens
    app.window.simulate("click", node=view.node("button"))
    assert app.maximized.get() is False
    called = []
    for action in ("minimize", "maximize", "restore", "close"):
        monkeypatch.setattr(app, action, lambda action=action: called.append(action))
        other = _shown(app, _file(tmp_path, _button(action), f"{action.title()}_View.yaml"), action)
        ViewModel(other)
        app.window.simulate("click", node=other.node("button"))
    assert called == ["minimize", "maximize", "restore", "close"]


def test_an_unknown_window_action_is_one_line(tmp_path):
    view = App().build_view(_file(tmp_path, _button("fullscreen")))
    with pytest.raises(ValueError, match='widget "button": handler "on_click" names "window.fullscreen", which '
                                         "isn't a window action \\(window.minimize, "):
        ViewModel(view)


def test_a_window_action_needs_an_apps_window():
    view = View(_button("close"))  # a window of its own, no App
    with pytest.raises(ValueError, match="but this view isn't on an App's window"):
        ViewModel(view)


def test_a_control_takes_window_region_too():
    """A control (here a Switch) is built by Tesserae, not from a `tre`
    primitive, so its node is set, and patched, separately."""
    spec = {"id": "root", "kind": "Container", "style": {"width": 300, "height": 100},
            "children": [{"id": "s", "kind": "Switch", "style": {}, "window_region": "none"}]}
    view = View(spec, theme_seed=SEED)
    assert view._built.controls["s"].node.get("window_region") == "none"
    view.reconcile({**spec, "children": [{"id": "s", "kind": "Switch", "style": {}}]})
    assert view._built.controls["s"].node.get("window_region") is None
