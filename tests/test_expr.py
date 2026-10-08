"""0.5.0 (#209, phase 2): the expression language, row by row against `design/yaml-language.md` section 8.

The sandbox tests are the point: a corpus of escapes that must all fail, every limit with its error, and a fuzzer over the
grammar that must never see anything but a value or an `ExprError`, and never reach the trap objects in its scope.
"""

import random
import re
import types
from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from tesserae import reactive
from tesserae.expr import (
    BUILTIN_FUNCTIONS, ExprError, Limits, MapScope, Origin, compile_expr, compile_statements, compile_template, is_action_name,
)
from tesserae.reactive import Computed, Signal


def run(source, **values):
    return compile_expr(source).evaluate(MapScope(values))


# -- the grammar table (8.1): everything allowed ----------------------------------------------------------------------

ALLOWED = [
    ("1", 1), ("2.5", 2.5), ("'a'", "a"), ('"a"', "a"), ("True", True), ("None", None),
    ("x", 3), ("d['k']", 1), ("d.k", 1), ("items[0]", 10), ("items[1:]", [20, 30]), ("items[::-1]", [30, 20, 10]), ("name[0]", "a"),
    ("not x", False), ("-x", -3), ("+x", 3),
    ("x + 1", 4), ("x - 1", 2), ("x * 2", 6), ("x / 2", 1.5), ("x // 2", 1), ("x % 2", 1), ("x ** 2", 9),
    ("x and 5", 5), ("0 or x", 3), ("x > 1 and x < 5", True),
    ("x == 3", True), ("x != 3", False), ("x < 4", True), ("x <= 3", True), ("x > 3", False), ("x >= 3", True),
    ("2 in items", False), ("10 in items", True), ("10 not in items", False), ("n is None", True), ("x is not None", True),
    ("1 < x < 5", True), ("'yes' if x else 'no'", "yes"), ("'yes' if not x else 'no'", "no"),
    ("f'{x} items'", "3 items"), ("f'{x:03d}'", "003"), ("f'{name!r}'", "'ada'"), ("f'{x * 2}'", "6"),
    ("[1, 2, x]", [1, 2, 3]), ("(1, x)", (1, 3)), ("{1, 2}", {1, 2}), ("{'a': x}", {"a": 3}), ("[*items, x]", [10, 20, 30, 3]),
    ("[i * 2 for i in items]", [20, 40, 60]), ("[i for i in items if i > 10]", [20, 30]), ("{i: i + 1 for i in items}", {10: 11, 20: 21, 30: 31}),
    ("{i % 2 for i in items}", {0}), ("sum(i for i in items)", 60), ("[(a, b) for a in (1, 2) for b in 'xy']", [(1, "x"), (1, "y"), (2, "x"), (2, "y")]),
    ("[a + b for a, b in [(1, 2), (3, 4)]]", [3, 7]),
    ("len(items)", 3), ("min(items)", 10), ("max(1, 5, 3)", 5), ("abs(-4)", 4), ("round(2.567, 2)", 2.57), ("sum(items)", 60),
    ("str(x)", "3"), ("int('7')", 7), ("float('1.5')", 1.5), ("bool(0)", False), ("sorted([3, 1, 2])", [1, 2, 3]),
    ("sorted([3, 1, 2], reverse=True)", [3, 2, 1]), ("list(reversed(items))", [30, 20, 10]), ("list(range(3))", [0, 1, 2]),
    ("list(enumerate('ab'))", [(0, "a"), (1, "b")]), ("list(zip('ab', [1, 2]))", [("a", 1), ("b", 2)]), ("any([0, 1])", True),
    ("all([1, 0])", False), ("list((1, 2))", [1, 2]), ("dict([('a', 1)])", {"a": 1}), ("tuple([1])", (1,)), ("set([1, 1])", {1}),
    ("isinstance(x, int)", True), ("isinstance(name, int)", False), ("format_number(1234.5, 1)", "1,234.5"),
    ("pluralize(1, 'item')", "item"), ("pluralize(2, 'item')", "items"), ("pluralize(2, 'child', 'children')", "children"),
    ("clamp(15, 0, 10)", 10),
    ("name.upper()", "ADA"), ("name.title()", "Ada"), ("'a,b'.split(',')", ["a", "b"]), ("'-'.join(['a', 'b'])", "a-b"),
    ("name.startswith('a')", True), ("name.replace('a', 'o')", "odo"), ("'  x '.strip()", "x"), ("'5'.zfill(3)", "005"),
    ("d.get('k')", 1), ("d.get('zz', 0)", 0), ("list(d.keys())", ["k"]), ("d.values()", [1]), ("d.items()", [("k", 1)]),
    ("items.index(20)", 1), ("items.count(10)", 1),
]


