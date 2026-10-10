"""#251: a function name that does not exist is found when the view loads, not when the expression runs -- in a template, an `if:`, a `for:`,
a stylesheet rule and a handler -- with the line, and the names that are near."""

import pytest

from tesserae import Signal
from tesserae.expr import BUILTIN_FUNCTIONS, ExprError, compile_expr, compile_statements, compile_template
from tesserae.spec.compose import Composer
from tesserae.spec.nodes import LoadError, load_marked, parse_view
from tesserae.spec.rules import RuleSheet


class VM:
    def __init__(self):
        self.count = Signal(0)
        self.items = Signal([1, 2, 3])
        self.log = []

    def bump(self, by=1):
        self.log.append(by)


def actions(path):
    """What an app's built-in actions answer: `copy` and `focus` exist, the rest do not."""
    return (lambda *args: None) if path in ("copy", "focus", "after") else None


actions.names = ("copy", "focus", "after")


def view(body, root="widget: Container\n"):
    return parse_view(root + "children:\n" + body, "Main_View.yaml")


def composed(body, vm=None, **kwargs):
    return Composer({}, vm or VM(), actions=actions, **kwargs).compose(view(body))


# -- an expression, a template, an `if:`, a `for:`: found when the text is compiled ---------------------------------------


def test_an_unknown_function_in_an_expression_is_a_load_error_naming_it():
    with pytest.raises(ExprError) as caught:
        compile_expr("nosuch(1)")
    assert "'nosuch' is not a function you can call here" in caught.value.message
    assert caught.value.hint.startswith("allowed: ") and "clamp" in caught.value.hint  # nothing is near: the whole list


def test_the_near_names_are_offered():
    with pytest.raises(ExprError) as caught:
        compile_expr("clmap(x, 0, 10)")
    assert caught.value.hint == "did you mean 'clamp'"


def test_the_builtin_functions_still_compile():
    for name in ("clamp", "min", "max", "len", "format_number", "pluralize", "format_date", "current_date"):
        assert name in BUILTIN_FUNCTIONS
        compile_expr(f"{name}(x)")


def test_a_call_inside_a_comprehension_is_checked_too():
    with pytest.raises(ExprError, match="'nosuch' is not a function"):
        compile_expr("[nosuch(i) for i in items]")


def test_an_unknown_function_in_a_template_names_the_file_and_line():
    with pytest.raises(LoadError) as caught:
        view("  - widget: Text\n    name: t\n    text: 'a {{ nosuch(1) }} b'\n")
    assert caught.value.file == "Main_View.yaml" and caught.value.line == 5
    assert "'nosuch' is not a function you can call here" in str(caught.value)


def test_an_unknown_function_in_an_if_and_a_for_is_a_load_error():
    with pytest.raises(LoadError, match="'nosuch' is not a function"):
        view("  - {widget: Rect, name: r, if: 'nosuch(count)'}\n")
    with pytest.raises(LoadError, match="'nosuch' is not a function"):
        view("  - {for: i in nosuch(3), key: i, widget: Rect, name: r}\n")


def test_an_unknown_function_in_a_stylesheet_rule_is_a_load_error():
    text = "styles:\n  - widget: Text\n    style: {width: '{{ nosuch(1) }}'}\n"
    with pytest.raises(LoadError, match="'nosuch' is not a function"):
        RuleSheet.of(load_marked(text, "S_Stylesheet.yaml"), "S_Stylesheet.yaml", text)


# -- a handler: found when the view is composed, against what the scope knows ---------------------------------------------


def test_an_unknown_function_in_a_handler_is_a_load_error_with_the_line():
    with pytest.raises(LoadError) as caught:
        composed("  - {widget: Rect, name: r, handlers: {on_click: 'count = nosuch(1)'}}\n")
    assert "'nosuch' is not a function or an action you can call here" in str(caught.value)
    assert caught.value.line == 3


def test_an_unknown_call_statement_in_a_handler_is_a_load_error_that_offers_near_names():
    with pytest.raises(LoadError) as caught:
        composed("  - {widget: Rect, name: r, handlers: {on_click: 'bmup(2)'}}\n")
    assert caught.value.hint == "did you mean 'bump'"


def test_a_viewmodel_method_a_builtin_action_and_a_builtin_function_still_load():
    vm = VM()
    composed("  - {widget: Rect, name: r, handlers: {on_click: 'bump(2); copy(str(count)); count = clamp(count + 1, 0, 5)'}}\n", vm)


def test_without_the_actions_a_handlers_names_cannot_be_judged_so_it_loads():
    Composer({}, VM()).compose(view("  - {widget: Rect, name: r, handlers: {on_click: 'copy(\"x\")'}}\n"))


def test_compile_statements_keeps_the_calls_it_saw():
    statements = compile_statements("bump(1); count = nosuch(2)")
    assert sorted(call.func.id for call in statements.calls) == ["bump", "nosuch"]
