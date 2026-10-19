"""The Bindings page lists every function and method an expression may use; a name added to (or dropped from) `tesserae.expr` has to reach the page."""

import re
from pathlib import Path

import pytest

import tesserae.expr as expr

PAGE = (Path(__file__).resolve().parent.parent / "docs" / "guide" / "bindings.md").read_text(encoding="utf-8")
WORDS = set(re.findall(r"[a-z_]+", PAGE))


@pytest.mark.parametrize("name", sorted(expr.BUILTIN_FUNCTIONS))
def test_a_built_in_function_is_on_the_bindings_page(name):
    assert name in WORDS


@pytest.mark.parametrize("name", sorted(expr._STR_METHODS | expr._LIST_METHODS | expr._DICT_METHODS))
def test_a_method_is_on_the_bindings_page(name):
    assert name in WORDS


def test_the_page_names_no_function_the_expression_language_lacks():
    listed = re.search(r"\| built-in functions \| (.*?) \|\n", PAGE).group(1)
    named = set(re.findall(r"`([a-z_ ]+)`", listed))
    functions = {word for entry in named for word in entry.split()}
    assert functions <= set(expr.BUILTIN_FUNCTIONS) | {"isinstance"}, sorted(functions - set(expr.BUILTIN_FUNCTIONS))