@pytest.mark.parametrize("source, expected", ALLOWED, ids=[a[0] for a in ALLOWED])
def test_the_grammar_allows(source, expected):
    scope = MapScope({"x": 3, "d": {"k": 1}, "items": [10, 20, 30], "name": "ada", "n": None})
    assert compile_expr(source).evaluate(scope) == expected


# -- everything else is an error with a message that says what (8.1) ---------------------------------------------------

DISALLOWED = [
    ("lambda: 1", "a lambda"), ("(y := 1)", "assignment expression"), ("x if", "syntax error"), ("await x", "await is not allowed"),
    ("x & 1", "the operator &"), ("x | 1", "the operator |"), ("x ^ 1", "the operator ^"), ("x << 1", "the operator <<"),
    ("x >> 1", "the operator >>"), ("~x", "the operator ~"), ("x @ x", "the operator @"),
    ("b'x'", "bytes"), ("1j", "complex"), ("...", "ellipsis"),
    ("{**d}", "'**' in a dict display"), ("f(**d)", "'**' in a call"), ("len(**d)", "'**' in a call"),
    ("x is 3", "'is' only compares"), ("x is x", "'is' only compares"), ("x is not 'a'", "'is' only compares"),
    ("[i async for i in x]", "async comprehensions are not allowed"), ("[x for x[0] in items]", "a loop variable must be a name"),
    ("name % 3", None),  # allowed to compile; refused when the left side is text (below)
    ("(1)(2)", "only a function or method can be called"), ("items[0](1)", "only a function or method can be called"),
    ("_x", "private"), ("x._y", "private"), ("x.__class__", "private"), ("__builtins__", "private"),
    ("open('f')", "not a function you can call here"), ("eval('1')", "not a function you can call here"), ("exec('1')", "not a function"),
    ("getattr(x, 'a')", "not a function"), ("type(x)", "not a function"), ("globals()", "not a function"), ("print(1)", "not a function"),
    ("print", "is not defined"), ("name.format()", "str.format() is not available"), ("name.format_map({})", "not available"),
    ("name.encode()", "not available"), ("items.append(1)", "not available"), ("items.pop()", "not available"), ("d.update({})", "not available"),
    ("d.pop('k')", "not available"), ("items.sort()", "not available"), ("(1).bit_length()", "cannot call"), ("x.real", "no readable attribute"),
    ("name.upper", "is a method"), ("sorted(items, key=len)", None),  # a function value is fine to pass to sorted()? see below
    ("x +", "syntax error"), ("", "empty"), ("   ", "empty"), ("1 2", "syntax error"), ("x = 1", "syntax error"), ("import os", "syntax error"),
]


@pytest.mark.parametrize("source, message", [d for d in DISALLOWED if d[1] is not None], ids=[d[0] or "''" for d in DISALLOWED if d[1] is not None])
def test_the_grammar_refuses(source, message):
    scope = MapScope({"x": 3, "d": {"k": 1}, "items": [10, 20, 30], "name": "ada"})
    with pytest.raises(ExprError, match=re.escape(message)):
        compile_expr(source).evaluate(scope)


def test_percent_formatting_is_refused_on_text_but_works_on_numbers():
    assert run("7 % 3") == 1
    with pytest.raises(ExprError, match="use an f-string"):
        run("'%s' % 1")


# -- names, scope and built-ins (8.3, 8.5) -------------------------------------------------------------------------------


def test_an_unknown_name_suggests_the_nearest():
    with pytest.raises(ExprError, match=r"'cnt' is not defined \(did you mean 'count'"):
        run("cnt + 1", count=1)


def test_the_scope_wins_over_the_built_ins_and_comprehension_names_do_not_leak():
    assert run("len", len="mine") == "mine"
    with pytest.raises(ExprError, match="'i' is not defined"):
        run("[i for i in [1]] + [i]")


def test_comprehension_names_are_not_free_names_of_the_expression():
    assert compile_expr("[i * k for i in items]").names == {"k", "items"}
    assert compile_expr("a + b.c[d]").names == {"a", "b", "d"}


def test_a_comprehension_variable_cannot_be_called_and_a_name_that_is_not_a_function_cannot_be_called():
    with pytest.raises(ExprError, match="not a function you can call here"):
        run("[f(1) for f in [len]]")
    with pytest.raises(ExprError, match="not a function you can call here"):
        compile_expr("save()").evaluate(MapScope({"save": lambda: 1}))


def test_the_built_in_list_is_the_documented_one():
    assert set(BUILTIN_FUNCTIONS) == {
        "len", "min", "max", "abs", "round", "sum", "str", "int", "float", "bool", "sorted", "reversed", "range", "enumerate", "zip", "any",
        "all", "list", "dict", "tuple", "set", "isinstance", "format_number", "pluralize", "clamp"}


# -- Signals read as values (8.4) --------------------------------------------------------------------------------------------


