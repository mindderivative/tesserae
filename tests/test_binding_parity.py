"""M36 Phase 1: Tesserae's binding evaluator (`tesserae.binding`) gives
exactly `tre`'s result or error for every expression.

`tre` has no Python entry point to its evaluator, so each expression is
evaluated by `tre` through a real `View`: a Text node bound to it. `tre`
reports a string result as the node's text, and anything else in its
error ("expects a string binding, got Int(3)"), which is the same form
`tesserae.binding.value_debug` prints. An evaluation error is compared by
its message.
"""

import re
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

import pytest
import tre

import tesserae
from tesserae.binding import BindingError, evaluate_value, parse_binding, value_debug

ROOT = Path(__file__).resolve().parent.parent


class Point:
    def __init__(self):
        self.x = 3
        self.label = "p"

    def norm(self):
        return 5.0

    def boom(self):
        raise KeyError("nope")


class Money:
    """A handle with its own operators."""

    def __init__(self, cents):
        self.cents = cents

    def __add__(self, other):
        return Money(self.cents + (other.cents if isinstance(other, Money) else int(other * 100)))

    def __eq__(self, other):
        return isinstance(other, Money) and other.cents == self.cents

    def __lt__(self, other):
        return self.cents < other.cents

    def __bool__(self):
        return self.cents != 0

    def __str__(self):
        return f"${self.cents / 100:.2f}"


ATTRS = {
    "n": 3, "m": -4, "z": 0, "f": 2.5, "g": 0.0, "s": "ab", "empty": "", "yes": True, "no": False,
    "nothing": None, "items": [10, 20, 30], "names": ["a", "b"], "table": {"k": "v", 1: "one"},
    "big": 2**70, "huge": 10**400, "dec": Decimal("1.5"), "frac": Fraction(1, 4),
    "pt": Point(), "cash": Money(250), "broke": Money(0),
}


def _vm_class():
    class VM(tesserae.ViewModel):
        def __init__(self, view):
            for key, value in ATTRS.items():
                setattr(self, key, value)
            self.count = tesserae.Signal(7)
            self.title = tesserae.Signal("Hello")
            self.total = tesserae.Computed(lambda: self.count.get() * 2)
            super().__init__(view)

    return VM


def _tre(expr: str):
    raw = "{{ " + expr + " }}"
    spec = {"id": "root", "kind": "Container", "children": [{
        "id": "t", "kind": "Text", "text": {"content": "", "font_family": "Roboto", "font_size": 14},
        "style": {"width": 10, "height": 10, "foreground": "#000000"}, "bindings": {"text": raw}}]}
    view = tre.View(spec=spec)
    try:
        _vm_class()(view)
    except ValueError as exc:
        message = str(exc)
        got = re.fullmatch(r'widget property "text" expects a string binding, got (.*)', message)
        if got:
            return ("value", got.group(1))
        prefix = f'widget "t" binding on "text" ({raw!r}): '.replace("'", '"')
        assert message.startswith('widget "t" binding on "text" ('), message
        return ("error", message.split('"): ', 1)[1] if '"): ' in message else message)
    return ("value", f'Str({_rust_str(view.node("t").get_text())})')


def _rust_str(s):
    from tesserae.binding import _str_debug
    return _str_debug(s)[1:-1].join('""')


def _tesserae(expr: str):
    raw = "{{ " + expr + " }}"

    class VM:  # same class name as tre's side, since errors name it
        pass

    vm = VM()
    for key, value in ATTRS.items():
        setattr(vm, key, value)
    vm.count = tesserae.Signal(7)
    vm.title = tesserae.Signal("Hello")
    vm.total = tesserae.Computed(lambda: vm.count.get() * 2)
    try:
        return ("value", value_debug(evaluate_value(parse_binding(raw), vm)))
    except BindingError as exc:
        return ("error", str(exc))


