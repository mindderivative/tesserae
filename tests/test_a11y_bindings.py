"""M47 Phase 2: bound `a11y:` fields. A value that is a `{{ }}` binding
follows the ViewModel, as `bindings:` do (Q1); `label`, `hidden` and
`level` can be bound, `role` and `live` can't (Q2). `tre` can't report
what a screen reader says, so these read the node's properties.
"""

import re

import pytest
import yaml

import tesserae
from tesserae.spec.build import SpecBuildError
from tesserae.spec.expand import expand_components_to_spec
from tesserae.view import View

SEED = (0x67, 0x50, 0xA4, 0xFF)


class VM(tesserae.ViewModel):
    def __init__(self, view):
        self.unread = tesserae.Signal(3)
        self.summary = tesserae.Computed(lambda: f"{self.unread.get()} unread")
        self.collapsed = tesserae.Signal(False)
        self.depth = tesserae.Signal(2)
        self.title = tesserae.Signal("Inbox")
        self.number = tesserae.Signal(7)
        self.nothing = tesserae.Signal(None)
        super().__init__(view)


def _text(node_id="status", **a11y):
    return {"id": node_id, "kind": "Text", "text": {"content": "x", "font_family": "Roboto", "font_size": 14},
            "style": {"foreground": "#000000", "width": 100, "height": 20}, "a11y": a11y}


def _root(*children):
    return {"id": "root", "kind": "Container", "children": list(children)}


def _view(spec):
    view = View(spec, theme_seed=SEED)
    return view, VM(view)


def test_bound_label_hidden_and_level_follow_the_viewmodel():
    view, vm = _view(_root(_text(label="{{ summary.get() }}", hidden="{{ collapsed.get() }}",
                                 level="{{ depth.get() }}", live="polite")))
    node = view.node("status")
    assert (node.get("label"), node.get("a11y_hidden"), node.get("level"), node.get("live")) == (
        "3 unread", False, 2, "polite")
    vm.unread.set(4)
    vm.collapsed.set(True)
    vm.depth.set(3)
    assert (node.get("label"), node.get("a11y_hidden"), node.get("level")) == ("4 unread", True, 3)


def test_fixed_fields_still_work_beside_bound_ones():
    view, vm = _view(_root(_text(label="{{ title.get() }}", role="heading", level=1)))
    node = view.node("status")
    assert (node.get("label"), node.get("role"), node.get("level")) == ("Inbox", "heading", 1)


def test_a_bound_value_survives_a_re_theme_a_re_style_and_a_reconcile():
    spec = _root(_text(label="{{ summary.get() }}", hidden="{{ collapsed.get() }}"))
    view, vm = _view(spec)
    node = view.node("status")
    vm.unread.set(9)
    vm.collapsed.set(True)
    view.set_theme(theme_seed=(0x00, 0x66, 0x88, 0xFF))
    assert (node.get("label"), node.get("a11y_hidden")) == ("9 unread", True)
    view.set_stylesheet({"styles": [{"kind": "Text", "style": {"opacity": 0.5}}]})
    assert (node.get("label"), node.get("a11y_hidden")) == ("9 unread", True)
    restyled = _root(_text(label="{{ summary.get() }}", hidden="{{ collapsed.get() }}"))
    restyled["children"][0]["style"]["width"] = 120  # a real patch
    view.reconcile(restyled)
    assert view.node("status") == node and (node.get("label"), node.get("a11y_hidden")) == ("9 unread", True)
    vm.unread.set(1)
    assert node.get("label") == "1 unread"  # still wired


def test_a_reconcile_can_turn_a_binding_into_a_fixed_value_and_back():
    view, vm = _view(_root(_text(label="{{ title.get() }}")))
    node = view.node("status")
    view.reconcile(_root(_text(label="Fixed")))
    vm.title.set("Changed")
    assert node.get("label") == "Fixed"  # no longer bound
    view.reconcile(_root(_text(label="{{ title.get() }}")))
    assert node.get("label") == "Changed"


def test_none_clears_a_bound_label_or_level():
    view, vm = _view(_root(_text(label="{{ nothing.get() }}", level="{{ nothing.get() }}")))
    assert view.node("status").get("label") is None and view.node("status").get("level") is None