def test_a_signal_reads_as_its_value_and_get_still_works():
    count = Signal(4)
    scope = MapScope({"count": count})
    assert compile_expr("count").evaluate(scope) == 4
    assert compile_expr("count + 1").evaluate(scope) == 5
    assert compile_expr("count.get() * 2").evaluate(scope) == 8
    assert compile_expr("f'{count} items'").evaluate(scope) == "4 items"


def test_a_computed_and_a_signal_inside_a_container_read_as_values():
    base = Signal(2)
    scope = MapScope({"double": Computed(lambda: base.get() * 2), "state": SimpleNamespace(user=Signal("Ada"))})
    assert compile_expr("double + 1").evaluate(scope) == 5
    assert compile_expr("state.user").evaluate(scope) == "Ada"
    assert compile_expr("state.user.get().upper()").evaluate(scope) == "ADA"
    assert compile_expr("state.user.upper()").evaluate(scope) == "ADA"


def test_reading_records_the_dependency_so_a_binding_follows_the_signal():
    count = Signal(1)
    expr = compile_expr("count * 10")
    reactive._begin_recording()
    try:
        expr.evaluate(MapScope({"count": count}))
    finally:
        recorded = reactive._end_recording()
    assert count in recorded


def test_evaluate_raw_keeps_the_signal_for_a_two_way_property():
    count = Signal(1)
    assert compile_expr("count").evaluate_raw(MapScope({"count": count})) is count
    assert compile_expr("count").bare_name() == "count" and compile_expr("count + 1").bare_name() is None


def test_a_signal_has_only_get_in_an_expression():
    with pytest.raises(ExprError):
        run("count.set(3)", count=Signal(1))


# -- attribute rules (8.4) -----------------------------------------------------------------------------------------------------


class Plain:
    def __init__(self):
        self.title = "t"
        self.items = [1, 2]
        self._secret = "no"

    def method(self):
        return 1


class Narrow:
    __expose__ = ("shown",)
    shown = 1
    hidden = 2


def test_object_attributes_are_read_only_public_and_never_methods():
    assert run("o.title", o=Plain()) == "t"
    assert run("o.items[1]", o=Plain()) == 2
    with pytest.raises(ExprError, match="is a method"):
        run("o.method", o=Plain())
    with pytest.raises(ExprError, match="cannot call"):
        run("o.method()", o=Plain())
    with pytest.raises(ExprError, match="private"):
        run("o._secret", o=Plain())
    with pytest.raises(ExprError, match=r"has no attribute 'titel'.*did you mean 'title'"):
        run("o.titel", o=Plain())


def test_expose_narrows_the_readable_attributes():
    assert run("o.shown", o=Narrow()) == 1
    with pytest.raises(ExprError, match="not exposed"):
        run("o.hidden", o=Narrow())


def test_a_mapping_reads_by_attribute_and_names_a_missing_key():
    assert run("row.title", row={"title": "x"}) == "x"
    with pytest.raises(ExprError, match=r"no key 'titel'.*did you mean 'title'"):
        run("row.titel", row={"title": "x"})


@pytest.mark.parametrize("value", [types, int, len, Plain.method, (lambda: 1), (x for x in []), Plain.__init__.__code__])
def test_modules_classes_and_functions_have_no_attributes_to_read(value):
    with pytest.raises(ExprError, match="cannot"):
        run("v.anything", v=value)
    with pytest.raises(ExprError):
        run("v[0]", v=value)
    with pytest.raises(ExprError):
        run("[i for i in v]", v=value)


# -- statements (9.1) ------------------------------------------------------------------------------------------------------------


def test_assignment_augmented_assignment_and_calls_run_in_order():
    calls = []
    scope = MapScope({"n": Signal(1), "on": False}, writable={"n", "on"}, actions={"save": lambda *a, **k: calls.append((a, k)),
                                                                                 "window.close": lambda: calls.append("closed")})
    compile_statements("n = n + 1; n += 5; on = not on; save(n, flag=on); window.close()").run(scope)
    assert scope.values["n"].get() == 7 and scope.values["on"] is True
    assert calls == [((7,), {"flag": True}), "closed"]


def test_newlines_separate_statements_too_and_event_is_in_scope():
    scope = MapScope({"query": "", "page": 3}, writable={"query", "page"})
    compile_statements("query = event.value\npage = 0").run(scope, event=SimpleNamespace(value="hello"))
    assert (scope.values["query"], scope.values["page"]) == ("hello", 0)


def test_a_loop_variable_name_can_be_read_in_a_handler_through_the_scope():
    seen = []
    scope = MapScope({"item": {"id": 7}}, actions={"open": seen.append})
    compile_statements("open(item.id)").run(scope)
    assert seen == [7]


