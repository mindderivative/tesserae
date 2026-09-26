"""M37 Phase 4: Tesserae's `View` (`tesserae.view`) -- built by
Tesserae's compiler, reconciled in place, with bindings, handlers and
`two_way:` wired by Tesserae.

Where `tre`'s `View` does the same thing, its behaviour and messages are
the reference (compared directly while 0.3.4 still has it). Two
deliberate differences: `on_change` fires only for the user's own edits
(`tre` issue #12), and a reconcile puts children in the new spec's order.
"""

import pytest
import tre

import tesserae
from tesserae.spec import ViewWatcher
from tesserae.view import View

SEED = (0x67, 0x50, 0xA4, 0xFF)


def _text(node_id="label", binding="{{ title.get() }}", **extra):
    node = {"id": node_id, "kind": "Text", "text": {"content": "placeholder", "font_family": "Roboto", "font_size": 14},
            "style": {"foreground": "#000000", "width": 100, "height": 20}}
    if binding is not None:
        node["bindings"] = {"text": binding}
    node.update(extra)
    return node


def _root(*children, **style):
    return {"id": "root", "kind": "Container", "style": {"flex_direction": "vertical", **style}, "children": list(children)}


def _rect(node_id, **extra):
    return {"id": node_id, "kind": "Rect", "style": {"width": 40, "height": 20, "background": "#112233"}, **extra}


class VM(tesserae.ViewModel):
    def __init__(self, view, **signals):
        self.title = tesserae.Signal("Hello")
        self.agreed = tesserae.Signal(True)
        self.name = tesserae.Signal("bob")
        self.width = tesserae.Signal(50)
        self.color = tesserae.Signal("#FF0000")
        self.flag = tesserae.Signal(True)
        self.other = tesserae.Signal("other")
        self.clicks, self.events, self.changes, self.not_callable = 0, [], 0, 5
        for key, value in signals.items():
            setattr(self, key, value)
        super().__init__(view)

    def bump(self):
        self.clicks += 1

    def with_event(self, event):
        self.events.append(event)

    def changed(self):
        self.changes += 1


def _view(spec, **kwargs):
    return View(spec, theme_seed=SEED, **kwargs)


# -- building and lookup -------------------------------------------------------


def test_a_view_builds_into_its_own_window_and_finds_nodes():
    view = _view(_root(_rect("a"), _text(binding=None)))
    view.window.advance(16)
    assert view.node("a").get("layout_width") == 40.0
    assert view.root.parent() is not None  # mounted in its own window
    with pytest.raises(ValueError, match="no widget with id 'nope'"):
        view.node("nope")


def test_a_view_can_build_into_a_given_window_unmounted():
    window = tre.Window(width=200, height=100)
    view = View(_root(_rect("a")), window=window, theme_seed=SEED)
    assert view.window is window and view.root.parent() is None


# -- bindings --------------------------------------------------------------------


def test_bindings_apply_and_follow_their_signals():
    spec = _root(_text(), _rect("box", bindings={"width": "{{ width.get() }}", "background": "{{ color.get() }}"}))
    view = _view(spec)
    vm = VM(view)
    assert view.node("label").get("text") == "Hello"
    assert (view.node("box").get("width"), view.node("box").get("fill")) == (50.0, (255, 0, 0, 255))
    vm.title.set("Bye")
    vm.width.set(80)
    vm.color.set("#00FF00")
    assert view.node("label").get("text") == "Bye"
    assert (view.node("box").get("width"), view.node("box").get("fill")) == (80.0, (0, 255, 0, 255))


def test_a_binding_can_read_a_computed():
    class CVM(tesserae.ViewModel):
        def __init__(self, view):
            self.n = tesserae.Signal(2)
            self.total = tesserae.Computed(lambda: f"total {self.n.get() * 10}")
            super().__init__(view)

    view = _view(_root(_text(binding="{{ total.get() }}")))
    vm = CVM(view)
    vm.n.set(3)
    assert view.node("label").get("text") == "total 30"


def test_dependencies_are_retracked_on_each_evaluation():
    view = _view(_root(_text(binding='{{ flag.get() and title.get() or other.get() }}')))
    vm = VM(view)
    assert view.node("label").get("text") == "Hello"
    vm.flag.set(False)
    assert view.node("label").get("text") == "other"
    vm.title.set("ignored now")
    assert view.node("label").get("text") == "other"
    vm.other.set("tracked")
    assert view.node("label").get("text") == "tracked"


BAD_BINDINGS = {
    "doesn't parse": "{{ -1 }}",
    "unknown attribute": "{{ missing.get() }}",
    "not a string for text": "{{ width.get() }}",
}