DESIGNED = [
    # names, attributes, indexing, calls
    "n", "s", "f", "yes", "nothing", "items", "missing", "pt.x", "pt.label", "pt.missing",
    "items[0]", "items[2]", "items[5]", "table[\"k\"]", "table[1]", "table[\"none\"]", "names[0] + names[1]",
    "pt.norm()", "pt.boom()", "s.upper()", "s.missing()", "count.get()", "title.get()", "total.get()",
    "count.get() + 1", "title.get() + \"!\"", "count", "items[n - 2]",
    # literals
    "1", "1.5", "0.1", "\"x\"", "'y'", "True", "False", "12345678901234567890", "1.2.3", "007",
    # arithmetic, primitive rules
    "1 + 2", "n + m", "1 + 2.5", "2.5 + 1", "f + f", "s + s", "s + 1", "1 - 2", "f - 1", "1 - f",
    "2 * 3", "f * 2", "s * 2", "7 / 2", "n / z", "f / g", "g / g", "-f", "1 / 2 * 4",
    "9223372036854775807 + 1", "n * 9223372036854775807",
    # comparison
    "1 == 1", "1 == 1.0", "1 != 1.0", "yes == True", "yes == 1", "s == \"ab\"", "n < 5", "f < 3",
    "f < 3.0", "s < \"b\"", "1 <= 1", "2 >= 3", "n > m", "yes > no", "1 == 1 == 1",
    # logic
    "yes and n", "no and n", "z or s", "empty or \"fallback\"", "not n", "not z", "not not s",
    "yes and not no", "n > 2 and s == \"ab\"", "nothing or 5", "items and n",
    # handles and Python operators
    "cash + cash", "cash + 1", "cash == cash", "cash < cash", "broke or cash", "not broke",
    "items + items", "items == items", "items * 2", "dec + 1", "frac", "big", "huge", "big + 1",
    "nothing == nothing", "names[0] < names[1]",
    # parse errors
    "", "1 +", "(1", "1)", "pt.", "pt.1", "f()", "items[", "a b", "1 , 2", "x $ y", "\"open",
    "n = 1", "pt.norm(1)", "[1]", "and", "not", "n not", "..",
]


def _repo_bindings():
    found = set()
    for path in [*ROOT.glob("src/**/*.yaml"), *ROOT.glob("examples/**/*.yaml"), *ROOT.glob("docs/**/*.md"),
                 *ROOT.glob("examples/**/*.py"), *ROOT.glob("tests/*.py"), ROOT / "README.md"]:
        if path.name == Path(__file__).name:
            continue
        for match in re.findall(r"\{\{\s*(.*?)\s*\}\}", path.read_text()):
            if match and "{" not in match and "\\" not in match and match not in DESIGNED:
                found.add(match)
    return sorted(found)


REPO = _repo_bindings()


def test_the_corpus_is_broad():
    assert len(DESIGNED) >= 120
    assert len(REPO) >= 20  # every {{ }} expression used in the repo


@pytest.mark.parametrize("expr", DESIGNED + REPO)
def test_tesserae_evaluates_exactly_as_tre_does(expr):
    assert _tesserae(expr) == _tre(expr)


def test_not_wrapped_is_an_error_naming_the_raw_text():
    with pytest.raises(BindingError, match=r'^binding "count\.get\(\)" is not wrapped in \{\{ \.\.\. \}\}$'):
        parse_binding("count.get()")
    with pytest.raises(BindingError, match="is not wrapped"):
        parse_binding("{{}")


def test_reads_are_recorded_for_dependency_tracking():
    from tesserae import reactive

    count, other = tesserae.Signal(1), tesserae.Signal(2)

    class VM:
        pass

    vm = VM()
    vm.count, vm.other = count, other
    reactive._begin_recording()
    try:
        evaluate_value(parse_binding("{{ count.get() + 1 }}"), vm)
    finally:
        touched = reactive._end_recording()
    assert touched == [count]