@pytest.mark.parametrize("source, message", [
    ("items = 1", "is not writable"), ("missing += 1", "'missing' is not defined"),
    ("if x: n = 1", "'if' is not available"), ("for i in x: pass", "'for' is not available"), ("del n", "'del' is not available"),
    ("return 1", "'return' is not available"), ("import os", "'import' is not available"), ("def f(): pass", "'def' is not available"),
    ("class A: pass", "'class' is not available"), ("with x: pass", "'with' is not available"), ("raise ValueError", "'raise' is not available"),
    ("x.y = 1", "assign to one name"), ("x[0] = 1", "assign to one name"), ("a = b = 1", "assign to one name"), ("x.y += 1", "assign to a name"),
    ("x |= 1", "is not allowed here"), ("x <<= 1", "is not allowed here"), ("n: int = 1", "an annotated assignment"), ("pass", "'pass' is not available"),
    ("1 + 1", "an expression statement"), ("x", "an expression statement"), ("_n = 1", "private"), ("(a, b) = (1, 2)", "assign to one name"),
])
def test_only_assignments_and_calls_are_statements(source, message):
    scope = MapScope({"n": 1, "x": 1, "items": [1]}, writable={"n", "x"})
    with pytest.raises(ExprError, match=message):
        compile_statements(source).run(scope)


def test_a_call_that_is_not_an_action_or_a_built_in_is_an_error_not_a_name_error():
    with pytest.raises(ExprError, match="not a function you can call here"):
        compile_statements("explode()").run(MapScope())


def test_is_action_name_tells_a_name_from_statements():
    assert all(is_action_name(t) for t in ("save", "window.close", "navigate.Settings", " surface.dismiss "))
    assert not any(is_action_name(t) for t in ("x = 1", "save()", "a b", "1x", "", "a;b"))


# -- templates ------------------------------------------------------------------------------------------------------------------


def test_text_with_parts_is_a_template_and_a_single_part_keeps_its_type():
    scope = MapScope({"name": "Ada", "n": 3, "flag": True, "nothing": None})
    assert compile_template("Hello {{ name }}!").evaluate(scope) == "Hello Ada!"
    assert compile_template("{{ n }}").evaluate(scope) == 3
    assert compile_template("{{ flag }}").evaluate(scope) is True
    assert compile_template("{{ n }} of {{ n * 2 }}").evaluate(scope) == "3 of 6"
    assert compile_template("[{{ nothing }}]").evaluate(scope) == "[]"
    assert compile_template("plain") is None and compile_template("") is None


def test_a_closing_braces_inside_a_string_or_brackets_belongs_to_the_expression():
    scope = MapScope({"d": {"a": 1}})
    assert compile_template("{{ {'a': 2}['a'] }}").evaluate(scope) == 2
    assert compile_template("{{ '}}' + 'x' }}").evaluate(scope) == "}}x"
    assert compile_template("a {{ d['a'] }} b").evaluate(scope) == "a 1 b"
    assert compile_template("{{ [x for x in [1, 2]] }}").evaluate(scope) == [1, 2]


def test_a_template_that_is_not_closed_is_an_error_with_a_position():
    with pytest.raises(ExprError, match="never closed") as raised:
        compile_template("Hello {{ name", origin=Origin("A_View.yaml", 4, 8))
    assert (raised.value.line, raised.value.column) == (4, 14)


def test_a_template_reports_whether_it_is_reactive():
    scope = MapScope({"count": 1, "label": "x"}, reactive={"count"})
    assert compile_template("a {{ count }}").is_reactive(scope) and not compile_template("a {{ label }}").is_reactive(scope)


# -- static and reactive (8.2) ----------------------------------------------------------------------------------------------------


def test_an_expression_is_reactive_when_any_name_it_reads_is():
    scope = MapScope({"height": 40, "count": 1}, reactive={"count"})
    assert not compile_expr("height / 2").is_reactive(scope)
    assert compile_expr("count + height").is_reactive(scope)
    assert not compile_expr("[i for i in range(3)]").is_reactive(scope)
    assert not compile_expr("len('x')").is_reactive(MapScope())


# -- errors carry the position (14) ------------------------------------------------------------------------------------------------


def test_errors_name_the_file_line_and_column_of_the_text_in_the_yaml():
    with pytest.raises(ExprError) as raised:
        compile_expr("count + cnt", origin=Origin("Main_View.yaml", 14, 7)).evaluate(MapScope({"count": 1}))
    error = raised.value
    assert str(error).startswith("Main_View.yaml:14:16: ") and (error.line, error.column) == (14, 15)
    assert "'cnt' is not defined" in str(error) and "did you mean 'count'" in str(error)
    rendered = error.render()
    assert "count + cnt" in rendered and rendered.rstrip().endswith("^^^")