@pytest.mark.parametrize("name", sorted(BAD_BINDINGS))
def test_binding_errors_read_as_tres_do(name):
    spec = _root(_text(binding=BAD_BINDINGS[name]))
    with pytest.raises(ValueError) as theirs:
        VM(tre.View(spec=spec, theme_seed=SEED))
    with pytest.raises(ValueError) as ours:
        VM(_view(spec))
    assert str(ours.value) == str(theirs.value)


# -- handlers --------------------------------------------------------------------


def test_handlers_are_wired_with_or_without_the_event():
    spec = _root(_rect("a", handlers={"on_click": "bump"}), _rect("b", handlers={"on_click": "with_event"}))
    view = _view(spec)
    vm = VM(view)
    view.window.advance(16)
    view.window.simulate("click", node=view.node("a"))
    view.window.simulate("click", node=view.node("b"))
    assert vm.clicks == 1 and len(vm.events) == 1 and vm.events[0] is not None


@pytest.mark.parametrize("method", ["missing_method", "not_callable"])
def test_handler_errors_read_as_tres_do(method):
    spec = _root(_rect("a", handlers={"on_click": method}))
    with pytest.raises(ValueError) as theirs:
        VM(tre.View(spec=spec, theme_seed=SEED))
    with pytest.raises(ValueError) as ours:
        VM(_view(spec))
    assert str(ours.value) == str(theirs.value)


def test_an_unknown_handler_name_is_validated_but_not_wired():
    view = _view(_root(_rect("a", handlers={"on_long_press": "bump"})))
    VM(view)  # no error: `bump` exists
    with pytest.raises(ValueError, match='names "nope"'):
        VM(_view(_root(_rect("a", handlers={"on_long_press": "nope"}))))


# -- on_change and two_way ----------------------------------------------------------

FIELD = {"id": "name", "kind": "TextField", "text": {"content": "", "font_family": "Roboto", "font_size": 14},
         "style": {"width": 100, "height": 30, "background": "surface"},
         "bindings": {"text": "{{ name.get() }}"}, "two_way": "text", "handlers": {"on_change": "changed"}}
CHECK = {"id": "cb", "kind": "Checkbox", "checked": False, "style": {"width": 18, "height": 18, "background": "primary"},
         "bindings": {"checked": "{{ agreed.get() }}"}, "two_way": "checked", "handlers": {"on_change": "changed"}}


def test_typing_writes_back_and_on_change_runs_only_for_user_edits():
    view = _view(_root(FIELD))
    vm = VM(view)
    view.window.advance(16)
    assert vm.changes == 0 and view.node("name").get("text") == "bob"
    vm.name.set("from code")  # a programmatic update: no on_change (tre issue #12)
    assert view.node("name").get("text") == "from code" and vm.changes == 0
    view.node("name").focus()
    view.window.simulate("key_down", key="x")
    assert vm.name.get() == "from codex" and vm.changes == 1


def test_a_checkbox_two_way_and_on_change_only_for_its_own_changes():
    view = _view(_root(CHECK))
    vm = VM(view)
    control = view.control("cb")
    assert control.checked.get() is True and vm.changes == 0  # the binding's initial True
    vm.agreed.set(False)
    assert control.checked.get() is False and view.node("cb").get("checked") is False and vm.changes == 0
    view.window.simulate("click", node=view.node("cb"))  # the user ticks it (M40: it ticks itself)
    assert vm.agreed.get() is True and vm.changes == 1
    view.window.simulate("key_down", key="space")
    view.window.simulate("key_up", key="space")
    assert vm.agreed.get() is False and vm.changes == 2


def test_controls_expose_their_signals_and_bind_disabled():
    spec = _root(dict(CHECK, bindings={"checked": "{{ agreed.get() }}", "disabled": "{{ agreed.get() }}"}))
    view = _view(spec)
    vm = VM(view)
    assert view.control("cb").disabled.get() is True and view.node("cb").get("focusable") is False
    vm.agreed.set(False)
    assert view.control("cb").disabled.get() is False and view.node("cb").get("focusable") is True
    with pytest.raises(ValueError, match="isn't a control kind"):
        view.control("root")


def test_two_way_needs_a_plain_signal_get():
    bad = dict(FIELD, bindings={"text": "{{ name.get() + '!' }}"})
    with pytest.raises(ValueError) as theirs:
        VM(tre.View(spec=_root(bad), theme_seed=SEED))
    with pytest.raises(ValueError) as ours:
        VM(_view(_root(bad)))
    assert str(ours.value) == str(theirs.value)


# -- reconcile --------------------------------------------------------------------------


