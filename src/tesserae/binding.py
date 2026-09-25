"""Tesserae's `{{ }}` binding expressions (M36): a port of `tre`'s
`engine-spec/src/binding.rs` and `engine-py/src/binding.rs` at v0.3.4,
which `tre` removes in 0.3.5 (its M98).

The grammar is a small whitelist and never uses `eval`:

- names (`clicks`), attributes (`user.name`), indexing (`items[0]`),
  and zero-argument method calls (`clicks.get()`) -- a call only as a
  method on something, never a bare `f()`;
- `+ - * /`, comparisons (`== != < <= > >=`), `and`, `or`, `not`,
  parentheses;
- literals: integers, floats (`1.5`), strings in `"..."` or `'...'` (no
  escapes), `True`, `False`. There is no unary minus and no `None`.

Evaluation matches `tre`'s exactly, quirks included, so every existing
view means the same thing:

- A Python value is used as a *primitive* when it is one: `bool`, then
  an `int` that fits in 64 bits (or anything with `__index__`), then
  anything `float()` accepts, then `str`. Anything else (a `Signal`, a
  list, an object) is an opaque *handle*.
- Arithmetic and comparison on two primitives follow `tre`'s own rules,
  not Python's: `-`, `*` and the ordering comparisons need both sides the
  same type (int with int, float with float); `+` also mixes int and
  float, and joins two strings; `int / int` is a float, and dividing an
  int by zero is an error while a float gives `inf`/`nan`; `==` is false
  across types (`1 == 1.0` is `False`); int arithmetic wraps at 64 bits.
  Anything else is an "unsupported operation" error.
- As soon as either side is a handle, Python's own operator decides.
- `and`/`or` short-circuit and return an operand, as in Python; `not`
  returns a `bool`.

Error messages match `tre`'s text, so errors read the same.
"""

from __future__ import annotations

import math
import operator
from dataclasses import dataclass
from typing import Any, Union

__all__ = ["BindingError", "Expression", "Handle", "evaluate", "parse_binding", "value_debug"]


class BindingError(ValueError):
    """A binding that doesn't parse, or fails to evaluate. The message is
    `tre`'s."""


# -- values -----------------------------------------------------------------


@dataclass(eq=False)
class Handle:
    """An opaque Python object inside an evaluation. `id` numbers the
    handles one evaluation made, in order, as `tre` does."""

    obj: Any
    id: int


Value = Union[bool, int, float, str, Handle]
_I64_MIN, _I64_MAX = -(2**63), 2**63 - 1


class _Resolver:
    """Resolves names against one ViewModel, for one evaluation."""

    def __init__(self, viewmodel: Any) -> None:
        self._viewmodel = viewmodel
        self._handles: list[Handle] = []

    def to_value(self, obj: Any) -> Value:
        # The order and acceptance of pyo3's extract::<bool/i64/f64/String>.
        if isinstance(obj, bool):
            return obj
        if not isinstance(obj, (str, float)) and hasattr(type(obj), "__index__"):
            try:
                n = operator.index(obj)
            except Exception:
                n = None
            if n is not None and _I64_MIN <= n <= _I64_MAX:
                return int(n)
        if not isinstance(obj, str):
            try:
                return float(obj) if not isinstance(obj, float) else obj
            except Exception:
                pass
        if isinstance(obj, str):
            return str(obj)
        handle = Handle(obj, len(self._handles))
        self._handles.append(handle)
        return handle

    @staticmethod
    def to_python(value: Value) -> Any:
        return value.obj if isinstance(value, Handle) else value

    def ident(self, name: str) -> Value:
        return self.to_value(_py(lambda: getattr(self._viewmodel, name)))

    def attr(self, base: Value, name: str) -> Value:
        obj = self.to_python(base)
        return self.to_value(_py(lambda: getattr(obj, name)))

    def index(self, base: Value, index: Value) -> Value:
        obj, idx = self.to_python(base), self.to_python(index)
        return self.to_value(_py(lambda: obj[idx]))

    def call(self, base: Value, method: str) -> Value:
        obj = self.to_python(base)
        return self.to_value(_py(lambda: getattr(obj, method)()))

    def binary_op(self, op: str, left: Value, right: Value) -> Value:
        l, r = self.to_python(left), self.to_python(right)
        fn = _PY_OPS[op]
        result = _py(lambda: fn(l, r))
        if op in _COMPARISONS:
            return bool(_py(lambda: bool(result)))
        return self.to_value(result)

    def truthy(self, value: Value) -> bool:
        obj = self.to_python(value)
        return bool(_py(lambda: bool(obj)))