def test_a_syntax_error_points_into_the_text_and_leading_whitespace_is_accounted_for():
    with pytest.raises(ExprError) as raised:
        compile_expr("   x +", origin=Origin("A_View.yaml", 2, 10))
    assert raised.value.line == 2 and "syntax error" in str(raised.value)
    with pytest.raises(ExprError) as raised:
        compile_expr("  nope", origin=Origin("A_View.yaml", 2, 10)).evaluate(MapScope())
    assert raised.value.column == 12  # 10 + the two leading spaces


def test_an_error_inside_a_multiline_expression_is_on_its_own_line():
    with pytest.raises(ExprError) as raised:
        compile_expr("(1 +\n  oops)", origin=Origin("A_View.yaml", 5, 4)).evaluate(MapScope())
    assert (raised.value.line, raised.value.column) == (6, 2)


# -- limits (8.6) ----------------------------------------------------------------------------------------------------------------------


LIMIT_CASES = [
    ("'x' * 2000", "expression is 10", Limits(max_source=8)),
    ("[" * 45 + "]" * 45, "nested more than 40", Limits()),
    ("[" + ",".join(["1"] * 1100) + "]", "more than 1000 parts", Limits(max_source=10**6)),
    ("[x for x in range(100000)]", "too expensive", Limits()),
    ("[x for x in range(10) for y in range(10) for z in range(10)]", "too expensive", Limits(max_steps=500)),
    ("range(100001)", "the limit is 100000", Limits()),
    ("range(10**9)", "the limit is 100000", Limits()),
    ("'a' * 1000001", "repeated sequence", Limits()),
    ("[0] * 2_000_000", "repeated sequence", Limits()),
    ("3 * 'ab' * 400000", "repeated sequence", Limits()),
    ("'a' * 600000 + 'b' * 600000", "joined sequence", Limits()),
    ("2 ** 65", "exponent is over 64", Limits()),
    ("10 ** 64 ** 2", "exponent is over 64", Limits()),
    ("9 ** 64 * 9 ** 64 * 9 ** 64 * 9 ** 64 * 9 ** 64 * 9 ** 64 * 9 ** 64 * 9 ** 64 * 9 ** 64 * 9 ** 64 * 9 ** 64 * 9 ** 64", "too large", Limits(max_int_bits=2000)),
    ("f'{\"a\" * 600000}{\"b\" * 600000}'", "over 1000000 characters", Limits(max_sequence=10**7)),
    ("'-'.join(['x' * 500000, 'y' * 600000])", "over 1000000 characters", Limits(max_sequence=10**7)),
    ("'x'.center(2000000)", "the width is over", Limits()),
    ("'x'.zfill(10**7)", "the width is over", Limits()),
    ("list(range(100000)) + list(range(100000)) + list(range(100000))", "too expensive", Limits(max_steps=250_000)),
    ("sum([[1]] * 500000, [])", "too expensive", Limits(max_steps=100_000)),
]


@pytest.mark.parametrize("source, message, limits", LIMIT_CASES, ids=[c[0][:50] for c in LIMIT_CASES])
def test_every_limit_is_a_named_error(source, message, limits):
    with pytest.raises(ExprError, match=message or ""):
        compile_expr(source, limits=limits).evaluate(MapScope())


def test_a_budget_makes_a_slow_expression_fail_it_does_not_hang():
    expr = compile_expr("[a + b + c for a in range(100) for b in range(100) for c in range(100)]")
    with pytest.raises(ExprError, match="too expensive"):
        expr.evaluate(MapScope())


def test_a_big_but_legitimate_expression_fits_the_default_budget():
    assert run("sum([i for i in range(5000)])") == sum(range(5000))
    assert len(run("[str(i) for i in range(2000)]")) == 2000


def test_the_budget_covers_a_whole_handler():
    scope = MapScope({"n": 0}, writable={"n"})
    statements = compile_statements("; ".join(["n = n + sum([i for i in range(300)])"] * 20), limits=Limits(max_steps=2000))
    with pytest.raises(ExprError, match="too expensive"):
        statements.run(scope)


# -- the sandbox: a corpus of escapes that must all fail -----------------------------------------------------------------------------


class Trap:
    """Anything that gets past the sandbox and calls, mutates or imports through this sets `tripped`."""

    tripped: list = []

    def __init__(self, name="trap"):
        self._name = name

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        return Trap(name)

    def __call__(self, *a, **k):
        Trap.tripped.append(("called", self._name))
        return 1

    def __setattr__(self, name, value):
        if name != "_name":
            Trap.tripped.append(("set", name))
        object.__setattr__(self, name, value)

    def __iter__(self):
        Trap.tripped.append(("iterated", self._name))
        return iter(())

    def __getitem__(self, key):
        return Trap(f"item {key}")

    def __len__(self):
        Trap.tripped.append(("len", self._name))
        return 1

    def __contains__(self, item):
        Trap.tripped.append(("contains", self._name))
        return True

    def dangerous(self):
        Trap.tripped.append(("method", self._name))


