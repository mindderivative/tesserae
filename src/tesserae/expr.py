"""Tesserae's expression language: a sandboxed subset of Python (`design/yaml-language.md`, section 8).

`{{ ... }}` in a view is one expression in this language, and a handler is a short list of statements in it. It is parsed with
Python's own `ast`, checked against a whitelist of node types, and run by a small evaluator: nothing is ever `eval`ed.

    expr = compile_expr("count + 1 if ready else 0")
    expr.evaluate(MapScope({"count": 2, "ready": True}))        # 3

- **Names** resolve through a *scope* (`lookup(name)`), then the built-ins. A `Signal` or `Computed` reads as its value
  (`{{ count }}`); `count.get()` keeps working.
- **Static or reactive**: `Expr.is_reactive(scope)` says whether any name the expression reads is reactive in the scope. The
  caller makes a binding of a reactive one and substitutes the value of a static one.
- **Limits**: a step budget, a length, depth and size for the source, and caps on `range`, repeated sequences, `**` and strings.
  Anything over is an `ExprError` and never a hang.
- **No escape**: no attribute starting with `_`, no attribute or call on a module, class or function, no lambda, no walrus, no
  import, no `format` (it reaches attributes), no calls but the whitelist below and, in a handler, the scope's actions.

Every failure is an `ExprError` with the position (line and column) in the source text, and `render()` draws a caret.
"""

from __future__ import annotations

import ast
import datetime
import decimal
import difflib
import enum
import math
import operator
import re
import types
import warnings
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Mapping, Optional

from tesserae.reactive import Computed, Signal

__all__ = [
    "BUILTIN_FUNCTIONS", "DEFAULT_LIMITS", "Expr", "ExprError", "Limits", "MapScope", "Origin", "Statements", "Template",
    "compile_expr", "compile_statements", "compile_template", "is_action_name",
]

MISSING = object()


# -- errors -------------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Origin:
    """Where an expression's text starts in its file, so errors can name the file, line and column: `line` is 1-based, `column`
    0-based (the column of the first character of the text)."""

    file: Optional[str] = None
    line: int = 1
    column: int = 0


class ExprError(ValueError):
    """A problem with an expression: it does not parse, uses something the language does not allow, names something that does
    not exist, goes over a limit, or fails to evaluate. `line` and `column` (1-based and 0-based) are in the *file* when an
    `Origin` was given, else in the expression text; `end_column` ends the span on that line (or is `None`)."""

    def __init__(self, message: str, *, source: str = "", line: int = 1, column: int = 0, end_column: Optional[int] = None,
                 origin: Optional[Origin] = None, hint: Optional[str] = None) -> None:
        self.message = message
        self.source = source
        self.hint = hint
        self.file = origin.file if origin else None
        # positions inside the text, mapped to the file's when the origin is known
        self.text_line, self.text_column = line, column
        if origin is not None:
            self.line = origin.line + line - 1
            self.column = origin.column + column if line == 1 else column
        else:
            self.line, self.column = line, column
        self.end_column = None if end_column is None else self.column + (end_column - column)
        super().__init__(self._summary())

    def _summary(self) -> str:
        where = ""
        if self.file is not None:
            where = f"{self.file}:{self.line}:{self.column + 1}: "
        text = self.message + (f" ({self.hint})" if self.hint else "")
        return f"{where}{text}"

    def render(self) -> str:
        """The message with the offending line of the expression and a caret under it."""
        lines = self.source.splitlines() or [""]
        line = lines[min(self.text_line, len(lines)) - 1]
        width = max(1, (self.end_column - self.column) if self.end_column is not None else 1)
        return f"{self}\n    {line}\n    {' ' * self.text_column}{'^' * width}"


# -- limits -------------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Limits:
    """The sandbox's caps (section 8.6). Each one that is exceeded is a named `ExprError`."""

    max_source: int = 2000        # characters of expression text
    max_depth: int = 40           # nesting of the syntax tree
    max_nodes: int = 1000         # nodes in the syntax tree
    max_steps: int = 200_000      # visited nodes and iterations in one evaluation
    max_range: int = 100_000      # length of a `range`
    max_sequence: int = 1_000_000  # items in a repeated or joined sequence
    max_pow_exponent: int = 64    # `**` exponent
    max_int_bits: int = 4096      # size of an integer result
    max_string: int = 1_000_000   # characters in a string result


DEFAULT_LIMITS = Limits()


# -- scopes -------------------------------------------------------------------------------------------------------------


class MapScope:
    """A scope over a dict, for tests and for places with plain values. `reactive` names read as reactive, `writable` names can
    be assigned in a handler, `actions` maps a dotted name (`window.close`, `save`) to a function a handler may call."""

    def __init__(self, values: Optional[Mapping[str, Any]] = None, *, reactive: Iterable[str] = (), writable: Iterable[str] = (),
                 actions: Optional[Mapping[str, Callable[..., Any]]] = None) -> None:
        self.values = dict(values or {})
        self.reactive = set(reactive)
        self.writable = set(writable)
        self.actions = dict(actions or {})

    def lookup(self, name: str) -> Any:
        return self.values[name]

    def names(self) -> list[str]:
        return list(self.values)

    def is_reactive(self, name: str) -> bool:
        return name in self.reactive

    def assign(self, name: str, value: Any) -> None:
        if name not in self.writable:
            raise KeyError(name)
        current = self.values.get(name)
        if isinstance(current, Signal):
            current.set(value)
        else:
            self.values[name] = value

    def is_action(self, path: str) -> bool:
        return path in self.actions

    def call_action(self, path: str, args: list[Any], kwargs: dict[str, Any]) -> Any:
        return self.actions[path](*args, **kwargs)


def _scope_names(scope: Any) -> list[str]:
    names = getattr(scope, "names", None)
    try:
        return list(names()) if names is not None else []
    except Exception:  # noqa: BLE001 - only for suggestions
        return []