def _py(fn: Any) -> Any:
    try:
        return fn()
    except Exception as exc:
        raise BindingError(f"{type(exc).__name__}: {exc}") from exc


_PY_OPS = {
    "Add": operator.add, "Sub": operator.sub, "Mul": operator.mul, "Div": operator.truediv,
    "Eq": operator.eq, "Ne": operator.ne, "Lt": operator.lt, "Le": operator.le,
    "Gt": operator.gt, "Ge": operator.ge,
}
_COMPARISONS = {"Eq", "Ne", "Lt", "Le", "Gt", "Ge"}


def _float_debug(f: float) -> str:
    """Rust's `{:?}` for an `f64`."""
    if math.isnan(f):
        return "NaN"
    if math.isinf(f):
        return "inf" if f > 0 else "-inf"
    text = repr(f)
    if "e" in text:
        mantissa, exp = text.split("e")
        return f"{mantissa}e{int(exp)}"
    return text


def _str_debug(s: str) -> str:
    """Rust's `{:?}` for a `String`, for the characters views use."""
    out = []
    for ch in s:
        if ch in '"\\':
            out.append("\\" + ch)
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\t":
            out.append("\\t")
        elif ch == "\r":
            out.append("\\r")
        elif ord(ch) < 0x20 or ord(ch) == 0x7F:
            out.append(f"\\u{{{ord(ch):x}}}")
        else:
            out.append(ch)
    return '"' + "".join(out) + '"'


def value_debug(value: Value) -> str:
    """A value as `tre` prints it (`Int(3)`, `Str("a")`, `Handle(0)`)."""
    if isinstance(value, bool):
        return f"Bool({'true' if value else 'false'})"
    if isinstance(value, int):
        return f"Int({value})"
    if isinstance(value, float):
        return f"Float({_float_debug(value)})"
    if isinstance(value, str):
        return f"Str({_str_debug(value)})"
    return f"Handle({value.id})"


# -- the AST ------------------------------------------------------------------


@dataclass(frozen=True)
class Expression:
    """One node: `kind` is `Ident`, `Literal`, `Attr`, `Index`, `Call`,
    `Not` or `BinaryOp`."""

    kind: str
    value: Any = None      # Ident/Attr/Call: a name; Literal: the value; BinaryOp: the op
    left: Any = None       # the base / operand / left side
    right: Any = None      # Index: the index; BinaryOp: the right side


# -- lexer ----------------------------------------------------------------------


@dataclass(frozen=True)
class _Token:
    kind: str
    value: Any = None

    def debug(self) -> str:
        if self.kind == "Ident":
            return f"Ident({_str_debug(self.value)})"
        if self.kind == "Int":
            return f"Int({self.value})"
        if self.kind == "Float":
            return f"Float({_float_debug(self.value)})"
        if self.kind == "Str":
            return f"Str({_str_debug(self.value)})"
        return self.kind


def _opt_debug(token: _Token | None) -> str:
    return "None" if token is None else f"Some({token.debug()})"


_KEYWORDS = {"and": "And", "or": "Or", "not": "Not", "True": "True", "False": "False"}
_TWO = {"==": "Eq", "!=": "Ne", "<=": "Le", ">=": "Ge"}
_ONE = {".": "Dot", ",": "Comma", "(": "LParen", ")": "RParen", "[": "LBracket", "]": "RBracket",
        "+": "Plus", "-": "Minus", "*": "Star", "/": "Slash", "<": "Lt", ">": "Gt"}


def _char_debug(c: str) -> str:
    """Rust's `{:?}` for a `char`."""
    if c == "'":
        return "'\\''"
    if c == "\\":
        return "'\\\\'"
    return f"'{c}'"