# These are INPUTS that the language must reject, quoted as text: nothing in this file calls Python's eval or exec.
ESCAPES = [
    # attribute traversal
    "().__class__", "().__class__.__bases__", "().__class__.__bases__[0].__subclasses__()", "[].__class__.__mro__", "''.__class__.__mro__[1]",
    "x.__class__", "x.__dict__", "x.__globals__", "x.__init__.__globals__", "len.__self__", "len.__module__", "obj.__class__",
    "(lambda: 1).__globals__", "trap.__class__", "trap.__dict__", "d.__class__", "items.__class__.__base__",
    "x.__getattribute__('a')", "x.__reduce__()", "''.join.__self__",
    # private names
    "__import__('os').system('true')", "__builtins__", "__builtins__['eval']", "_", "_x", "__name__", "__file__", "_trap",
    # unicode normalisation to a dunder
    "().＿＿class＿＿", "＿＿import＿＿('os')", "ｅval('1')", "x.＿private",
    # eval and friends
    "eval('1')", "exec('x=1')", "compile('1', 'a', 'eval')", "open('/etc/passwd')", "input()", "breakpoint()", "help()", "exit()", "quit()",
    "getattr(x, 'real')", "setattr(x, 'a', 1)", "delattr(x, 'a')", "hasattr(x, 'a')", "vars()", "dir()", "globals()", "locals()", "type(x)",
    "type('A', (), {})", "object()", "super()", "id(x)", "hash(x)", "callable(x)", "iter(x)", "next(x)", "print(x)", "format(x, '')",
    "chr(65)", "ord('a')", "hex(1)", "bytes(1)", "bytearray(1)", "memoryview(b'')", "slice(1)", "property()", "staticmethod(len)", "frozenset()",
    "issubclass(int, int)", "isinstance(x, object)", "isinstance(x, type)", "isinstance(x, (int, str))", "isinstance(x, trap)",
    # format string traversal
    "'{0.__class__}'.format(x)", "'{x.__class__}'.format(x=x)", "'{}'.format(x)", "'%s' % x", "'%(a)s' % {'a': 1}", "'{0}'.format_map({})",
    "'{0.__class__}'.format_map(x)", "f'{x.__class__}'", "f'{x!r:{x.__class__}}'", "f'{__import__(\"os\")}'", "f'{(lambda: 1)()}'",
    # lambda, comprehension and generator tricks
    "(lambda: 1)()", "[lambda: 1 for _ in [1]]", "(x for x in [1]).gi_frame", "(x for x in [1]).gi_frame.f_globals", "[].__class__",
    "[x for x in ().__class__.__mro__]", "{k: v for k, v in x.__dict__.items()}", "[c for c in ().__class__.__bases__[0].__subclasses__()]",
    "(i for i in [1]).__next__()", "[i for i in trap]", "list(trap)", "sorted(trap)", "sum(trap)", "dict(trap)", "[*trap]", "(*trap,)",
    # calls on methods of non-whitelisted objects and types
    "trap()", "trap.dangerous()", "trap.dangerous", "trap.x.y()", "obj.method()", "obj.method", "d.update({})", "items.append(1)",
    "items.extend([1])", "items.clear()", "items.pop()", "items.remove(1)", "items.sort()", "items.reverse()", "items.insert(0, 1)",
    "d.pop('k')", "d.popitem()", "d.setdefault('a', 1)", "d.clear()", "d.copy()", "name.encode()", "name.translate({})", "name.maketrans('a', 'b')",
    "name.format()", "name.partition('a')", "name.expandtabs()", "int.__call__(1)", "str.upper(name)", "int.from_bytes(b'', 'big')",
    "(1).bit_length()", "(1.5).as_integer_ratio()", "x.real", "x.numerator", "x.imag", "True.real",
    # statements and assignment in an expression
    "x = 1", "x += 1", "(y := 1)", "import os", "from os import path", "del x", "pass", "raise ValueError", "assert x", "return x", "yield x",
    "await x", "async def f(): pass", "def f(): pass", "class A: pass", "with x: pass", "try: pass\nexcept: pass", "global x", "nonlocal x",
    "x; y", "x\ny", "print(x) if x else None",
    # operators that are not in the language
    "x & 1", "x | 1", "x ^ 1", "x << 1", "x >> 1", "~x", "x @ x", "x if x else y if", "*x", "**x", "x ** ", "[*]", "{**x}", "f(**x)",
    # dunder-ish via subscript and strings
    "d['__class__']", "x.__class__ if x else 0", "name.__getitem__(0)", "getattr", "x['__class__']",
    # resource exhaustion
    "'a' * 10**9", "[0] * 10**9", "10 ** 10 ** 10", "9 ** 9 ** 9", "2 ** 100000", "range(10**12)", "list(range(10**7))", "sum(range(10**7))",
    "'x'.zfill(10**9)", "'x'.center(10**9)", "'x'.ljust(10**9)", "[i for i in range(10**6)]", "[0 for a in range(1000) for b in range(1000)]",
    "(" * 500 + "1" + ")" * 500, "[" * 300 + "]" * 300, "-" * 5000 + "1", "x + " * 3000 + "x", "'" + "a" * 3000 + "'", "not " * 800 + "x",
    "1 if " * 100 + "1 else 2" + " else 2" * 100,
]