# -- built-ins ----------------------------------------------------------------------------------------------------------


def _format_number(x: Any, digits: int = 0) -> str:
    return f"{x:,.{int(digits)}f}"


def _pluralize(n: Any, one: str, other: Optional[str] = None) -> str:
    return one if n == 1 else (other if other is not None else one + "s")


def _clamp(x: Any, low: Any, high: Any) -> Any:
    return max(low, min(high, x))


#: The functions an expression may call (section 8.5). `isinstance` is special-cased: its second argument must be one of the
#: types here.
BUILTIN_FUNCTIONS: dict[str, Callable[..., Any]] = {
    "len": len, "min": min, "max": max, "abs": abs, "round": round, "sum": sum, "str": str, "int": int, "float": float,
    "bool": bool, "sorted": sorted, "reversed": lambda x: list(reversed(x)), "range": range, "enumerate": lambda x, start=0: list(enumerate(x, start)),
    "zip": lambda *xs: list(zip(*xs)), "any": any, "all": all, "list": list, "dict": dict, "tuple": tuple, "set": set,
    "isinstance": isinstance, "format_number": _format_number, "pluralize": _pluralize, "clamp": _clamp,
}
_ISINSTANCE_TYPES = {"str": str, "int": int, "float": float, "bool": bool, "list": list, "dict": dict}
#: Functions that consume iterables: their iterable arguments are bounded and charged to the step budget first.
_ITERATING = {"min", "max", "sum", "sorted", "reversed", "enumerate", "zip", "any", "all", "list", "dict", "tuple", "set"}

_STR_METHODS = frozenset("lower upper title capitalize strip lstrip rstrip split splitlines join startswith endswith replace find count "
                         "zfill isdigit isalpha center ljust rjust removeprefix removesuffix".split())
_LIST_METHODS = frozenset({"index", "count"})
_DICT_METHODS = frozenset({"get", "keys", "values", "items"})
_METHODS_BY_TYPE: list[tuple[type, frozenset[str]]] = [
    (str, _STR_METHODS), (list, _LIST_METHODS), (tuple, _LIST_METHODS), (dict, _DICT_METHODS),
]
_DICT_VIEWS = (type({}.keys()), type({}.values()), type({}.items()))
_SEQUENCE_BUILDING = {"center", "ljust", "rjust", "zfill"}  # take a width

_DENIED_BASES: tuple[type, ...] = (
    types.ModuleType, type, types.FunctionType, types.BuiltinFunctionType, types.MethodType, types.CodeType, types.FrameType,
    types.GeneratorType, types.TracebackType, types.CoroutineType, types.AsyncGeneratorType, types.MethodWrapperType,
    types.WrapperDescriptorType, types.MethodDescriptorType,
)
_PRIMITIVES = (str, int, float, bool, list, tuple, dict, set, frozenset, type(None))
#: The only things an expression iterates over, tests membership in, or hands to a function that iterates: an object with its own
#: `__iter__`, `keys` or `__contains__` would run application code the author never wrote.
_CONTAINERS = (str, list, tuple, dict, set, frozenset, range)
_PLAIN = (bool, int, float, str, type(None)) + _CONTAINERS
# Values that operators, truth tests, subscripts, formatting and the built-in functions may touch. Any other object is
# the application's own and may carry code in __add__, __eq__, __bool__, __len__, __getitem__ or __format__, so an
# expression can only read its attributes.
_INERT = _PLAIN + (Mapping, datetime.date, datetime.time, datetime.timedelta, decimal.Decimal, enum.Enum)

_BIN_OPS: dict[type, Callable[[Any, Any], Any]] = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod, ast.Pow: operator.pow,
}
_BIN_SYMBOLS = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/", ast.FloorDiv: "//", ast.Mod: "%", ast.Pow: "**"}
_CMP_OPS: dict[type, Callable[[Any, Any], bool]] = {
    ast.Eq: operator.eq, ast.NotEq: operator.ne, ast.Lt: operator.lt, ast.LtE: operator.le, ast.Gt: operator.gt, ast.GtE: operator.ge,
    ast.In: lambda a, b: a in b, ast.NotIn: lambda a, b: a not in b, ast.Is: operator.is_, ast.IsNot: operator.is_not,
}

_ALLOWED_NODES = (
    ast.Expression, ast.Constant, ast.Name, ast.Load, ast.Store, ast.Attribute, ast.Subscript, ast.Slice, ast.UnaryOp, ast.Not,
    ast.USub, ast.UAdd, ast.BinOp, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow, ast.BoolOp, ast.And, ast.Or,
    ast.Compare, ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.In, ast.NotIn, ast.Is, ast.IsNot, ast.IfExp,
    ast.JoinedStr, ast.FormattedValue, ast.List, ast.Tuple, ast.Set, ast.Dict, ast.ListComp, ast.DictComp, ast.SetComp,
    ast.GeneratorExp, ast.comprehension, ast.Call, ast.keyword, ast.Starred,
)
_NAMES_OF_DISALLOWED = {
    ast.Lambda: "a lambda", ast.NamedExpr: "an assignment expression (:=)", ast.Await: "await", ast.Yield: "yield",
    ast.YieldFrom: "yield", ast.BitAnd: "the operator &", ast.BitOr: "the operator |", ast.BitXor: "the operator ^",
    ast.LShift: "the operator <<", ast.RShift: "the operator >>", ast.MatMult: "the operator @", ast.Invert: "the operator ~",
}


# -- compiling ----------------------------------------------------------------------------------------------------------