def test_reconcile_patches_in_place_and_keeps_bound_values():
    spec = _root(_text(), _rect("a"))
    view = _view(spec)
    vm = VM(view)
    label, a = view.node("label"), view.node("a")
    changed = _root(dict(_text(), style={"foreground": "#000000", "width": 100, "height": 30}), _rect("a"))
    view.reconcile(changed)
    assert view.node("label") == label and view.node("a") == a  # the same nodes
    assert view.node("label").get("height") == 30.0
    assert view.node("label").get("text") == "Hello"  # bound value, not the placeholder
    vm.title.set("still live")
    assert view.node("label").get("text") == "still live"


def test_reconcile_adds_removes_and_orders_children_as_the_new_spec_does():
    view = _view(_root(_rect("a"), _rect("b"), _rect("c")))
    a, c = view.node("a"), view.node("c")
    view.reconcile(_root(_rect("c"), _rect("d"), _rect("a")))
    assert view.node("a") == a and view.node("c") == c
    assert list(view.root.children()) == [view.node("c"), view.node("d"), view.node("a")]
    with pytest.raises(ValueError):
        view.node("b")


def test_reconcile_rebuilds_a_node_whose_kind_changed_and_a_new_root():
    view = _view(_root(_rect("a")))
    a = view.node("a")
    view.reconcile(_root({"id": "a", "kind": "Container", "style": {"width": 10, "height": 10}}))
    assert view.node("a") != a
    old_root = view.root
    view.reconcile({"id": "other_root", "kind": "Container", "children": [_rect("z")]})
    assert view.root != old_root and view.root.parent() is not None


def test_a_removed_nodes_bindings_are_unsubscribed():
    view = _view(_root(_text(), _rect("a")))
    vm = VM(view)
    assert len(vm.title._subscribers) == 1
    view.reconcile(_root(_rect("a")))
    assert vm.title._subscribers == []
    vm.title.set("no error: nothing listens")


def test_rewiring_doesnt_double_handlers():
    view = _view(_root(_rect("a", handlers={"on_click": "bump"})))
    vm = VM(view)
    for _ in range(3):
        view.reconcile(_root(_rect("a", handlers={"on_click": "bump"})))
    view.window.advance(16)
    view.window.simulate("click", node=view.node("a"))
    assert vm.clicks == 1


# -- theme and stylesheet -----------------------------------------------------------------


def test_set_stylesheet_and_set_theme_restyle_in_place_and_keep_state():
    view = _view(_root(_text(), _rect("a", style={"width": 40, "height": 20, "background": "primary"}), CHECK))
    vm = VM(view)
    a = view.node("a")
    view.set_stylesheet({"styles": [{"kind": "Rect", "style": {"corner_radius": 7}}]})
    assert view.node("a") == a and a.get("corner_radius") == 7.0
    view.set_theme(theme_seed=(0xB3, 0x26, 0x1E, 0xFF))
    from tesserae import tokens

    assert a.get("fill") == tokens.color_scheme((0xB3, 0x26, 0x1E, 0xFF))["primary"]
    assert a.get("corner_radius") == 7.0  # the stylesheet stays
    assert view.node("label").get("text") == "Hello" and view.control("cb").checked.get() is True
    assert vm.changes == 0 and vm.agreed.get() is True


# -- hot reload ---------------------------------------------------------------------------


def test_view_watcher_reloads_a_tesserae_view(tmp_path):
    import os

    from tesserae.spec.load import build_view_spec

    path = tmp_path / "Home_View.yaml"
    path.write_text("id: root\nkind: Container\nchildren:\n"
                    "  - {id: label, kind: Text, text: {content: Hi, font_family: Roboto, font_size: 14},"
                    ' style: {foreground: "#000000", width: 50, height: 20}}\n')
    spec, frames, _ = build_view_spec(path)
    view = _view(spec)
    label = view.node("label")
    watcher = ViewWatcher(view, path)
    before = path.stat().st_mtime_ns
    path.write_text(path.read_text().replace("content: Hi", "content: Bye"))
    os.utime(path, ns=(before + 10**9, before + 10**9))
    assert watcher.poll() is True
    assert view.node("label") == label and label.get("text") == "Bye"


def test_reconcile_keeps_focus_on_an_unchanged_field():
    view = _view(_root(FIELD, _rect("a")))
    VM(view)
    view.window.advance(16)
    view.node("name").focus()
    view.reconcile(_root(FIELD, _rect("a", style={"width": 60, "height": 20, "background": "#112233"})))
    assert view.node("name").get("focused") is True
    assert view.node("a").get("width") == 60.0
