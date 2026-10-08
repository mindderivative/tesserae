"""Tesserae's `{{ }}` bindings: a thin layer over :mod:`tesserae.expr`.

Since 0.5.0 a binding is a Python-subset expression (see ``design/yaml-language.md`` section 8), evaluated by the
sandboxed evaluator in :mod:`tesserae.expr` -- no longer the port of `tre`'s binding grammar. Python's arithmetic and
comparison rules apply (``1 == 1.0``, unbounded ints up to a limit, unary minus, ``None``), and a Signal reads as its
value, with ``count.get()`` still working.

What stays here is the shape `view.py` was written against:

- `parse_binding(raw)` takes a whole ``"{{ ... }}"`` and returns an `Expression`;
- `evaluate_value` returns a primitive (bool, int, float, str) or a `Handle` around any other object (``None``, a list,
  an object); `evaluate` returns the Python value itself;
- `BindingError` is what both raise, carrying the position and a hint from the `ExprError` behind it;
- the ViewModel is the scope: every public attribute is a name, an underscore name is invisible, and every name is
  treated as reactive.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any, Optional, Union

from tesserae.expr import Expr, ExprError, compile_expr

__all__ = ["BindingError", "Expression", "Handle", "evaluate", "evaluate_value", "parse_binding", "value_debug"]


class BindingError(ValueError):
    """A binding that doesn't parse, or fails to evaluate."""


@dataclass(eq=False)
class Handle:
    """Any value that is not a bool, int, float or str, inside an evaluation. `id` numbers the handles one evaluation
    made, in order."""

    obj: Any
    id: int


Value = Union[bool, int, float, str, Handle]


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



# -- the parsed binding ----------------------------------------------------------------------------------------------

_SIGNAL_GET = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*\.\s*get\s*\(\s*\)\s*$")


class Expression:
    """A compiled binding. `kind`, `value` and `left` describe the one shape the two-way check looks for: a Signal's own
    ``name.get()`` (``kind == "Call"``, ``value == "get"``, ``left.kind == "Ident"``)."""

    __slots__ = ("expr", "kind", "value", "left")

    def __init__(self, expr: Expr, source: str) -> None:
        self.expr = expr
        match = _SIGNAL_GET.match(source)
        if match:
            self.kind, self.value = "Call", "get"
            self.left: Any = _Ident(match.group(1))
        else:
            self.kind, self.value, self.left = "Other", None, None


@dataclass(frozen=True)
class _Ident:
    value: str
    kind: str = "Ident"


class _ViewModelScope:
    """A ViewModel as the names of one expression: its public attributes, all reactive."""

    def __init__(self, viewmodel: Any) -> None:
        self._viewmodel = viewmodel

    def lookup(self, name: str) -> Any:
        if name.startswith("_"):
            raise KeyError(name)
        try:
            return getattr(self._viewmodel, name)
        except AttributeError:
            raise KeyError(name) from None

    def names(self) -> list[str]:
        return [n for n in dir(self._viewmodel) if not n.startswith("_")]

    def is_reactive(self, name: str) -> bool:
        return True


def parse_binding(raw: str) -> Expression:
    """Parses ``"{{ expression }}"``. Raises `BindingError` if it isn't wrapped in ``{{ }}`` or doesn't parse."""
    trimmed = raw.strip()
    if not (trimmed.startswith("{{") and trimmed.endswith("}}") and len(trimmed) >= 4):
        raise BindingError(f"binding {_str_debug(raw)} is not wrapped in {{{{ ... }}}}")
    inner = trimmed[2:-2]
    try:
        return Expression(compile_expr(inner), inner)
    except ExprError as exc:
        raise BindingError(f"failed to parse binding expression: {exc}") from None


def _to_value(obj: Any, handles: list[Handle]) -> Value:
    if isinstance(obj, (bool, int, float, str)):
        return obj
    handle = Handle(obj, len(handles))
    handles.append(handle)
    return handle


def evaluate_value(expr: Expression, viewmodel: Any) -> Value:
    """Evaluates `expr` against `viewmodel`: a primitive or a `Handle`. Signal reads are recorded on
    `tesserae.reactive`'s stack. Raises `BindingError`."""
    try:
        result = expr.expr.evaluate(_ViewModelScope(viewmodel))
    except ExprError as exc:
        raise BindingError(str(exc)) from None
    return _to_value(result, [])


def evaluate(expr: Expression, viewmodel: Any) -> Any:
    """Evaluates `expr` against `viewmodel` and returns the Python value."""
    value = evaluate_value(expr, viewmodel)
    return value.obj if isinstance(value, Handle) else value