class _Checker:
    """Walks a parsed tree once: every node type must be allowed, with the extra rules of section 8.1."""

    def __init__(self, source: str, origin: Optional[Origin], limits: Limits, mode: str) -> None:
        self.source, self.origin, self.limits, self.mode = source, origin, limits, mode
        self.names: set[str] = set()
        self.nodes = 0
        self._bound: list[set[str]] = []

    def error(self, node: ast.AST, message: str, hint: Optional[str] = None) -> ExprError:
        return _node_error(self.source, self.origin, node, message, hint)

    def check(self, node: ast.AST, depth: int = 1) -> None:
        self.nodes += 1
        if depth > self.limits.max_depth:
            raise self.error(node, f"the expression is nested more than {self.limits.max_depth} deep")
        if self.nodes > self.limits.max_nodes:
            raise self.error(node, f"the expression has more than {self.limits.max_nodes} parts")
        kind = type(node)
        if kind in _NAMES_OF_DISALLOWED:
            raise self.error(node, f"{_NAMES_OF_DISALLOWED[kind]} is not allowed in an expression")
        if not isinstance(node, _ALLOWED_NODES):
            raise self.error(node, f"{kind.__name__} is not allowed in an expression")
        handler = getattr(self, "check_" + kind.__name__, None)
        if handler is not None:
            handler(node, depth)
        else:
            for child in ast.iter_child_nodes(node):
                self.check(child, depth + 1)

    def check_Constant(self, node: ast.Constant, depth: int) -> None:
        if not (node.value is None or isinstance(node.value, (bool, int, float, str))):
            raise self.error(node, f"a {type(node.value).__name__} value is not allowed in an expression")

    def check_Name(self, node: ast.Name, depth: int) -> None:
        if node.id.startswith("_") and node.id != "_":
            raise self.error(node, f"the name '{node.id}' is private (names starting with _ are not visible)")
        if not any(node.id in frame for frame in self._bound):
            self.names.add(node.id)

    def check_Attribute(self, node: ast.Attribute, depth: int) -> None:
        if node.attr.startswith("_"):
            raise self.error(node, f"the attribute '{node.attr}' is private (attributes starting with _ are not allowed)")
        self.check(node.value, depth + 1)

    def check_Compare(self, node: ast.Compare, depth: int) -> None:
        for op, right in zip(node.ops, node.comparators):
            if isinstance(op, (ast.Is, ast.IsNot)) and not (isinstance(right, ast.Constant) and right.value in (None, True, False)
                                                           and (right.value is None or isinstance(right.value, bool))):
                raise self.error(node, "'is' only compares with None, True or False; use == for anything else")
        self.check(node.left, depth + 1)
        for right in node.comparators:
            self.check(right, depth + 1)

    def check_Dict(self, node: ast.Dict, depth: int) -> None:
        for key, value in zip(node.keys, node.values):
            if key is None:
                raise self.error(value, "'**' in a dict display is not allowed")
            self.check(key, depth + 1)
            self.check(value, depth + 1)

    def check_Call(self, node: ast.Call, depth: int) -> None:
        if not isinstance(node.func, (ast.Name, ast.Attribute)):
            raise self.error(node, "only a function or method can be called")
        for kw in node.keywords:
            if kw.arg is None:
                raise self.error(kw.value, "'**' in a call is not allowed")
        self.check(node.func, depth + 1)
        for arg in node.args:
            self.check(arg, depth + 1)
        for kw in node.keywords:
            self.check(kw.value, depth + 1)

    def _targets(self, target: ast.AST) -> set[str]:
        if isinstance(target, ast.Name):
            if target.id.startswith("_") and target.id != "_":
                raise self.error(target, f"the name '{target.id}' is private")
            return {target.id}
        if isinstance(target, (ast.Tuple, ast.List)):
            found: set[str] = set()
            for element in target.elts:
                found |= self._targets(element)
            return found
        raise self.error(target, "a loop variable must be a name (or names in a tuple)")

    def _comprehension(self, generators: list[ast.comprehension], parts: list[ast.AST], depth: int) -> None:
        frame: set[str] = set()
        self._bound.append(frame)
        try:
            for generator in generators:
                if generator.is_async:
                    raise self.error(generator.iter, "async comprehensions are not allowed")
                self.check(generator.iter, depth + 1)  # the first iterable sees the outer names, later ones the targets too
                frame |= self._targets(generator.target)
                for condition in generator.ifs:
                    self.check(condition, depth + 1)
            for part in parts:
                self.check(part, depth + 1)
        finally:
            self._bound.pop()

    def check_ListComp(self, node: ast.ListComp, depth: int) -> None:
        self._comprehension(node.generators, [node.elt], depth)

    def check_SetComp(self, node: ast.SetComp, depth: int) -> None:
        self._comprehension(node.generators, [node.elt], depth)

    def check_GeneratorExp(self, node: ast.GeneratorExp, depth: int) -> None:
        self._comprehension(node.generators, [node.elt], depth)

    def check_DictComp(self, node: ast.DictComp, depth: int) -> None:
        self._comprehension(node.generators, [node.key, node.value], depth)


def _node_error(source: str, origin: Optional[Origin], node: ast.AST, message: str, hint: Optional[str] = None) -> ExprError:
    line = getattr(node, "lineno", 1)
    column = getattr(node, "col_offset", 0)
    end = getattr(node, "end_col_offset", None) if getattr(node, "end_lineno", line) == line else None
    return ExprError(message, source=source, line=line, column=column, end_column=end, origin=origin, hint=hint)


def _strip(source: str, origin: Optional[Origin]) -> tuple[str, Optional[Origin]]:
    """The text without its surrounding whitespace, and the origin moved to where that text starts."""
    stripped = source.strip()
    if origin is None:
        return stripped, None
    lead = source[: len(source) - len(source.lstrip())]
    newlines = lead.count("\n")
    column = (len(lead) - lead.rfind("\n") - 1) if newlines else origin.column + len(lead)
    return stripped, Origin(origin.file, origin.line + newlines, column)