def _lex(text: str) -> list[_Token]:
    tokens: list[_Token] = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c.isspace():
            i += 1
        elif "0" <= c <= "9":
            start = i
            while i < n and ("0" <= text[i] <= "9" or text[i] == "."):
                i += 1
            word = text[start:i]
            if "." in word:
                try:
                    tokens.append(_Token("Float", float(word)))
                except ValueError:
                    raise BindingError(f"invalid number {_str_debug(word)}") from None
            else:
                value = int(word)
                if value > _I64_MAX:
                    raise BindingError(f"invalid number {_str_debug(word)}")
                tokens.append(_Token("Int", value))
        elif c.isalpha() or c == "_":
            start = i
            while i < n and (text[i].isalnum() or text[i] == "_"):
                i += 1
            word = text[start:i]
            tokens.append(_Token(_KEYWORDS[word]) if word in _KEYWORDS else _Token("Ident", word))
        elif c in "\"'":
            end = text.find(c, i + 1)
            if end < 0:
                raise BindingError("unterminated string literal")
            tokens.append(_Token("Str", text[i + 1:end]))
            i = end + 1
        elif text[i:i + 2] in _TWO:
            tokens.append(_Token(_TWO[text[i:i + 2]]))
            i += 2
        elif c in _ONE:
            tokens.append(_Token(_ONE[c]))
            i += 1
        else:
            raise BindingError(f"unexpected character {_char_debug(c)}")
    return tokens


# -- parser ----------------------------------------------------------------------


class _Parser:
    def __init__(self, tokens: list[_Token]) -> None:
        self.tokens, self.pos = tokens, 0

    def peek(self) -> _Token | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def peek_kind(self) -> str | None:
        token = self.peek()
        return token.kind if token else None

    def advance(self) -> _Token | None:
        token = self.peek()
        self.pos += 1
        return token

    def expect(self, kind: str) -> None:
        token = self.advance()
        if token is None or token.kind != kind:
            raise BindingError(f"expected {kind}, got {_opt_debug(token)}")

    def parse_or(self) -> Expression:
        left = self.parse_and()
        while self.peek_kind() == "Or":
            self.advance()
            left = Expression("BinaryOp", "Or", left, self.parse_and())
        return left

    def parse_and(self) -> Expression:
        left = self.parse_not()
        while self.peek_kind() == "And":
            self.advance()
            left = Expression("BinaryOp", "And", left, self.parse_not())
        return left

    def parse_not(self) -> Expression:
        if self.peek_kind() == "Not":
            self.advance()
            return Expression("Not", left=self.parse_not())
        return self.parse_comparison()

    def parse_comparison(self) -> Expression:
        left = self.parse_additive()
        op = self.peek_kind()
        if op not in ("Eq", "Ne", "Lt", "Le", "Gt", "Ge"):
            return left
        self.advance()
        return Expression("BinaryOp", op, left, self.parse_additive())

    def parse_additive(self) -> Expression:
        left = self.parse_multiplicative()
        while self.peek_kind() in ("Plus", "Minus"):
            op = "Add" if self.advance().kind == "Plus" else "Sub"
            left = Expression("BinaryOp", op, left, self.parse_multiplicative())
        return left

    def parse_multiplicative(self) -> Expression:
        left = self.parse_postfix()
        while self.peek_kind() in ("Star", "Slash"):
            op = "Mul" if self.advance().kind == "Star" else "Div"
            left = Expression("BinaryOp", op, left, self.parse_postfix())
        return left

    def parse_postfix(self) -> Expression:
        expr = self.parse_primary()
        while True:
            kind = self.peek_kind()
            if kind == "Dot":
                self.advance()
                token = self.advance()
                if token is None or token.kind != "Ident":
                    raise BindingError(f"expected identifier after '.', got {_opt_debug(token)}")
                if self.peek_kind() == "LParen":
                    self.advance()
                    self.expect("RParen")
                    expr = Expression("Call", token.value, expr)
                else:
                    expr = Expression("Attr", token.value, expr)
            elif kind == "LBracket":
                self.advance()
                index = self.parse_or()
                self.expect("RBracket")
                expr = Expression("Index", left=expr, right=index)
            else:
                return expr

    def parse_primary(self) -> Expression:
        token = self.advance()
        kind = token.kind if token else None
        if kind == "Ident":
            return Expression("Ident", token.value)
        if kind in ("Int", "Float", "Str"):
            return Expression("Literal", token.value)
        if kind == "True":
            return Expression("Literal", True)
        if kind == "False":
            return Expression("Literal", False)
        if kind == "LParen":
            expr = self.parse_or()
            self.expect("RParen")
            return expr
        raise BindingError(f"unexpected token {_opt_debug(token)}")