def _escape_scope():
    return MapScope({"x": 3, "d": {"k": 1}, "items": [1, 2], "name": "ada", "obj": Plain(), "trap": Trap()})


@pytest.mark.parametrize("source", ESCAPES, ids=[e[:60].replace("\n", " ") for e in ESCAPES])
def test_the_escape_corpus_all_fails_and_never_reaches_the_trap(source):
    Trap.tripped.clear()
    with pytest.raises(ExprError):
        compile_expr(source).evaluate(_escape_scope())
    assert Trap.tripped == []


@pytest.mark.parametrize("source", ESCAPES, ids=[e[:60].replace("\n", " ") for e in ESCAPES])
def test_the_escape_corpus_fails_as_a_handler_too(source):
    Trap.tripped.clear()
    scope = _escape_scope()
    scope.writable = {"n"}
    try:
        compile_statements(source).run(scope)
    except ExprError:
        pass
    else:
        pytest.fail(f"{source!r} ran as a handler")
    assert Trap.tripped == []


def test_the_scope_names_a_handler_may_call_are_the_only_calls_outside_the_built_ins():
    Trap.tripped.clear()
    scope = _escape_scope()
    scope.actions = {"save": lambda: Trap.tripped.append("saved")}
    compile_statements("save()").run(scope)
    assert Trap.tripped == ["saved"]
    for source in ("trap()", "trap.dangerous()", "obj.method()"):
        Trap.tripped.clear()
        with pytest.raises(ExprError):
            compile_statements(source).run(scope)
        assert Trap.tripped == []


# -- the fuzzer: a value or an ExprError, nothing else, and never the trap ------------------------------------------------------------------


ATOMS = ["x", "d", "items", "name", "n", "1", "0", "-1", "2.5", "'a'", "''", "True", "None", "trap", "obj", "count", "(1, 2)", "[]", "{}",
         "[1, 2, 3]", "{'a': 1}", "range(5)", "len", "open", "eval", "__class__", "_x", "x.y", "d.k", "items[0]", "name[0]", "d['k']"]
OPS = ["+", "-", "*", "/", "//", "%", "**", "==", "!=", "<", ">", "and", "or", "in", "is", "&", "|", "<<"]
FUNCS = ["len", "min", "max", "sum", "sorted", "list", "range", "str", "int", "float", "abs", "round", "any", "all", "enumerate", "zip", "dict",
         "set", "tuple", "isinstance", "eval", "open", "getattr", "type", "print", "format_number", "pluralize", "clamp"]
METHODS = ["upper", "lower", "split", "join", "get", "keys", "items", "append", "pop", "format", "encode", "dangerous", "count", "index", "replace"]


def _gen(rng: random.Random, depth: int = 0) -> str:
    if depth > 4 or rng.random() < 0.25:
        return rng.choice(ATOMS)
    kind = rng.random()
    sub = lambda: _gen(rng, depth + 1)  # noqa: E731
    if kind < 0.30:
        return f"({sub()} {rng.choice(OPS)} {sub()})"
    if kind < 0.42:
        return f"{rng.choice(FUNCS)}({', '.join(sub() for _ in range(rng.randint(0, 3)))})"
    if kind < 0.54:
        return f"{sub()}.{rng.choice(METHODS)}({', '.join(sub() for _ in range(rng.randint(0, 2)))})"
    if kind < 0.60:
        return f"{sub()}[{sub()}]"
    if kind < 0.66:
        return f"({sub()} if {sub()} else {sub()})"
    if kind < 0.72:
        return f"[{sub()} for i in {sub()} if {sub()}]"
    if kind < 0.76:
        return f"f'{{{sub()}}}'"
    if kind < 0.80:
        return f"not {sub()}"
    if kind < 0.84:
        return f"{{{sub()}: {sub()} for i in {sub()}}}"
    if kind < 0.88:
        return f"lambda: {sub()}"
    if kind < 0.92:
        return f"{sub()}.{rng.choice(['__class__', '_x', 'real', 'y', 'k', 'dangerous'])}"
    return f"[{', '.join(sub() for _ in range(rng.randint(0, 3)))}]"