def _parse(stripped: str, mode: str, origin: Optional[Origin], limits: Limits) -> ast.AST:
    """The syntax tree of already stripped text."""
    if not stripped:
        raise ExprError("the expression is empty", source=stripped, origin=origin)
    if len(stripped) > limits.max_source:
        raise ExprError(f"the expression is {len(stripped)} characters; the limit is {limits.max_source}", source=stripped[:80], origin=origin)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            return ast.parse(stripped, mode=mode)
    except SyntaxError as exc:
        line = exc.lineno or 1
        column = max((exc.offset or 1) - 1, 0)
        raise ExprError(f"syntax error: {exc.msg}", source=stripped, line=line, column=column, origin=origin) from None
    except (RecursionError, MemoryError, ValueError) as exc:
        raise ExprError(f"cannot parse the expression ({type(exc).__name__}): too deeply nested or malformed", source=stripped[:80],
                        origin=origin) from None


@dataclass
class Expr:
    """A compiled expression. `names` are the free names it reads (comprehension variables excluded)."""

    source: str
    tree: ast.Expression
    names: frozenset[str]
    origin: Optional[Origin] = None
    limits: Limits = field(default=DEFAULT_LIMITS, repr=False)

    def is_reactive(self, scope: Any) -> bool:
        """Whether any name it reads is reactive in `scope` (conservative: a name that may hold a Signal counts)."""
        check = getattr(scope, "is_reactive", None)
        return bool(check) and any(check(name) for name in self.names)

    def evaluate(self, scope: Any) -> Any:
        """The value, with Signals read as their values. Raises `ExprError`."""
        evaluator = _Evaluator(scope, self.limits, self.source, self.origin, "expr")
        return evaluator.unwrap(evaluator.raw(self.tree.body))

    def evaluate_raw(self, scope: Any) -> Any:
        """The value without unwrapping a Signal or Computed it ends in (what a model property needs to write back)."""
        evaluator = _Evaluator(scope, self.limits, self.source, self.origin, "expr")
        return evaluator.raw(self.tree.body)

    def bare_name(self) -> Optional[str]:
        """The name, if the whole expression is one bare name (a candidate for two-way binding), else `None`."""
        body = self.tree.body
        return body.id if isinstance(body, ast.Name) else None


def compile_expr(source: str, *, origin: Optional[Origin] = None, limits: Limits = DEFAULT_LIMITS) -> Expr:
    """Parses and checks one expression. Raises `ExprError`."""
    if not isinstance(source, str):
        raise ExprError(f"an expression is text, got {type(source).__name__}", origin=origin)
    text, origin = _strip(source, origin)
    tree = _parse(text, "eval", origin, limits)
    checker = _Checker(text, origin, limits, "expr")
    checker.check(tree)
    return Expr(text, tree, frozenset(checker.names), origin, limits)


# -- statements (handlers) ----------------------------------------------------------------------------------------------

_NAME_PATH = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*$")


def is_action_name(text: str) -> bool:
    """Whether a handler's text is just a (dotted) name, such as `save` or `navigate.back`, rather than statements."""
    return bool(_NAME_PATH.match(text.strip()))


@dataclass
class Statements:
    """A compiled handler: assignments and calls separated by `;` or newlines (section 9.1)."""

    source: str
    body: list[ast.stmt]
    names: frozenset[str]
    origin: Optional[Origin] = None
    limits: Limits = field(default=DEFAULT_LIMITS, repr=False)

    def run(self, scope: Any, *, event: Any = None) -> None:
        """Runs the statements in order against `scope` (assignments through `scope.assign`, calls through the scope's actions
        and the whitelisted functions); `event` is readable as `event`. The step budget covers all of them."""
        evaluator = _Evaluator(scope, self.limits, self.source, self.origin, "handler", event=event)
        for statement in self.body:
            evaluator.run_statement(statement)


def compile_statements(source: str, *, origin: Optional[Origin] = None, limits: Limits = DEFAULT_LIMITS) -> Statements:
    """Parses and checks a handler's statements. Raises `ExprError`."""
    if not isinstance(source, str):
        raise ExprError(f"a handler is text, got {type(source).__name__}", origin=origin)
    text, origin = _strip(source, origin)
    tree = _parse(text, "exec", origin, limits)
    checker = _Checker(text, origin, limits, "handler")
    names: set[str] = set()
    assert isinstance(tree, ast.Module)
    for statement in tree.body:
        if isinstance(statement, ast.Assign):
            if len(statement.targets) != 1 or not isinstance(statement.targets[0], ast.Name):
                raise checker.error(statement, "assign to one name: `name = expression`")
            _private_target(checker, statement.targets[0])
            names.add(statement.targets[0].id)
            checker.check(statement.value)
        elif isinstance(statement, ast.AugAssign):
            if not isinstance(statement.target, ast.Name):
                raise checker.error(statement, "assign to a name: `name += expression`")
            if type(statement.op) not in _BIN_OPS:
                raise checker.error(statement, f"{type(statement.op).__name__} is not allowed here (use + - * / // % **)")
            _private_target(checker, statement.target)
            names.add(statement.target.id)
            checker.check(statement.value)
        elif isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call):
            checker.check(statement.value)
        else:
            raise checker.error(statement, f"'{_statement_name(statement)}' is not available in a handler (an assignment or a call only)",
                                "if, for, del, return and the rest are reserved")
    return Statements(text, tree.body, frozenset(checker.names | names), origin, limits)


#: The calls whose second argument is a handler of its own, run later: `after(ms, "statements")`, `every(ms, "statements")`.
TIMER_CALLS = frozenset({"after", "every"})


def timer_handlers(statements: "Statements") -> list[str]:
    """The handler texts written as literals in the statements' calls to `after` and `every`, so a mistake in one is found when the view loads."""
    found: list[str] = []
    for statement in statements.body:
        for node in ast.walk(statement):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in TIMER_CALLS and len(node.args) >= 2
                    and isinstance(node.args[1], ast.Constant) and isinstance(node.args[1].value, str)):
                found.append(node.args[1].value)
    return found


