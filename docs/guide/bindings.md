# Binding Expressions

A `{{ }}` expression keeps a widget property in step with your ViewModel:

```yaml
- widget: Text
  name: label
  text: "{{ title }}"
  typography_role: body_large
  style: {foreground: on_surface}
```

The expression is worked out against the ViewModel when the view is
opened. Every `Signal` or `Computed` it reads becomes a dependency, and
a change to one works it out again and updates the property. An expression
that reads nothing that can change (literals, params with fixed values,
a loop variable over a fixed list) is worked out once.

An expression is a **Python subset**, run by a sandboxed
evaluator (`tesserae.expr`): nothing in a view file can import, open a
file, reach `__class__` or run code the application did not expose. The
full grammar and limits are in `design/yaml-language.md` section 8.

A binding can drive text, sizes, colours and other numbers, `checked`
and `selected`, and `visible`: `false` takes a node out of the
layout and out of hit-testing, not just out of sight. There is a
conditional expression: `{{ 'Restore' if app.maximized else 'Maximize' }}`. A value inside a
`style:` can be an expression too (`style: {width: "{{ size * 2 }}"}`). Text can mix words and
expressions: `text: "{{ app.state.user }}'s tasks"`.

## What you can write

| | Examples |
|---|---|
| a name | a loop variable, a local `state:`, a param, a ViewModel attribute (`count`, `title`), then `app` |
| an attribute of a value | `user.name`, `pt.x`; a dict reads by attribute too (`row.title`) |
| indexing and slices | `items[0]`, `table["key"]`, `items[n - 1]`, `name[:3]` |
| arithmetic | `a + b`, `a - b`, `-a`, `a * b`, `a / b`, `a // b`, `a % b`, `a ** 2` |
| comparison | `==`, `!=`, `<`, `<=`, `>`, `>=`, `in`, `not in`, `is None` |
| logic and choice | `a and b`, `a or b`, `not a`, `x if cond else y` |
| literals and displays | `42`, `1.5`, `"text"`, `True`, `None`, `[1, 2]`, `{"a": 1}`, `f"{n} items"` |
| comprehensions | `[t.upper() for t in tags if t]` |
| built-in functions | `len`, `min`, `max`, `sum`, `abs`, `round`, `sorted`, `str`, `int`, `float`, `range`, `format_number`, `pluralize`, `clamp`, `format_date`, `current_date`, ... |
| methods of text, lists and dicts | `name.upper()`, `items.index(x)`, `d.get("k")` |

A **Signal or Computed reads as its value**: `count` and `count.get()` are
the same, and both keep the binding in step when it changes.

A property the user edits (a text field's `text`, a `Checkbox`'s `checked`, a `Slider`'s `value`) is **two-way** when it is given
one bare reference to a Signal or a local `state:` name: `checked: "{{ done }}"`. The user's edit is written back to `done`. Any
other expression (`"{{ not done }}"`, `"{{ app.state.user }}"`) is one-way: the widget shows its value, the user's edit stays on screen until the value
next changes, and a handler such as `on_change` does the writing. [Two-way properties](view-language.md#two-way-properties) has the whole rule: which
names a handler may write, what a model param does with each thing a caller gives it, and what `state:` keeps when a view is reloaded.

Names and attributes starting with `_` do not exist for an expression.
A call is only a built-in function, a method of text, a list or a dict, or
`name.get()` on a Signal. An object the application owns can be read
(its public attributes), but it cannot be added, compared, formatted or
iterated by an expression, so its own methods never run from a view.

An `a11y:` field can be bound the same way (`label`, `hidden` and
`level`): see [Interaction & Accessibility](interaction.md#bound-fields).

### Video frames

An `Image` takes a `frame`: a value `(rgba, width, height)`,
`width * height * 4` bytes of RGBA and the frame's size. Each new value
is shown as it arrives, and `None` keeps the last one. Decoding the video
is the app's: a ViewModel sets a `Signal` of the latest frame, and the
view pushes it. The latest frame survives a re-theme and a reconcile.

```yaml
- widget: Image
  name: screen
  fit: fill
  frame: "{{ player_frame }}"
  style: {width: 640, height: 360}
```

`widget: VideoPlayer` is that Image with transport controls under it: `frame`, `playing`, `position`, `duration` and the
rest are its properties ([Video](../components/video.md) has the list).

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

A binding that doesn't parse, or fails to evaluate, is an error when the view loads. It names the file, line and column, and
gives a hint when there is one:

```
Counter_View.yaml:5:43: 'cont' is not defined (did you mean 'count')
```

A function name that does not exist is found when the view loads, with the line, not when the expression runs. In a property, an `if:`,
a `for:` or a stylesheet rule the only functions are the built-in ones (`clamp`, `min`, `max`, `len`, `format_number`, ...), so
`{{ limit(x, 0, 1) }}` is a load error naming `limit` and offering the near names (`did you mean 'clamp'`). In a handler a call may also be
a built-in action (`copy`, `focus`, `after`, `navigate_to`, ...), a method of the ViewModel or a handler parameter; a name that is none of
these is a load error too (`bmup(2)` offers `bump`). `app.check()` lists every name and action the open views use that their ViewModels
do not have, without a window.

## Who evaluates it

Tesserae does: `tesserae.expr` is the evaluator, and `ComposedView` keeps the live nodes in step with what it reads.

A binding that changes a value sets it; one whose value hasn't changed
does nothing. Setting a value from a binding never counts as the user's
edit, so `on_change` runs only when the user changes the widget: typing in
a text field, or toggling a checkbox.
