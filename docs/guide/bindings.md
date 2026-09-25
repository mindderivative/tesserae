# Binding Expressions

A `{{ }}` binding keeps a widget property in step with your ViewModel:

```yaml
- id: label
  kind: Text
  text: {content: "", font_family: Roboto, font_size: 16}
  bindings: {text: "{{ title.get() }}"}
```

The expression is evaluated against the ViewModel when the view is
attached. Every `Signal` or `Computed` it reads becomes a dependency, and
a change to one evaluates it again and updates the property.

Expressions are a small, safe language, not Python: nothing in a view
file can run arbitrary code.

## What you can write

| | Examples |
|---|---|
| a ViewModel attribute | `count`, `title` |
| an attribute of a value | `user.name`, `pt.x` |
| indexing | `items[0]`, `table["key"]`, `items[n - 1]` |
| a method call with no arguments | `count.get()`, `name.upper()` |
| arithmetic | `a + b`, `a - b`, `a * b`, `a / b` |
| comparison | `==`, `!=`, `<`, `<=`, `>`, `>=` |
| logic | `a and b`, `a or b`, `not a` |
| grouping | `(a + b) * 2` |
| literals | `42`, `1.5`, `"text"`, `'text'`, `True`, `False` |

A call is only allowed as a method on something: `info.described()`
works, a bare `described()` doesn't. A method can't take arguments.

## Rules that differ from Python

Arithmetic and comparison between plain values (numbers, strings,
booleans) follow the binding language's own rules:

- **No negative literals.** There's no unary minus: write `0 - x`, or
  compute the value in the ViewModel.
- **Mixing ints and floats:** `+` mixes them (`1 + 2.5` is `3.5`), but
  `-`, `*` and `<`/`<=`/`>`/`>=` need both sides the same type, so
  `f - 1` is an error when `f` is a float. Write `f - 1.0`.
- **`==` across types is false:** `1 == 1.0` is `False`, and so is
  `True == 1`.
- **Division:** `7 / 2` is `3.5`. Dividing an int by zero is an error;
  a float by zero gives `inf` or `nan`.
- **Strings:** `+` joins two strings; `*` and the ordering comparisons
  aren't supported for strings.
- **No `None` literal**, and string literals have no escapes.
- **Whole numbers are 64-bit.** An int that doesn't fit is used as a
  float, and int arithmetic that overflows wraps around.

As soon as either side is some other object (a list, a `Decimal`, your
own class), Python's own operator decides: `items + items` joins two
lists, and your class's `__add__` or `__lt__` runs.

`and` and `or` return one of their operands, as in Python
(`name or "Untitled"`), and `not` returns `True` or `False`.

## When a binding is wrong

A binding that doesn't parse, or fails to evaluate, raises `ValueError`
when the view is attached, naming the widget, the property and the
expression:

```
widget "label" binding on "text" ("{{ -1 }}"): failed to parse binding expression: unexpected token Some(Minus)
```

## Who evaluates it

Tesserae does, with `tesserae.binding`, a port of `tre`'s evaluator that
gives the same result or the same error for every expression (tested
side by side), in a Tesserae `View` (`tesserae.view.View`, M37). A view
still built by `tre`'s `View` is evaluated by `tre` until Tesserae builds
every view itself (M37 Phase 6); `tre` removes its evaluator in 0.3.5.

In a Tesserae view, a binding that changes a value sets it; one whose
value hasn't changed does nothing. Setting a value from a binding never
counts as the user's edit, so `on_change` runs only when the user changes
the widget: typing in a text field, or toggling a checkbox.