def _private_target(checker: _Checker, target: ast.Name) -> None:
    if target.id.startswith("_"):
        raise checker.error(target, f"the name '{target.id}' is private")


def _statement_name(statement: ast.stmt) -> str:
    return {ast.If: "if", ast.For: "for", ast.While: "while", ast.Delete: "del", ast.Return: "return", ast.Import: "import",
            ast.ImportFrom: "import", ast.FunctionDef: "def", ast.ClassDef: "class", ast.With: "with", ast.Try: "try",
            ast.Raise: "raise", ast.Assert: "assert", ast.Global: "global", ast.Nonlocal: "nonlocal", ast.AnnAssign: "an annotated assignment",
            ast.Pass: "pass", ast.Break: "break", ast.Continue: "continue", ast.Expr: "an expression statement"}.get(type(statement), type(statement).__name__)


# -- templates ----------------------------------------------------------------------------------------------------------


@dataclass
class Template:
    """Text with `{{ }}` parts: `"Hello {{ name }}!"`. `parts` are strings and `Expr`s. When the whole text is one `{{ }}`, the
    value keeps its own type (`single`); otherwise the parts are joined as text (`None` is empty)."""

    parts: list[Any]

    @property
    def single(self) -> bool:
        return len(self.parts) == 1 and isinstance(self.parts[0], Expr)

    @property
    def names(self) -> frozenset[str]:
        return frozenset().union(*(p.names for p in self.parts if isinstance(p, Expr)))

    def is_reactive(self, scope: Any) -> bool:
        return any(p.is_reactive(scope) for p in self.parts if isinstance(p, Expr))

    def evaluate(self, scope: Any) -> Any:
        if self.single:
            return self.parts[0].evaluate(scope)
        out = []
        for part in self.parts:
            if isinstance(part, Expr):
                value = part.evaluate(scope)
                out.append("" if value is None else _text(value))
            else:
                out.append(part)
        return "".join(out)


def _text(value: Any) -> str:
    return str(value)


def compile_template(text: str, *, origin: Optional[Origin] = None, limits: Limits = DEFAULT_LIMITS) -> Optional[Template]:
    """Splits `text` at its `{{ }}` parts and compiles each. Returns `None` when there is no `{{` (plain text). A `}}` inside a
    string or a bracket belongs to the expression, so `{{ {'a': 1}['a'] }}` works. Raises `ExprError`."""
    if "{{" not in text:
        return None
    parts: list[Any] = []
    i, n, literal_start = 0, len(text), 0
    while i < n:
        if text.startswith("{{", i):
            if literal_start < i:
                parts.append(text[literal_start:i])
            end = _closing(text, i + 2)
            if end is None:
                line, column = _line_col(text, i)
                raise ExprError("a '{{' is never closed with '}}'", source=text.splitlines()[line - 1] if text else "", line=line, column=column,
                                origin=origin)
            inner = text[i + 2:end]
            line, column = _line_col(text, i + 2)
            at = Origin(origin.file, origin.line + line - 1, origin.column + column if line == 1 else column) if origin else None
            parts.append(compile_expr(inner, origin=at, limits=limits))
            i = literal_start = end + 2
        else:
            i += 1
    if literal_start < n:
        parts.append(text[literal_start:])
    return Template(parts)


def _line_col(text: str, index: int) -> tuple[int, int]:
    before = text[:index]
    line = before.count("\n") + 1
    return line, index - (before.rfind("\n") + 1)


def _closing(text: str, start: int) -> Optional[int]:
    """The index of the `}}` that closes a `{{` whose inside starts at `start`, skipping strings and balanced brackets."""
    depth, quote, i, n = 0, "", start, len(text)
    while i < n:
        c = text[i]
        if quote:
            if c == "\\":
                i += 2
                continue
            if c == quote:
                quote = ""
        elif c in "'\"":
            quote = c
        elif c in "([{":
            depth += 1
        elif c in ")]":
            depth -= 1
        elif c == "}":
            if depth == 0 and text.startswith("}}", i):
                return i
            depth -= 1
        i += 1
    return None


# -- evaluating ---------------------------------------------------------------------------------------------------------