def test_the_fuzzer_only_ever_sees_a_value_or_an_expr_error():
    rng = random.Random(20261008)
    values = errors = 0
    for _ in range(4000):
        source = _gen(rng)
        Trap.tripped.clear()
        try:
            compile_expr(source, limits=Limits(max_steps=20_000)).evaluate(_escape_scope())
            values += 1
        except ExprError:
            errors += 1
        except Exception as exc:  # noqa: BLE001
            pytest.fail(f"{source!r} raised {type(exc).__name__}: {exc}")
        assert Trap.tripped == [], source
    assert values > 100 and errors > 1000  # the fuzzer exercises both sides


def test_the_fuzzer_over_handlers_never_trips_the_trap():
    rng = random.Random(7)
    for _ in range(1500):
        source = rng.choice(["x = {}", "{} = x", "x += {}", "save({})", "trap.dangerous({})", "x.y = {}", "d['k'] = {}", "n = {}; save(n)"]).format(_gen(rng))
        Trap.tripped.clear()
        scope = _escape_scope()
        scope.writable = {"x", "n"}
        scope.actions = {"save": lambda *a, **k: None}
        try:
            compile_statements(source, limits=Limits(max_steps=20_000)).run(scope)
        except ExprError:
            pass
        except Exception as exc:  # noqa: BLE001
            pytest.fail(f"{source!r} raised {type(exc).__name__}: {exc}")
        assert Trap.tripped == [], source


def test_mutating_a_valid_expression_one_token_at_a_time_never_escapes():
    rng = random.Random(99)
    seeds = [s for s, _ in ALLOWED][:80]
    tokens = ["__class__", "lambda", "import", ":=", "**", "[", "]", "(", ")", "'", ".", "_", "eval", "open", "trap", "await", "yield", ";", "\n"]
    for source in seeds:
        for _ in range(20):
            cut = rng.randrange(len(source) + 1)
            mutated = source[:cut] + rng.choice(tokens) + source[cut:]
            Trap.tripped.clear()
            try:
                compile_expr(mutated, limits=Limits(max_steps=20_000)).evaluate(_escape_scope())
            except ExprError:
                pass
            except Exception as exc:  # noqa: BLE001
                pytest.fail(f"{mutated!r} raised {type(exc).__name__}: {exc}")
            assert Trap.tripped == [], mutated


# -- the sandbox's own claims, one test each so removing a rule fails one -----------------------------------------------------------------


@dataclass
class Row:
    title: str = "t"


def test_a_dataclass_instance_reads_like_an_object():
    assert run("r.title", r=Row()) == "t"


def test_unhashable_keys_bad_indexes_and_type_errors_are_expression_errors():
    for source in ("{[1]: 2}", "items[10]", "d['nope']", "1 + 'a'", "'a' < 1", "int('x')", "name[1.5]", "len(5)", "sum('a')", "max([])"):
        with pytest.raises(ExprError):
            run(source, items=[1], d={}, name="ada")


def test_a_deeply_nested_but_legal_expression_does_not_overflow_the_stack():
    assert run("(" * 35 + "1" + ")" * 35) == 1
    with pytest.raises(ExprError):
        run("[" * 60 + "1" + "]" * 60)


# Each of these is a rule the mutation check found no test for: switching it off left the whole suite green.

@pytest.mark.parametrize("source", ["[i for i in trap]", "1 in trap", "1 not in trap", "list(trap)", "sum(trap)", "len(trap)", "{**trap}", "[*trap]"])
def test_an_object_that_is_not_a_built_in_container_is_never_iterated_or_searched(source):
    Trap.tripped.clear()
    with pytest.raises(ExprError):
        compile_expr(source).evaluate(MapScope({"trap": Trap()}))
    assert Trap.tripped == []


@pytest.mark.parametrize("source", ["isinstance(1, tuple)", "isinstance(1, (int, str))", "isinstance(1, object)", "isinstance(1, trap)", "isinstance(1, int | str)"])
def test_isinstance_compares_only_with_the_named_basic_types(source):
    with pytest.raises(ExprError):
        compile_expr(source).evaluate(MapScope({"trap": Trap()}))


def test_event_is_not_a_name_in_an_expression():
    with pytest.raises(ExprError, match="'event' is not defined"):
        compile_expr("event").evaluate(MapScope({}))


def test_a_loop_variable_that_shares_an_action_name_is_not_the_action():
    calls = []
    scope = MapScope({}, writable={"n"}, actions={"save": lambda *a, **k: calls.append(a), "show": lambda *a, **k: None})
    with pytest.raises(ExprError):
        compile_statements("show([save(1) for save in [1]])").run(scope)
    assert calls == []


def test_the_power_cap_names_itself_before_the_number_grows():
    with pytest.raises(ExprError, match=r"\*\* is too large"):
        compile_expr("(3 ** 64) ** 64").evaluate(MapScope({}))
