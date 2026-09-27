"""M43 Phase 3: `tre`'s answers, recorded once, so the parity tests keep
their proof after `tre` 0.3.5 removes `View`, `Signal` and window themes.

A reference test wraps each question it asks `tre` in `tre(fn)`:

    assert ours == reference.tre(lambda: view.node("r").get("fill"))

Normally `tre(fn)` doesn't call `fn`: it returns the answer recorded for
this test (or raises the exception recorded, with the same type and
message), so the test runs with no `tre` reference at all. With
`TESSERAE_RECORD_TRE=1` -- set by `tools/record_tre_reference.py`, on a
`tre` that still has them (0.3.4) -- it calls `fn`, returns its answer and
records it. Answers are keyed by the test's id and the order it asks, and
kept per test module in `tests/reference/<module>.json`, in a small tagged
JSON form that keeps tuples, non-string dict keys and exceptions exact.
"""

from __future__ import annotations

import builtins
import json
import os
from pathlib import Path
from typing import Any, Callable

DIR = Path(__file__).resolve().parent / "reference"
RECORDING = os.environ.get("TESSERAE_RECORD_TRE") == "1"


class MissingAnswer(AssertionError):
    pass


class _Recorded(Exception):
    """A recorded exception whose type isn't a builtin."""


def encode(value: Any) -> Any:
    if isinstance(value, tuple):
        return {"__tuple__": [encode(v) for v in value]}
    if isinstance(value, list):
        return [encode(v) for v in value]
    if isinstance(value, dict):
        if all(isinstance(k, str) and not k.startswith("__") for k in value):
            return {k: encode(v) for k, v in value.items()}
        return {"__dict__": [[encode(k), encode(v)] for k, v in value.items()]}
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    raise TypeError(f"can't record {type(value).__name__} {value!r}: have fn return plain data")


def decode(value: Any) -> Any:
    if isinstance(value, list):
        return [decode(v) for v in value]
    if isinstance(value, dict):
        if "__tuple__" in value:
            return tuple(decode(v) for v in value["__tuple__"])
        if "__dict__" in value:
            return {decode(k): decode(v) for k, v in value["__dict__"]}
        return {k: decode(v) for k, v in value.items()}
    return value


class _Store:
    def __init__(self) -> None:
        self.modules: dict[str, dict[str, Any]] = {}
        self.test: tuple[str, str] | None = None  # (module, test id)
        self.asked = 0

    def data(self, module: str) -> dict[str, Any]:
        if module not in self.modules:
            path = DIR / f"{module}.json"
            self.modules[module] = {} if RECORDING or not path.exists() else json.loads(path.read_text())
        return self.modules[module]

    def save(self) -> None:
        DIR.mkdir(exist_ok=True)
        for module, answers in self.modules.items():
            (DIR / f"{module}.json").write_text(json.dumps(dict(sorted(answers.items())), indent=1) + "\n")


STORE = _Store()


def begin(module: str, test_id: str) -> None:
    """Called for each test (`conftest.py`)."""
    STORE.test, STORE.asked = (module, test_id), 0


def answer(key: str, fn: Callable[[], Any], module: str) -> Any:
    """`tre`'s answer to `fn` under an explicit `key`, for questions asked
    outside a test (building a parametrize list, say)."""
    return _answer(module, key, fn)


def tre(fn: Callable[[], Any]) -> Any:
    """`tre`'s answer to `fn`, for the running test (see the module doc)."""
    if STORE.test is None:
        raise RuntimeError("reference.tre() outside a test: use reference.answer(key, fn, module)")
    module, test_id = STORE.test
    STORE.asked += 1
    return _answer(module, f"{test_id}#{STORE.asked}", fn)


def _answer(module: str, key: str, fn: Callable[[], Any]) -> Any:
    answers = STORE.data(module)
    if RECORDING:
        try:
            value = fn()
        except Exception as exc:
            answers[key] = {"__raises__": [type(exc).__name__, str(exc)]}
            raise
        answers[key] = encode(value)
        return value
    if key not in answers:
        raise MissingAnswer(f"no recorded tre answer for {module}: {key} -- run tools/record_tre_reference.py "
                            f"on tre 0.3.4 (the question changed, or it's new)")
    recorded = answers[key]
    if isinstance(recorded, dict) and "__raises__" in recorded:
        kind, message = recorded["__raises__"]
        error = getattr(builtins, kind, None)
        if not (isinstance(error, type) and issubclass(error, BaseException)):
            error = _Recorded
        raise error(message)
    return decode(recorded)


def recorded(module: str) -> dict[str, Any]:
    """Every answer recorded for `module`, decoded (replay only)."""
    return {k: decode(v) for k, v in STORE.data(module).items()}
