# Getting Started

A real Tesserae app is always a `*_View.yaml` + `*_ViewModel.py` pair,
loaded and shown by one `app.py` entry point.

## The view

```yaml
# Counter_View.yaml
id: root
kind: Container
style: {flex_direction: vertical, width: 240, height: 120, gap: 12, padding: 16}
children:
  - id: label
    kind: Text
    text: {content: "Count: 0", font_family: Roboto, font_size: 20}
    style: {width: 200, height: 32, foreground: "#FFFFFF"}
    bindings: {text: "{{ label.get() }}"}
  - id: button
    kind: Rect
    style: {width: 120, height: 40, background: "#6750A4", corner_radius: 8}
    handlers: {on_click: "increment"}
```

Tesserae builds this view itself on `tre`'s building blocks.
`text: {content: ...}` seeds the initial label;
`bindings: {text: "{{ label.get() }}"}` keeps it live-bound to a
`Signal` your `ViewModel` owns; `handlers: {on_click: "increment"}`
names a method on that `ViewModel` to call on a click. A node with
`on_click` is also a button for the keyboard and for assistive
technology: Tab reaches it, Enter or Space clicks it, and it has
`role="button"`. It also gets MD3's hover tint and press ripple (see
[Interaction Feedback](guide/interaction.md)).

## The ViewModel

```python
# Counter_ViewModel.py
from tesserae import Signal, ViewModel


class CounterViewModel(ViewModel):
    def __init__(self, view):
        self.count = 0
        self.label = Signal("Count: 0")
        super().__init__(view)  # must run after the Signals exist --
                                 # _attach evaluates every binding immediately

    def increment(self):
        self.count += 1
        self.label.set(f"Count: {self.count}")
```

`ViewModel.__init__(view)` (called last, via `super().__init__`) wires
every declared `bindings:`/`handlers:` entry against `self` -- so every
`Signal` a binding expression reads must already exist before that
call.

## The entry point

```python
# app.py
from pathlib import Path

from tesserae import App
from Counter_ViewModel import CounterViewModel

app = App(width=240, height=120, title="My First App")
app.load(str(Path(__file__).parent / "Counter_View.yaml"), CounterViewModel)
app.show("Counter")  # inferred name: the file's own "Counter_View.yaml" prefix
app.run()
```

```bash
python app.py
```

A real window opens; clicking the rect increments the bound label
through a genuine dispatched click and render loop.

## Next steps

- [Apps & Screens](guide/apps-and-screens.md) -- more than one screen,
  switching between them.
- [Components & Embedding](guide/components.md) -- reusable,
  independently-stateful pieces of UI.
- [Repeater](guide/repeater.md) -- a real dynamic list driven by one
  `Signal`.
