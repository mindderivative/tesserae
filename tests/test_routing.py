"""M66 (#12): routing. `navigate(name, **params)` pushes a history entry
and hands the params to the screen's ViewModel (`on_navigated`); `back`
and `forward` move through the history; `show` stays a jump that
replaces the current entry. Routes (`route`, `navigate_to`, `location`)
map strings to screens and params; the shell's rail navigates; Alt+Left
and Alt+Right go back and forward.
"""

import pytest

from tesserae import App, Signal, View, ViewModel


def _screen(label="screen"):
    return {"id": "root", "kind": "Container", "style": {"width": 200, "height": 60},
            "children": [{"id": "label", "kind": "Text", "text": {"content": label, "font_family": "Roboto", "font_size": 14},
                          "style": {"foreground": "#000000", "width": 180, "height": 20}}]}


class Recorder(ViewModel):
    def __init__(self, view, log):
        self.log = log
        super().__init__(view)

    def on_navigated(self, params):
        self.log.append((self._view.node("label").get("text"), params))


def _app(*names, hooks=True):
    app = App(width=300, height=200)
    log = []
    for name in names:
        view = View(_screen(name), window=app.window)
        vm = Recorder(view, log) if hooks else ViewModel(view)
        app.register(name, view, vm)
    return app, log


def _state(app):
    return [n for n, _ in app._history], app._at, app.can_go_back.get(), app.can_go_forward.get()


def test_navigate_pushes_and_back_and_forward_move():
    app, log = _app("Home", "Notes", "Note")
    app.show("Home")
    app.navigate("Notes")
    app.navigate("Note", id=42)
    assert app.current == "Note" and _state(app) == (["Home", "Notes", "Note"], 2, True, False)
    assert log == [("Notes", {}), ("Note", {"id": 42})]
    assert app.back() is True and app.current == "Notes" and log[-1] == ("Notes", {})
    assert app.back() is True and app.current == "Home" and _state(app) == (["Home", "Notes", "Note"], 0, False, True)
    assert app.back() is False and app.current == "Home"  # nothing before
    assert app.forward() is True and app.forward() is True and log[-1] == ("Note", {"id": 42})  # its params again
    assert app.forward() is False and app.current == "Note"


def test_navigating_after_back_drops_the_forward_entries():
    app, _ = _app("Home", "Notes", "Settings")
    app.show("Home")
    app.navigate("Notes")
    app.back()
    app.navigate("Settings")
    assert _state(app) == (["Home", "Settings"], 1, True, False)


def test_the_entry_already_showing_is_not_pushed_again():
    app, log = _app("Home", "Note")
    app.show("Home")
    app.navigate("Note", id=1)
    app.navigate("Note", id=1)
    assert len(app._history) == 2 and log == [("Note", {"id": 1})]
    app.navigate("Note", id=2)  # other params: a new entry
    assert len(app._history) == 3


def test_show_is_a_jump_that_replaces_the_current_entry():
    app, log = _app("Home", "Notes", "Settings")
    app.show("Home")
    assert _state(app) == (["Home"], 0, False, False)
    app.navigate("Notes", tag="work")
    app.show("Settings")  # no hook, no push
    assert log == [("Notes", {"tag": "work"})] and _state(app) == (["Home", "Settings"], 1, True, False)
    app.back()
    assert app.current == "Home"


def test_navigate_works_before_any_show():
    app, _ = _app("Home", "Notes")
    app.navigate("Home")
    assert _state(app) == (["Home"], 0, False, False) and app.current == "Home"


def test_a_screen_without_a_hook_is_just_shown():
    app, _ = _app("Home", "Notes", hooks=False)
    app.navigate("Home")
    app.navigate("Notes", id=3)
    assert app.current == "Notes" and app.back() and app.current == "Home"


def test_the_hook_gets_a_copy_and_runs_before_the_screen_shows():
    app, _ = _app("Home")
    seen = []

    class Editor(ViewModel):
        def on_navigated(self, params):
            seen.append(app.current)  # still the old screen
            params["id"] = "changed"

    view = View(_screen("Editor"), window=app.window)
    app.register("Editor", view, Editor(view))
    app.show("Home")
    app.navigate("Editor", id=7)
    assert seen == ["Home"] and app._history[1] == ("Editor", {"id": 7})


def test_a_failing_hook_leaves_the_history_and_screen_as_they_were():
    app, _ = _app("Home")

    class Broken(ViewModel):
        def on_navigated(self, params):
            raise RuntimeError("no such note")

    view = View(_screen("Broken"), window=app.window)
    app.register("Broken", view, Broken(view))
    app.show("Home")
    with pytest.raises(RuntimeError, match="no such note"):
        app.navigate("Broken", id=1)
    assert app.current == "Home" and _state(app) == (["Home"], 0, False, False)


def test_a_hook_failing_on_back_leaves_the_history_where_it_was():
    app, _ = _app("Notes")
    fail = []

    class Flaky(ViewModel):
        def on_navigated(self, params):
            if fail:
                raise RuntimeError("gone")

    view = View(_screen("Flaky"), window=app.window)
    app.register("Flaky", view, Flaky(view))
    app.navigate("Flaky")
    app.navigate("Notes")
    fail.append(True)
    with pytest.raises(RuntimeError, match="gone"):
        app.back()
    assert app.current == "Notes" and _state(app) == (["Flaky", "Notes"], 1, True, False)


def test_an_unknown_screen_is_named():
    app, _ = _app("Home")
    with pytest.raises(KeyError, match="no view registered under 'Nope'"):
        app.navigate("Nope")
    with pytest.raises(KeyError, match="no view registered under 'Nope'"):
        app.show("Nope")


def test_can_go_back_and_forward_are_signals_to_follow():
    from tesserae import Effect

    app, _ = _app("Home", "Notes")
    seen = []
    Effect(lambda: seen.append((app.can_go_back.get(), app.can_go_forward.get())))
    app.show("Home")
    app.navigate("Notes")
    app.back()
    assert seen == [(False, False), (True, False), (False, True)]