@pytest.mark.parametrize("field, raw, message", [
    ("label", "{{ number.get() }}", 'a11y binding on "label" ("{{ number.get() }}"): a11y label must be a string, got 7'),
    ("hidden", "{{ title.get() }}", "a11y hidden must be true or false, got 'Inbox'"),
    ("level", "{{ collapsed.get() }}", "a11y level must be a positive whole number, got False"),
    ("label", "{{ unread }}", "a11y label must be a string, got 3"),  # a Signal reads as its value since 0.5.0
    ("label", "{{ missing.get() }}", 'widget "status" a11y binding on "label"'),
])
def test_a_bad_bound_value_is_an_error_naming_the_widget_and_field(field, raw, message):
    view = View(_root(_text(**{field: raw})), theme_seed=SEED)
    with pytest.raises(ValueError, match=re.escape(message)):
        VM(view)


@pytest.mark.parametrize("field", ["role", "live"])
def test_role_and_live_cant_be_bound(field):
    with pytest.raises(SpecBuildError, match=f"a11y {field} can't be bound -- only label, hidden, level"):
        View(_root(_text(**{field: "{{ title.get() }}"})), theme_seed=SEED)


def test_text_mixed_with_a_binding_is_an_error():
    view = View(_root(_text(label="{{ unread.get() }} unread")), theme_seed=SEED)
    with pytest.raises(ValueError, match=re.escape("is not wrapped in {{ ... }}")):
        VM(view)


def test_a_text_field_carries_its_bound_label_on_its_input():
    field = {"id": "f", "kind": "TextField", "text": {"content": "", "font_family": "Roboto", "font_size": 14},
             "style": {"width": 200, "height": 40, "background": "surface"}, "a11y": {"label": "{{ title.get() }}"}}
    view, vm = _view(_root(field))
    assert view.node("f").get("label") == "Inbox" and view.node("f").get("role") == "textbox"
    vm.title.set("Search mail")
    assert view.node("f").get("label") == "Search mail"


def _link(**extra):
    return {"id": "go", "kind": "Link", "text": {"content": "Open", "font_family": "Roboto", "font_size": 14},
            "style": {"foreground": "#000000"}, **extra}


def test_a_links_bound_label_wins_over_its_bound_text():
    view, vm = _view(_root(_link(bindings={"text": "{{ title.get() }}"}, a11y={"label": "{{ summary.get() }}"})))
    box = view.node("go")
    assert box.get("label") == "3 unread"
    vm.title.set("Elsewhere")  # the text changes; the name doesn't
    assert box.get("label") == "3 unread"
    vm.unread.set(5)
    assert box.get("label") == "5 unread"


def test_a_links_fixed_label_wins_over_its_bound_text_and_without_one_the_text_names_it():
    view, vm = _view(_root(_link(bindings={"text": "{{ title.get() }}"}, a11y={"label": "Go to inbox"})))
    vm.title.set("Elsewhere")
    assert view.node("go").get("label") == "Go to inbox"  # before M47 the text binding overwrote it
    view, vm = _view(_root(_link(bindings={"text": "{{ title.get() }}"})))
    vm.title.set("Elsewhere")
    assert view.node("go").get("label") == "Elsewhere"


def _checkbox(**a11y):
    return {"id": "cb", "kind": "Checkbox", "checked": False,
            "style": {"width": 18, "height": 18, "background": "#6750A4"}, "a11y": a11y}


def test_a_controls_a11y_fields_reach_it_fixed_or_bound():
    """Before M47 a control's `a11y:` was checked and then dropped."""
    view, vm = _view(_root(_checkbox(label="Agree to the terms")))
    node = view.node("cb")
    assert (node.get("label"), node.get("role")) == ("Agree to the terms", "checkbox")
    view.set_theme(theme_seed=(0x00, 0x66, 0x88, 0xFF))
    assert node.get("label") == "Agree to the terms"
    view.reconcile(_root(_checkbox(label="Accept")))  # a patch
    assert view.node("cb") == node and node.get("label") == "Accept"
    view, vm = _view(_root(_checkbox(label="{{ title.get() }}")))
    vm.title.set("Agree")
    assert view.node("cb").get("label") == "Agree" and view.node("cb").get("role") == "checkbox"


