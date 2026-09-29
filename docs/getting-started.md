# Getting Started

A real Tesserae app is always a `*_View.yaml` + `*_ViewModel.py` pair,
loaded and shown by one `app.py` entry point.

## The quick way: `tesserae new`

Installing Tesserae installs a `tesserae` command (M67), which makes an
app you can run at once:

```bash
tesserae new notes
cd notes
python app.py
```

`notes/` has `app.py`, and a `Home_View.yaml`/`Home_ViewModel.py` pair
following the [naming convention](guide/naming-convention.md): a
greeting from the app's [shared state](guide/apps-and-screens.md#shared-state)
and a button that counts its clicks. `app.py` gives Home the route `""`,
so `python app.py <route>` opens on a screen by its route (a
[deep link](guide/apps-and-screens.md#routes-and-deep-links)).

Add a screen with:

```bash
tesserae add screen Settings
```

That writes `Settings_View.yaml` and `Settings_ViewModel.py` (a title
and a Back button that calls `self.app.back()`), and adds its import,
`app.load(...)` and route (`settings`) to `app.py`, above the two marker
comments `tesserae new` left there. Without them it prints the lines to
add instead. A CamelCase name gets a kebab-case route: `UserProfile` is
`user-profile`.

- `tesserae new notes --shell` also makes an [app shell](guide/app-shell.md)
  file, `Notes_Shell.yaml` (a top bar, a navigation rail over Home and
  Settings, a status bar), and the Settings screen.
- `--dir` makes the app somewhere other than here, or adds a screen to
  an app somewhere else.
- Nothing is overwritten: a folder that isn't empty, or a screen whose
  files exist, is refused with a one-line message (exit code 2).
- `python -m tesserae` is the same command.

The rest of this page builds the same kind of app by hand.

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
[Interaction & Accessibility](guide/interaction.md)).

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