def parse_binding(raw: str) -> Expression:
    """Parses `"{{ expression }}"`. Raises `BindingError` with `tre`'s
    message if it isn't wrapped in `{{ }}` or doesn't parse."""
    trimmed = raw.strip()
    if not (trimmed.startswith("{{") and trimmed.endswith("}}") and len(trimmed) >= 4):
        raise BindingError(f"binding {_str_debug(raw)} is not wrapped in {{{{ ... }}}}")
    inner = trimmed[2:-2]
    try:
        tokens = _lex(inner)
        parser = _Parser(tokens)
        expr = parser.parse_or()
        if parser.pos != len(tokens):
            raise BindingError(f"unexpected trailing input at token {parser.pos}")
    except BindingError as exc:
        raise BindingError(f"failed to parse binding expression: {exc}") from None
    return expr


# -- evaluator --------------------------------------------------------------------


def _wrap(n: int) -> int:
    return ((n - _I64_MIN) % 2**64) + _I64_MIN


def _float_div(a: float, b: float) -> float:
    if b != 0:
        return a / b
    if math.isnan(a) or a == 0:
        return math.nan
    return math.copysign(math.inf, a) * math.copysign(1.0, b)


def _kind(v: Value) -> str:
    if isinstance(v, bool):
        return "Bool"
    if isinstance(v, int):
        return "Int"
    if isinstance(v, float):
        return "Float"
    if isinstance(v, str):
        return "Str"
    return "Handle"


def _primitive_op(op: str, left: Value, right: Value) -> Value:
    kl, kr = _kind(left), _kind(right)
    if op == "Eq":
        return kl == kr and left == right
    if op == "Ne":
        return not (kl == kr and left == right)
    if op == "Add":
        if kl == kr == "Int":
            return _wrap(left + right)
        if {kl, kr} <= {"Int", "Float"} and "Float" in (kl, kr):
            return float(left) + float(right)
        if kl == kr == "Str":
            return left + right
    elif op in ("Sub", "Mul"):
        fn = operator.sub if op == "Sub" else operator.mul
        if kl == kr == "Int":
            return _wrap(fn(left, right))
        if kl == kr == "Float":
            return fn(left, right)
    elif op == "Div":
        if kl == kr == "Int" and right != 0:
            return left / right
        if kl == kr == "Float":
            return _float_div(left, right)
    elif op in ("Lt", "Le", "Gt", "Ge") and kl == kr and kl in ("Int", "Float"):
        return _PY_OPS[op](left, right)
    raise BindingError(f"unsupported operation {op} between {value_debug(left)} and {value_debug(right)}")


def _evaluate(expr: Expression, resolver: _Resolver) -> Value:
    kind = expr.kind
    if kind == "Ident":
        return resolver.ident(expr.value)
    if kind == "Literal":
        return expr.value
    if kind == "Attr":
        return resolver.attr(_evaluate(expr.left, resolver), expr.value)
    if kind == "Index":
        base = _evaluate(expr.left, resolver)
        return resolver.index(base, _evaluate(expr.right, resolver))
    if kind == "Call":
        return resolver.call(_evaluate(expr.left, resolver), expr.value)
    if kind == "Not":
        return not _truthy(_evaluate(expr.left, resolver), resolver)
    op = expr.value
    left = _evaluate(expr.left, resolver)
    if op == "And":
        return _evaluate(expr.right, resolver) if _truthy(left, resolver) else left
    if op == "Or":
        return left if _truthy(left, resolver) else _evaluate(expr.right, resolver)
    right = _evaluate(expr.right, resolver)
    if isinstance(left, Handle) or isinstance(right, Handle):
        return resolver.binary_op(op, left, right)
    return _primitive_op(op, left, right)


def _truthy(value: Value, resolver: _Resolver) -> bool:
    if isinstance(value, Handle):
        return resolver.truthy(value)
    return bool(value)


def evaluate_value(expr: Expression, viewmodel: Any) -> Value:
    """Evaluates `expr` against `viewmodel`, returning a primitive or a
    `Handle` -- the form `value_debug` prints. Raises `BindingError`."""
    return _evaluate(expr, _Resolver(viewmodel))


def evaluate(expr: Expression, viewmodel: Any) -> Any:
    """Evaluates `expr` against `viewmodel` and returns the Python value:
    a primitive, or the object a handle stands for. Signal reads inside
    it are recorded on `tesserae.reactive`'s stack. Raises `BindingError`
    with `tre`'s message."""
    return _Resolver.to_python(evaluate_value(expr, viewmodel))