def test_a_binding_passes_through_a_fragment_while_its_params_substitute(tmp_path):
    (tmp_path / "Status_Component.yaml").write_text(yaml.safe_dump({
        "params": ["size"],
        "id": "root", "kind": "Text", "text": {"content": "x", "font_family": "Roboto", "font_size": "{{ size }}"},
        "style": {"foreground": "#000000", "width": 100, "height": 20},
        "a11y": {"label": "{{ summary.get() }}", "live": "polite"},
    }))
    text = yaml.safe_dump({"id": "root", "kind": "Container",
                           "children": [{"id": "s", "component": "Status", "with": {"size": 14}}]})
    spec = expand_components_to_spec(text, component_dirs=[tmp_path])
    view, vm = _view(spec)
    vm.unread.set(2)
    assert view.node("s").get("label") == "2 unread" and view.node("s").get("font_size") == 14.0


# -- Phase 3: tesserae.a11y.bind, for widgets made in Python ------------------

import tre  # noqa: E402

from tesserae import Computed, Signal, a11y  # noqa: E402
from tesserae.widgets import button, checkbox  # noqa: E402


def _window():
    return tre.Window(width=300, height=200)


def test_bind_follows_a_signal_a_computed_and_a_function():
    count, collapsed = Signal(3), Signal(False)
    b = button(_window(), "Inbox", 120, 40)
    a11y.bind(b, label=Computed(lambda: f"{count.get()} unread"), hidden=collapsed,
              level=lambda: 1 + count.get() // 10)
    node = b.node
    assert (node.get("label"), node.get("a11y_hidden"), node.get("level")) == ("3 unread", False, 1)
    count.set(12)
    collapsed.set(True)
    assert (node.get("label"), node.get("a11y_hidden"), node.get("level")) == ("12 unread", True, 2)


def test_bind_takes_a_node_or_a_plain_value_and_stops():
    node = _window().create("box", width=10, height=10)
    title = Signal("One")
    stop = a11y.bind(node, label=title, level=2)
    assert (node.get("label"), node.get("level")) == ("One", 2)
    stop()
    title.set("Two")
    assert node.get("label") == "One"


def test_a_controls_bound_label_survives_its_own_repaints_and_a_re_theme():
    from tesserae import Theme

    cb = checkbox(_window(), (0x67, 0x50, 0xA4, 0xFF), 18, 18, checked=False)
    terms = Signal("Agree to the terms")
    a11y.bind(cb, label=terms)
    cb.checked.set(True)  # the control repaints
    cb.set_theme(Theme.resolve(theme_seed=(0x00, 0x66, 0x88, 0xFF)))
    assert cb.node.get("label") == "Agree to the terms" and cb.node.get("role") == "checkbox"
    terms.set("Accept")
    assert cb.node.get("label") == "Accept"


@pytest.mark.parametrize("fields, message", [
    ({"role": Signal("button")}, "'role' can't be bound -- only label, hidden, level"),
    ({"live": "polite"}, "'live' can't be bound"),
    ({"label": Signal(5)}, "a11y.bind: a11y label must be a string, got 5"),
    ({"level": lambda: 0}, "a11y level must be a positive whole number, got 0"),
])
def test_bind_rejects_what_it_cant_set(fields, message):
    with pytest.raises(ValueError, match=re.escape(message)):
        a11y.bind(_window().create("box"), **fields)


def test_a_failed_bind_undoes_the_fields_it_had_set_up():
    node = _window().create("box")
    title = Signal("One")
    with pytest.raises(ValueError):
        a11y.bind(node, label=title, hidden=Signal("not a bool"))
    title.set("Two")
    assert node.get("label") == "One"  # the label's effect was disposed


def test_a_bad_value_later_raises_naming_the_field():
    node = _window().create("box")
    level = Signal(1)
    a11y.bind(node, level=level)
    with pytest.raises(ValueError, match="a11y level must be a positive whole number, got -1"):
        level.set(-1)
