"""M66 (#12): routing. `navigate(name, **params)` pushes a history entry
and hands the params to the screen's ViewModel (`on_navigated`); `back`
and `forward` move through the history; `show` stays a jump that
replaces the current entry. Routes (`route`, `navigate_to`, `location`)
map strings to screens and params; Alt+Left
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


# -- routes ------------------------------------------------------------------------------

def _routed():
    app, log = _app("Home", "Notes", "Note", "Tagged")
    app.route("", "Home")
    app.route("notes", "Notes")
    app.route("notes/{id:int}", "Note")
    app.route("notes/tag/{tag}", "Tagged")
    return app, log


def test_a_route_navigates_with_its_params():
    app, log = _routed()
    app.navigate_to("notes/42")
    assert app.current == "Note" and log[-1] == ("Note", {"id": 42}) and app.location == "notes/42"
    app.navigate_to("/notes/tag/work/")  # slashes at the ends don't matter
    assert log[-1] == ("Tagged", {"tag": "work"}) and app.location == "notes/tag/work"
    app.navigate_to("")
    assert app.current == "Home" and app.location == ""
    app.navigate("Notes")  # {} would read back from "" too, but that route is Home's
    assert app.location == "notes"
    app.back()
    assert app.back() and app.location == "notes/tag/work"  # a route's entry is an ordinary step


@pytest.mark.parametrize("route", ["notes/abc", "notes/42/more", "people", "notes/tag"])
def test_an_unmatched_route_is_named(route):
    app, _ = _routed()
    with pytest.raises(KeyError, match="no route matches"):
        app.navigate_to(route)


def test_an_int_segment_takes_negative_numbers_and_routes_are_tried_in_order():
    app, log = _app("Note", "Any")
    app.route("n/{id:int}", "Note")
    app.route("n/{name}", "Any")
    app.navigate_to("n/-3")
    assert log[-1] == ("Note", {"id": -3})
    app.navigate_to("n/three")
    assert log[-1] == ("Any", {"name": "three"})  # a param called `name`: `navigate`'s own is positional-only
    app.navigate("Any", name="four")
    assert log[-1] == ("Any", {"name": "four"})


def test_location_is_none_without_a_route_that_reads_it_back():
    app, _ = _routed()
    assert app.location is None  # nothing showing yet
    app.navigate("Note", id="x")  # not an int: "notes/x" wouldn't read back as this entry
    assert app.location is None
    app.navigate("Note", id=7, extra=1)  # a param the route doesn't carry
    assert app.location is None
    app.navigate("Note", id=7)
    assert app.location == "notes/7"


def test_location_takes_the_first_route_of_its_screen_that_fits():
    app, _ = _app("Note")
    app.route("n/{slug}", "Note")
    app.route("notes/{id:int}", "Note")
    app.navigate("Note", id=5)
    assert app.location == "notes/5"  # "n/{slug}" would read back {"slug": ...}, not this


@pytest.mark.parametrize("pattern, message", [
    ("notes/{1d}", "isn't {name} or {name:int}"), ("notes/{id:float}", "isn't {name} or {name:int}"),
    ("a/{id}/{id}", "'id' appears twice"), ("a//b", "'' isn't a segment"), ("a/x{id}", "'x{id}' isn't a segment"),
])
def test_a_bad_pattern_is_named(pattern, message):
    app, _ = _app("Home")
    with pytest.raises(ValueError, match=message.replace("{", r"\{").replace("}", r"\}")):
        app.route(pattern, "Home")


# -- the rail and the keys --------------------------------------------------------------

def _key(app, key, node=None, **mods):
    if node is not None:
        node.focus()
    app.window.simulate("key_down", key=key, **mods)


def test_alt_left_and_right_go_back_and_forward():
    app, _ = _app("Home", "Notes")
    app.show("Home")
    app.navigate("Notes")
    _key(app, "arrow_left", alt=True)
    assert app.current == "Home"
    _key(app, "arrow_right", alt=True)
    assert app.current == "Notes"
    for mods in ({}, {"alt": True, "shift": True}, {"alt": True, "ctrl": True}, {"alt": True, "meta": True}):
        _key(app, "arrow_left", **mods)  # plain, or with another modifier: not a history key
        assert app.current == "Notes"
    app.back()  # somewhere to go forward to
    _key(app, "arrow_up", alt=True)
    _key(app, "arrow_down", alt=True)
    assert app.current == "Home" and app.can_go_forward.get()  # only left and right move


def test_the_keys_work_from_a_focused_node_but_not_a_text_input():
    app = App(width=300, height=200)
    spec = {"id": "root", "kind": "Container", "style": {"width": 200, "height": 100},
            "children": [{"id": "box", "kind": "Rect", "style": {"width": 40, "height": 40, "background": "#6750A4"},
                          "handlers": {"on_click": "noop"}},
                         {"id": "field", "kind": "TextField", "text": {"content": "", "font_family": "Roboto", "font_size": 14},
                          "style": {"width": 120, "height": 32, "foreground": "#000000", "background": "#FFFFFF"}}]}

    class Form(ViewModel):
        def noop(self):
            pass

    form = View(spec, window=app.window)
    app.register("Form", form, Form(form))
    other = View(_screen("Other"), window=app.window)
    app.register("Other", other, ViewModel(other))
    app.show("Other")
    app.navigate("Form")
    _key(app, "arrow_left", node=form.node("field"), alt=True)  # Option+Left moves by word there
    assert app.current == "Form"
    _key(app, "arrow_left", node=form.node("box"), alt=True)
    assert app.current == "Other"


def test_the_mouses_side_buttons_go_back_and_forward():  # M72, on tre 0.4.1
    app, log = _app("Home", "Notes")
    app.show("Home")
    app.navigate("Notes")
    label = app._registered["Notes"].view.node("label")
    app.window.simulate("pointer_down", node=label, button="back")  # over a node
    assert app.current == "Home"
    app.window.simulate("pointer_down", x=250.0, y=150.0, button="forward")  # over nothing: the root hears it
    assert app.current == "Notes" and log[-1] == ("Notes", {})
    for button in ("primary", "secondary", "middle"):
        app.window.simulate("pointer_down", node=label, button=button)
    assert app.current == "Notes" and app.can_go_back.get()  # the other buttons don't move
    app.back()
    for button in ("primary", "secondary", "middle"):  # nor forward, with somewhere to go
        app.window.simulate("pointer_down", x=250.0, y=150.0, button=button)
    assert app.current == "Home" and app.can_go_forward.get()
    app.forward()
    app.window.simulate("pointer_up", node=label, button="back")
    assert app.current == "Notes"  # the press moves, not the release
