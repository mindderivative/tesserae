# Getting Started

Build one small app, a label and a button that counts, twice: **declaratively**
(a YAML view and a Python ViewModel) and **imperatively** (Python calls that
create nodes). Each step shows both, and every program here is a file in
[`examples/getting_started/`](https://github.com/mindderivative/tesserae/tree/main/examples/getting_started)
that Tesserae's tests run.

## Install

You need Python 3.12 or newer and a desktop session with a Vulkan graphics
driver (any current Linux, macOS or Windows install has one; see
[Installation](installation.md) if a window won't open).

```bash
mkdir counter && cd counter
python3 -m venv .venv
source .venv/bin/activate     # fish: source .venv/bin/activate.fish
pip install tesserae-ui
```

`tesserae-ui` is the name on PyPI; you import `tesserae`. Everything below goes
in the `counter` folder, with the environment active.

## 1. A window

An `App` owns the window. Make one 360 by 160 with a dark background (so the
white text we add next reads on any desktop theme) and open it.

=== "Declarative"

    ```yaml title="Counter_View.yaml"
    --8<-- "examples/getting_started/declarative/step1/Counter_View.yaml"
    ```

    ```python title="app.py"
    --8<-- "examples/getting_started/declarative/step1/app.py"
    ```

=== "Imperative"

    ```python title="app.py"
    --8<-- "examples/getting_started/imperative/step1/app.py"
    ```

Declaratively the window shows a **screen**: `app.build_view` reads
`Counter_View.yaml` and `app.register` names it (`None` is its ViewModel, which
it doesn't need yet). Imperatively there is no file: `window.root` is the box
every node goes in, and one call sets its layout and background.

```bash
python app.py
```

An empty window titled "Counter" opens.

## 2. A node

A **node** is one thing on screen. Add a label that says `Count: 0`.

=== "Declarative"

    ```yaml title="Counter_View.yaml"
    --8<-- "examples/getting_started/declarative/step2/Counter_View.yaml"
    ```

    ```python title="app.py"
    --8<-- "examples/getting_started/declarative/step2/app.py"
    ```

=== "Imperative"

    ```python title="app.py"
    --8<-- "examples/getting_started/imperative/step2/app.py"
    ```

In YAML a node is an entry in `children:`: `kind: Text` makes a label and
`text:` holds what it says. In code, `window.create("text", ...)` makes the node
and `window.root.add_child(...)` puts it in the window. The text's colour is
`foreground` in YAML and `fill=` in code.

!!! tip "If Python prints an error"
    A mistake in a view file ends in a traceback; read the **last line**. It
    names the file, the widget and the problem, and for a misspelt word says what
    you probably meant:

    ```text
    ValueError: .../Counter_View.yaml: widget "label": unknown style field(s) ['foregorund'] -- did you mean 'foreground'?
    ```

## 3. A second node

Add a button: a purple, rounded box with a centred text node in it.

=== "Declarative"

    ```yaml title="Counter_View.yaml"
    --8<-- "examples/getting_started/declarative/step3/Counter_View.yaml"
    ```

    ```python title="app.py"
    --8<-- "examples/getting_started/declarative/step3/app.py"
    ```

=== "Imperative"

    ```python title="app.py"
    --8<-- "examples/getting_started/imperative/step3/app.py"
    ```

A button is a `Rect` (a coloured box) with a `Text` in it. The two ways name
things a little differently:

| YAML view | Python |
| --- | --- |
| `kind: Text` / `kind: Rect` | `window.create("text", ...)` / `window.create("box", ...)` |
| `style: {width: 96, ...}` | `width=96` |
| `foreground`, `background` (`"#RRGGBB"`) | `fill=(r, g, b, a)` |
| `text: {content: "...", font_size: 20}` | `text="..."`, `font_size=20` |
| `children:` | `node.add_child(other)` |

## 4. Make it count

=== "Declarative"

    ```python title="Counter_ViewModel.py"
    --8<-- "examples/getting_started/declarative/step4/Counter_ViewModel.py"
    ```

    ```yaml title="Counter_View.yaml"
    --8<-- "examples/getting_started/declarative/step4/Counter_View.yaml"
    ```

    ```python title="app.py"
    --8<-- "examples/getting_started/declarative/step4/app.py"
    ```

=== "Imperative"

    ```python title="app.py"
    --8<-- "examples/getting_started/imperative/step4/app.py"
    ```

**Declaratively** the state lives in a ViewModel, paired with the view by name
(`Counter_View.yaml` and `Counter_ViewModel.py`). Its `Signal` holds the label's
text; the view's `bindings:` keeps the label showing it, and `handlers:` calls
`increment` on a click. `app.load` pairs the two files.

**Imperatively** the state is a variable and you are the view: `button.on("click",
count)` runs `count`, which sets the label with `label.set(text=...)`.

Run it. Click the button, or press Tab and then Enter or Space, and the count
goes up. The two versions are the same app.

!!! tip "Hot reload"
    Change `app.run()` to `app.run(hot_reload=True)` and edit
    `Counter_View.yaml` while the app is open: the window updates at once and the
    count stays. See [Hot Reload](guide/hot-reload.md).

## Which to use

Use **declarative** for the screens you design: layout, styling, themes and
bindings live in the view file, and the ViewModel holds only your logic. Use
**imperative** for what is made while the app runs; the
[Widgets in Python](guide/widget-catalog.md) guide covers it. The two mix freely,
because a declarative screen is made of the same nodes you create in code:
`view.node("button")` returns any node the YAML declared.

## Next

- [Tutorial](tutorial.md): build a bigger app with a custom window, several
  views and ViewModels, components and styling, in one flat folder; or [as a project](tutorial-project.md),
  with the files in folders and found by name.
- [Projects](guide/projects.md) and [the `tesserae` command](guide/cli.md): start an app from a template, with
  its files in standard folders.
- [Apps & Screens](guide/apps-and-screens.md), [Layout](guide/layout.md) and
  [Themes](themes/index.md).
- [Components](components/index.md): every MD3 component, with its YAML.