class _Evaluator:
    """Runs one compiled expression or handler against a scope, counting steps."""

    def __init__(self, scope: Any, limits: Limits, source: str, origin: Optional[Origin], mode: str, *, event: Any = None) -> None:
        self.scope, self.limits, self.source, self.origin, self.mode, self.event = scope, limits, source, origin, mode, event
        self.steps = 0
        self.frames: list[dict[str, Any]] = []

    # errors and budget ----------------------------------------------------------------------------------------------

    def error(self, node: ast.AST, message: str, hint: Optional[str] = None) -> ExprError:
        return _node_error(self.source, self.origin, node, message, hint)

    def tick(self, node: ast.AST, count: int = 1) -> None:
        self.steps += count
        if self.steps > self.limits.max_steps:
            raise self.error(node, f"the expression is too expensive to evaluate (over {self.limits.max_steps} steps)")

    def unwrap(self, value: Any) -> Any:
        return value.get() if isinstance(value, (Signal, Computed)) else value

    def value(self, node: ast.AST) -> Any:
        return self.unwrap(self.raw(node))

    # dispatch -------------------------------------------------------------------------------------------------------

    def raw(self, node: ast.AST) -> Any:
        self.tick(node)
        method = getattr(self, "eval_" + type(node).__name__, None)
        if method is None:  # the checker allows nothing else; defence in depth
            raise self.error(node, f"{type(node).__name__} cannot be evaluated")
        try:
            return method(node)
        except ExprError:
            raise
        except RecursionError:
            raise self.error(node, "the expression is nested too deeply") from None
        except ZeroDivisionError:
            raise self.error(node, "division by zero") from None
        except OverflowError:
            raise self.error(node, "the number is too large") from None
        except Exception as exc:  # noqa: BLE001 - any failure of an operation is the expression's error
            raise self.error(node, f"{type(exc).__name__}: {exc}") from None

    # leaves ---------------------------------------------------------------------------------------------------------

    def eval_Constant(self, node: ast.Constant) -> Any:
        return node.value

    def eval_Name(self, node: ast.Name) -> Any:
        name = node.id
        for frame in reversed(self.frames):
            if name in frame:
                return frame[name]
        if name == "event" and self.mode == "handler":
            return self.event
        try:
            return self.scope.lookup(name)
        except (KeyError, AttributeError):
            pass
        if name in BUILTIN_FUNCTIONS:
            return BUILTIN_FUNCTIONS[name]
        known = [n for f in self.frames for n in f] + _scope_names(self.scope) + list(BUILTIN_FUNCTIONS)
        close = difflib.get_close_matches(name, known, n=3)
        raise self.error(node, f"'{name}' is not defined", ("did you mean " + " or ".join(f"'{c}'" for c in close)) if close else None)

    # attributes and indexing ----------------------------------------------------------------------------------------

    def _denied(self, node: ast.AST, base: Any, what: str) -> ExprError:
        return self.error(node, f"cannot {what} of {type(base).__name__}")

    def eval_Attribute(self, node: ast.Attribute) -> Any:
        base = self.value(node.value)
        name = node.attr
        if isinstance(base, Mapping):
            if name in base:
                return base[name]
            close = difflib.get_close_matches(name, [str(k) for k in base], n=3)
            raise self.error(node, f"no key '{name}'", ("did you mean " + " or ".join(f"'{c}'" for c in close)) if close else None)
        if isinstance(base, _DENIED_BASES):
            raise self._denied(node, base, f"read '{name}'")
        if isinstance(base, _PRIMITIVES):
            for kind, methods in _METHODS_BY_TYPE:
                if isinstance(base, kind) and name in methods:
                    raise self.error(node, f"'{name}' is a method: call it, as {name}()")
            raise self.error(node, f"{type(base).__name__} has no readable attribute '{name}'")
        exposed = getattr(type(base), "__expose__", None)
        if exposed is not None and name not in exposed:
            raise self.error(node, f"'{name}' is not exposed by {type(base).__name__}", f"exposed: {', '.join(exposed)}")
        try:
            value = getattr(base, name)
        except AttributeError:
            public = [a for a in dir(base) if not a.startswith("_")]
            close = difflib.get_close_matches(name, public, n=3)
            raise self.error(node, f"{type(base).__name__} has no attribute '{name}'",
                             ("did you mean " + " or ".join(f"'{c}'" for c in close)) if close else None) from None
        if callable(value) and not isinstance(value, (Signal, Computed)):
            raise self.error(node, f"'{name}' is a method of {type(base).__name__}: it cannot be read as a value")
        return value

    def inert(self, value: Any, node: ast.AST, use: str) -> Any:
        if not isinstance(value, _INERT):
            raise self.error(node, f"a {type(value).__name__} cannot be used {use}", "read one of its attributes instead")
        return value

    def truth(self, value: Any) -> bool:
        return bool(value) if isinstance(value, _INERT) else True

    def eval_Subscript(self, node: ast.Subscript) -> Any:
        base = self.value(node.value)
        if isinstance(base, _DENIED_BASES):
            raise self._denied(node, base, "index")
        self.inert(base, node, "with [ ]")
        if isinstance(node.slice, ast.Slice):
            index = slice(*(None if p is None else self.value(p) for p in (node.slice.lower, node.slice.upper, node.slice.step)))
        else:
            index = self.value(node.slice)
        self.tick(node, 1)
        return base[index]

    # operators ------------------------------------------------------------------------------------------------------

    def eval_UnaryOp(self, node: ast.UnaryOp) -> Any:
        operand = self.value(node.operand)
        if isinstance(node.op, ast.Not):
            return not self.truth(operand)
        self.inert(operand, node, "with a sign")
        return -operand if isinstance(node.op, ast.USub) else +operand

    def eval_BinOp(self, node: ast.BinOp) -> Any:
        left, right = self.value(node.left), self.value(node.right)
        self.inert(left, node, "in arithmetic")
        self.inert(right, node, "in arithmetic")
        op = type(node.op)
        if op is ast.Mod and isinstance(left, str):
            raise self.error(node, "'%' formatting is not available", "use an f-string")
        lim = self.limits
        if op is ast.Pow:
            if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                if abs(right) > lim.max_pow_exponent:
                    raise self.error(node, f"the exponent is over {lim.max_pow_exponent}")
                if left not in (0, 1, -1) and abs(right) * math.log2(abs(left) or 1) > lim.max_int_bits:
                    raise self.error(node, "the result of ** is too large")
        elif op is ast.Mult:
            for seq, count in ((left, right), (right, left)):
                if isinstance(seq, (str, list, tuple)) and isinstance(count, int) and not isinstance(count, bool):
                    if len(seq) * max(count, 0) > lim.max_sequence:
                        raise self.error(node, f"the repeated sequence would have over {lim.max_sequence} items")
        elif op is ast.Add and isinstance(left, (str, list, tuple)) and type(left) is type(right):
            if len(left) + len(right) > lim.max_sequence:
                raise self.error(node, f"the joined sequence would have over {lim.max_sequence} items")
        try:
            result = _BIN_OPS[op](left, right)
        except TypeError:
            raise self.error(node, f"cannot use {_BIN_SYMBOLS[op]} on {type(left).__name__} and {type(right).__name__}") from None
        if isinstance(result, int) and not isinstance(result, bool) and result.bit_length() > lim.max_int_bits:
            raise self.error(node, "the number is too large")
        if isinstance(result, str) and len(result) > lim.max_string:
            raise self.error(node, f"the text would be over {lim.max_string} characters")
        return result

    def eval_BoolOp(self, node: ast.BoolOp) -> Any:
        result: Any = None
        for index, operand in enumerate(node.values):
            result = self.value(operand)
            if isinstance(node.op, ast.And) and not self.truth(result):
                return result
            if isinstance(node.op, ast.Or) and self.truth(result):
                return result
        return result

    def eval_Compare(self, node: ast.Compare) -> Any:
        left = self.value(node.left)
        for op, comparator in zip(node.ops, node.comparators):
            right = self.value(comparator)
            self.tick(node, 1)
            if not isinstance(op, (ast.Is, ast.IsNot)):
                self.inert(left, node, "in a comparison")
                self.inert(right, node, "in a comparison")
            if isinstance(op, (ast.In, ast.NotIn)) and not isinstance(right, _CONTAINERS) and not isinstance(right, Mapping):
                raise self.error(node, f"cannot test membership in a {type(right).__name__}", "a list, tuple, dict, set, text or range")
            try:
                if not _CMP_OPS[type(op)](left, right):
                    return False
            except TypeError:
                raise self.error(node, f"cannot compare {type(left).__name__} and {type(right).__name__}") from None
            left = right
        return True

    def eval_IfExp(self, node: ast.IfExp) -> Any:
        return self.value(node.body) if self.truth(self.value(node.test)) else self.value(node.orelse)

    # displays -------------------------------------------------------------------------------------------------------

    def _elements(self, nodes: list[ast.expr]) -> list[Any]:
        out: list[Any] = []
        for element in nodes:
            if isinstance(element, ast.Starred):
                out.extend(self.bounded(self.value(element.value), element))
            else:
                out.append(self.value(element))
        return out

    def eval_List(self, node: ast.List) -> Any:
        return self._elements(node.elts)

    def eval_Tuple(self, node: ast.Tuple) -> Any:
        return tuple(self._elements(node.elts))

    def eval_Set(self, node: ast.Set) -> Any:
        return set(self._elements(node.elts))

    def eval_Dict(self, node: ast.Dict) -> Any:
        return {self.value(k): self.value(v) for k, v in zip(node.keys, node.values) if k is not None}

    def eval_JoinedStr(self, node: ast.JoinedStr) -> Any:
        out: list[str] = []
        for part in node.values:
            if isinstance(part, ast.Constant):
                out.append(str(part.value))
            else:
                out.append(self._formatted(part))
            if sum(map(len, out)) > self.limits.max_string:
                raise self.error(node, f"the text would be over {self.limits.max_string} characters")
        return "".join(out)

    def _formatted(self, node: ast.FormattedValue) -> str:
        value = self.inert(self.value(node.value), node, "in text")
        if node.conversion == 115:
            value = str(value)
        elif node.conversion == 114:
            value = repr(value)
        elif node.conversion == 97:
            value = ascii(value)
        spec = self.eval_JoinedStr(node.format_spec) if node.format_spec is not None else ""
        return format(value, spec)

    def eval_FormattedValue(self, node: ast.FormattedValue) -> Any:
        return self._formatted(node)

    # comprehensions -------------------------------------------------------------------------------------------------

    def bounded(self, iterable: Any, node: ast.AST) -> list[Any]:
        """The items of `iterable` as a list, charged to the step budget and capped. Only the built-in containers are iterated."""
        if not isinstance(iterable, _CONTAINERS) and not isinstance(iterable, Mapping):
            raise self.error(node, f"cannot iterate over a {type(iterable).__name__}", "a list, tuple, dict, set, text or range")
        count = len(iterable)
        self.tick(node, count)
        if count > self.limits.max_sequence:
            raise self.error(node, f"over {self.limits.max_sequence} items")
        return list(iterable)

    def _bind(self, target: ast.AST, value: Any, frame: dict[str, Any], node: ast.AST) -> None:
        if isinstance(target, ast.Name):
            frame[target.id] = value
            return
        items = self.bounded(value, node)
        if len(items) != len(target.elts):  # type: ignore[attr-defined]
            raise self.error(node, f"cannot unpack {len(items)} values into {len(target.elts)} names")  # type: ignore[attr-defined]
        for sub, item in zip(target.elts, items):  # type: ignore[attr-defined]
            self._bind(sub, item, frame, node)

    def _run_generators(self, generators: list[ast.comprehension], index: int, emit: Callable[[], None]) -> None:
        if index == len(generators):
            emit()
            return
        generator = generators[index]
        frame = self.frames[-1]
        for item in self.bounded(self.value(generator.iter), generator.iter):
            self.tick(generator.iter, 1)
            self._bind(generator.target, item, frame, generator.iter)
            if all(self.truth(self.value(condition)) for condition in generator.ifs):
                self._run_generators(generators, index + 1, emit)

    def eval_ListComp(self, node: ast.ListComp) -> Any:
        out: list[Any] = []
        self.frames.append({})
        try:
            self._run_generators(node.generators, 0, lambda: out.append(self.value(node.elt)))
        finally:
            self.frames.pop()
        return out

    def eval_GeneratorExp(self, node: ast.GeneratorExp) -> Any:
        out: list[Any] = []
        self.frames.append({})
        try:
            self._run_generators(node.generators, 0, lambda: out.append(self.value(node.elt)))
        finally:
            self.frames.pop()
        return out

    def eval_SetComp(self, node: ast.SetComp) -> Any:
        out: set[Any] = set()
        self.frames.append({})
        try:
            self._run_generators(node.generators, 0, lambda: out.add(self.value(node.elt)))
        finally:
            self.frames.pop()
        return out

    def eval_DictComp(self, node: ast.DictComp) -> Any:
        out: dict[Any, Any] = {}
        self.frames.append({})
        try:
            self._run_generators(node.generators, 0, lambda: out.__setitem__(self.value(node.key), self.value(node.value)))
        finally:
            self.frames.pop()
        return out

    # calls ----------------------------------------------------------------------------------------------------------

    def _arguments(self, node: ast.Call) -> tuple[list[Any], dict[str, Any]]:
        args: list[Any] = []
        for arg in node.args:
            if isinstance(arg, ast.Starred):
                args.extend(self.bounded(self.value(arg.value), arg))
            else:
                args.append(self.value(arg))
        return args, {kw.arg: self.value(kw.value) for kw in node.keywords if kw.arg is not None}

    @staticmethod
    def _dotted(node: ast.AST) -> Optional[str]:
        parts: list[str] = []
        while isinstance(node, ast.Attribute):
            parts.append(node.attr)
            node = node.value
        if isinstance(node, ast.Name):
            parts.append(node.id)
            return ".".join(reversed(parts))
        return None

    def eval_Call(self, node: ast.Call) -> Any:
        func = node.func
        path = self._dotted(func)
        if self.mode == "handler" and path is not None:
            is_action = getattr(self.scope, "is_action", None)
            local = isinstance(func, ast.Name) and any(func.id in frame for frame in self.frames)
            if is_action is not None and not local and is_action(path):
                args, kwargs = self._arguments(node)
                try:
                    return self.scope.call_action(path, args, kwargs)
                except ExprError:
                    raise
                except Exception as exc:  # noqa: BLE001 - a handler's own failure
                    raise self.error(node, f"{path}() failed: {type(exc).__name__}: {exc}") from None
        if isinstance(func, ast.Name):
            return self._call_builtin(node, func.id)
        assert isinstance(func, ast.Attribute)
        return self._call_method(node, func)

    def _call_builtin(self, node: ast.Call, name: str) -> Any:
        if any(name in frame for frame in self.frames) or name not in BUILTIN_FUNCTIONS:
            allowed = ", ".join(sorted(BUILTIN_FUNCTIONS))
            raise self.error(node, f"'{name}' is not a function you can call here", f"allowed: {allowed}")
        args, kwargs = self._arguments(node)
        lim = self.limits
        if name == "range":
            if not args or not all(isinstance(a, int) and not isinstance(a, bool) for a in args) or kwargs:
                raise self.error(node, "range() takes whole numbers")
            result = range(*args)
            if len(result) > lim.max_range:
                raise self.error(node, f"the range has {len(result)} items; the limit is {lim.max_range}")
            return result
        if name == "isinstance":
            if len(args) != 2 or not isinstance(node.args[1], ast.Name) or node.args[1].id not in _ISINSTANCE_TYPES:
                raise self.error(node, f"isinstance() compares with one of: {', '.join(_ISINSTANCE_TYPES)}")
            return isinstance(args[0], _ISINSTANCE_TYPES[node.args[1].id])
        for value in [*args, *kwargs.values()]:
            if name != "isinstance" and not isinstance(value, _INERT):
                raise self.error(node, f"{name}() takes lists, tuples, dicts, sets, text, ranges and plain values, not a {type(value).__name__}")
        if name in _ITERATING:
            args = [self.bounded(a, node) if isinstance(a, _CONTAINERS) or isinstance(a, Mapping) else a for a in args]
        self.tick(node, 1)
        result = BUILTIN_FUNCTIONS[name](*args, **kwargs)
        if isinstance(result, str) and len(result) > lim.max_string:
            raise self.error(node, f"the text would be over {lim.max_string} characters")
        if isinstance(result, int) and not isinstance(result, bool) and result.bit_length() > lim.max_int_bits:
            raise self.error(node, "the number is too large")
        return result

    def _call_method(self, node: ast.Call, func: ast.Attribute) -> Any:
        name = func.attr
        base_raw = self.raw(func.value)
        if isinstance(base_raw, (Signal, Computed)) and name == "get" and not node.args and not node.keywords:
            return base_raw.get()
        base = self.unwrap(base_raw)
        for kind, methods in _METHODS_BY_TYPE:
            if isinstance(base, kind):
                if name not in methods:
                    raise self.error(node, f"{kind.__name__}.{name}() is not available", f"allowed: {', '.join(sorted(methods))}")
                args, kwargs = self._arguments(node)
                lim = self.limits
                if name in _SEQUENCE_BUILDING and args and isinstance(args[0], int) and args[0] > lim.max_string:
                    raise self.error(node, f"the width is over {lim.max_string}")
                if name == "join" and args:
                    args = [self.bounded(args[0], node)]
                self.tick(node, 1)
                result = getattr(base, name)(*args, **kwargs)
                if isinstance(result, _DICT_VIEWS):
                    result = list(result)
                if isinstance(result, str) and len(result) > lim.max_string:
                    raise self.error(node, f"the text would be over {lim.max_string} characters")
                return result
        raise self.error(node, f"cannot call .{name}() on a {type(base).__name__}",
                         "an expression may call the built-in functions and the methods of text, lists and dicts")

    # statements -----------------------------------------------------------------------------------------------------

    def run_statement(self, statement: ast.stmt) -> None:
        self.tick(statement)
        if isinstance(statement, ast.Assign):
            name = statement.targets[0].id  # type: ignore[attr-defined]
            self._assign(statement, name, self.value(statement.value))
        elif isinstance(statement, ast.AugAssign):
            name = statement.target.id  # type: ignore[attr-defined]
            synthetic = ast.BinOp(left=ast.Name(id=name, ctx=ast.Load()), op=statement.op, right=statement.value)
            ast.copy_location(synthetic, statement)
            ast.fix_missing_locations(synthetic)
            self._assign(statement, name, self.value(synthetic))
        elif isinstance(statement, ast.Expr):
            self.raw(statement.value)

    def _assign(self, node: ast.AST, name: str, value: Any) -> None:
        assign = getattr(self.scope, "assign", None)
        if assign is None:
            raise self.error(node, f"'{name}' is not writable")
        try:
            assign(name, value)
        except KeyError:
            raise self.error(node, f"'{name}' is not writable", "assign only local state and Signals") from None
        except ExprError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise self.error(node, f"assigning '{name}' failed: {type(exc).__name__}: {exc}") from None
