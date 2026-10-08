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

An expression is a **Python subset**, run by a sandboxed
evaluator (`tesserae.expr`): nothing in a view file can import, open a
file, reach `__class__` or run code the application did not expose. The
full grammar and limits are in `design/yaml-language.md` section 8.

A binding can drive text, sizes, colours and other numbers, `checked`
and `selected`, and `visible`: `False` takes a node out of the
layout and out of hit-testing, not just out of sight. There is a
conditional expression: `{{ 'Restore' if app.maximized else 'Maximize' }}`.

## What you can write

| | Examples |
|---|---|
| a ViewModel attribute | `count`, `title` |
| an attribute of a value | `user.name`, `pt.x`; a dict reads by attribute too (`row.title`) |
| indexing and slices | `items[0]`, `table["key"]`, `items[n - 1]`, `name[:3]` |
| arithmetic | `a + b`, `a - b`, `-a`, `a * b`, `a / b`, `a // b`, `a % b`, `a ** 2` |
| comparison | `==`, `!=`, `<`, `<=`, `>`, `>=`, `in`, `not in`, `is None` |
| logic and choice | `a and b`, `a or b`, `not a`, `x if cond else y` |
| literals and displays | `42`, `1.5`, `"text"`, `True`, `None`, `[1, 2]`, `{"a": 1}`, `f"{n} items"` |
| comprehensions | `[t.upper() for t in tags if t]` |
| built-in functions | `len`, `min`, `max`, `sum`, `abs`, `round`, `sorted`, `str`, `int`, `float`, `range`, `format_number`, `pluralize`, `clamp`, ... |
| methods of text, lists and dicts | `name.upper()`, `items.index(x)`, `d.get("k")` |

A **Signal or Computed reads as its value**: `count` and `count.get()` are
the same, and both keep the binding in step when it changes.

Names and attributes starting with `_` do not exist for an expression.
A call is only a built-in function, a method of text, a list or a dict, or
`name.get()` on a Signal. An object the application owns can be read
(its public attributes), but it cannot be added, compared, formatted or
iterated by an expression, so its own methods never run from a view.

An `a11y:` field can be bound the same way (`label`, `hidden` and
`level`): see [Interaction & Accessibility](interaction.md#bound-fields).

### Video frames

An `Image` takes a `frame` binding: a value `(rgba, width, height)`,
`width * height * 4` bytes of RGBA and the frame's size. Each new value
is shown as it arrives, and `None` keeps the last one. Decoding the video
is the app's: a ViewModel sets a `Signal` of the latest frame, and the
view pushes it. The latest frame survives a re-theme and a reconcile.

```yaml
- id: screen
  kind: Image
  image: {fit: fill}
  style: {width: 640, height: 360}
  bindings: {frame: "{{ player.frame.get() }}"}
```

The `Video` fragment is that Image: `component: Video` with `width`,
`height`, `fit` and `frame` (the binding expression, as a string).

## Python's rules

Arithmetic and comparison are Python's: `1 == 1.0` is `True`, integers
do not wrap (an int over 4096 bits is an error), `7 / 2` is `3.5` and
`7 // 2` is `3`. Dividing by zero is an error. `and` and `or` return one
of their operands (`name or "Untitled"`), and `not` returns `True` or
`False`.

Every expression has limits, and a breach is an error that names it: 2000
characters of source, 1000 nodes, nesting 40 deep, 200 000 evaluation
steps, `range` up to 100 000, a result of up to 1 000 000 items,
`**` with an exponent up to 64, and text up to 1 MB. `%` formatting and
`str.format` are not available; use an f-string.

## When a binding is wrong

A binding that doesn't parse, or fails to evaluate, raises `ValueError`
when the view is attached, naming the widget, the property and the
expression, with the position in the expression and a hint when there is
one:

```
widget "label" binding on "text" ("{{ missing.get() }}"): 'missing' is not defined (did you mean 'min')
```

## Who evaluates it

Tesserae does: `tesserae.binding` is a thin layer over `tesserae.expr`, in
a Tesserae `View` (`tesserae.view.View`).

A binding that changes a value sets it; one whose value hasn't changed
does nothing. Setting a value from a binding never counts as the user's
edit, so `on_change` runs only when the user changes the widget: typing in
a text field, or toggling a checkbox.
