# Getting Started

This page takes you from a fresh Linux install to a window with a label
and a button that counts. You build the same small app twice: first
**declaratively**, with a YAML view and a Python ViewModel, then
**imperatively**, creating nodes with Python calls. Every step is shown
both ways, side by side, and every program on this page is a real file in
[`examples/getting_started/`](https://github.com/mindderivative/tesserae/tree/main/examples/getting_started)
that is run by Tesserae's tests.

## Before you start

You need:

- **Python 3.12 or newer**, already installed. Check with
  `python3 --version`.
- **Tesserae 0.3.1 or newer**, which `pip install tesserae-ui` below gets.
- **A Linux desktop session**, X11 or Wayland, on x86-64. (Tesserae also
  runs on macOS with Apple silicon and on Windows; see
  [Installation](installation.md).)
- **A graphics driver with Vulkan.** Any current desktop install has one.
  If a window won't open and Python ends with `no GPU adapter available`,
  install your distribution's Mesa Vulkan driver:

    ```bash
    sudo apt install mesa-vulkan-drivers      # Debian, Ubuntu
    sudo dnf install mesa-vulkan-drivers      # Fedora
    ```

- **`libxkbcommon-x11`**, which an X11 session needs (a Wayland session
  doesn't). Most desktops have it. If the error names it:

    ```bash
    sudo apt install libxkbcommon-x11-0       # Debian, Ubuntu
    sudo dnf install libxkbcommon-x11         # Fedora
    ```

## Set up

Recent distributions won't let `pip` install into the system's Python,
so make a virtual environment for the app. (Debian and Ubuntu split
`venv` into its own package: `sudo apt install python3-venv`.)

```bash
mkdir counter
cd counter
python3 -m venv .venv
source .venv/bin/activate     # fish: source .venv/bin/activate.fish
pip install tesserae-ui
```

`tesserae-ui` is the name on PyPI; you import `tesserae`. It installs
everything the app needs, including the rendering engine (`tre`) as a
prebuilt wheel. Check it:

```bash
python -c "import tesserae; print('Tesserae is ready')"
```

Everything below goes in the `counter` folder, with the environment
active (`source .venv/bin/activate` in a new terminal).

## 1. A window

An `App` owns the window. Make one 360 by 160 with a dark background and
open it. The dark background keeps the white text we add next readable
whatever the desktop's light or dark theme is.

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


In the declarative version the window shows a **screen**, a view in a
file: `app.build_view` reads `Counter_View.yaml` and `app.register` names
it. The `None` is its ViewModel, which it doesn't need yet. In the
imperative version there is no file: `window.root` is the box every node
goes in, and you set its layout (a column with 16 px of padding and 12
between nodes) and its background with one call.

Run it:

```bash
python app.py
```

An empty window opens, titled "Counter". Close it with its close button.

## 2. A node

A **node** is one thing on screen. Add a label: text that says
`Count: 0`.

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


Declaratively, a node is an entry in `children:`. `kind: Text` makes a
label, and `text:` holds what it says (a `Text` needs a `font_family`).
Imperatively, `window.create("text", ...)` makes the node and
`window.root.add_child(...)` puts it in the window. Both give the text node
a size, and its colour is `foreground` in YAML and `fill=` in code.

Run `python app.py` again: the window now says "Count: 0".

!!! tip "If Python prints an error"
    A mistake in the view file ends in a long traceback, and the **last
    line** is the one to read. It names the file, the widget and the
    problem, and for a misspelt word it says what you probably meant:

    ```text
    ValueError: .../Counter_View.yaml: widget "label": unknown style field(s) ['foregorund'] -- did you mean 'foreground'?
    ```

    Fix the word in the file and run it again. (With hot reload on, see
    [Run it](#5-run-it), a mistake saved while the app is open is logged
    instead, the window keeps its last good version, and saving the fix
    brings it in. See [Hot Reload](guide/hot-reload.md#when-an-edit-is-broken).)

## 3. A second node

Add a button. It is a purple, rounded box with a text node in it, centred.

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


A button is nothing special: a `Rect` (a coloured box) with a `Text` in
it. In code the box is `window.create("box", ...)`, and the text goes
inside it with `add_child` before the box goes in the window. The text is
as wide as the button, and `text_align: center` centres it there.

The two ways name things a little differently:

| In the YAML view | In Python |
| --- | --- |
| `kind: Text` / `kind: Rect` | `window.create("text", ...)` / `window.create("box", ...)` |
| `style: {width: 96, ...}` | `width=96` |
| `foreground` and `background` (`"#RRGGBB"`) | `fill=(r, g, b, a)` |
| `text: {content: "...", font_size: 20}` | `text="..."`, `font_size=20` |
| `text: {text_align: center}` | `text_align="center"` |
| `children:` | `node.add_child(other)` |

Run it again to see the button. It doesn't do anything yet.

## 4. Make it count

The count is the app's state, and the label shows it.

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


**Declaratively**, the state lives in a ViewModel, a Python class paired
with the view by name (`Counter_View.yaml` and `Counter_ViewModel.py`).
Its `Signal` holds the label's text. In the view,
`bindings: {text: "{{ label_text.get() }}"}` keeps the label showing it,
and `handlers: {on_click: increment}` calls the ViewModel's `increment`
method when the button is clicked. The `super().__init__(view)` call goes
last, because it reads the Signals the view refers to. `app.py` now uses
`app.load`, which pairs the view with its ViewModel class by that naming
convention.

**Imperatively**, the state is a variable and the "view" is you:
`button.on("click", count)` runs `count` on a click, and `count` sets the
label's text with `label.set(text=...)`. The last line makes the button
a real button for the keyboard and for screen readers: Tab reaches it,
and Enter or Space clicks it. (In YAML, a node with an `on_click` handler
is made a button for you, with MD3's hover tint and press ripple as well.
In code, [`tesserae.interaction`](guide/interaction.md#from-code) or the
[`button` widget](guide/widget-catalog.md) add those.)

## 5. Run it

```bash
python app.py
```

Click the button and the count goes up. Press Tab and the button takes
focus (declaratively it also shows MD3's focus ring); Enter or Space
counts too. The two versions are the same app: the same layout, colours
and behaviour, the hover tint, ripple and focus ring aside.

To see a declarative edit without restarting, run it with hot reload:
change `app.run()` to `app.run(hot_reload=True)`, then edit
`Counter_View.yaml` (the button's colour, say) while the app is open. It
changes at once, and the count stays. Hot reload watches the view file
the screen was built from; the imperative version has no file, so there
you edit and run again. The edit reaches the window even if you aren't
touching it (see [Hot Reload](guide/hot-reload.md)).

## Which to use, and both together

- **Declarative** suits the screens you design: the layout, the styling,
  light and dark themes, bindings to state, and hot reload are all in the
  view file, and the ViewModel holds only the app's own logic. It is how
  `tesserae new` makes an app, and how most of Tesserae is documented.
- **Imperative** suits what is made while the app runs, from data or
  from a loop, and the [widget catalog](guide/widget-catalog.md) (every
  MD3 widget as a Python function). For a list that grows and shrinks,
  see [Repeater](guide/repeater.md).
- **Both at once** works, because a declarative screen is made of the
  same nodes you create in code. Add a node to a screen loaded from YAML:

    ```python
    view, viewmodel = app.load(Path(__file__).parent / "Counter_View.yaml", CounterViewModel)
    note = app.window.create("text", text="Made in Python", font_size=14, width=120, height=20,
                             fill=(255, 255, 255, 255))
    view.root.add_child(note)
    ```

    `view.node("button")` gives you any node the YAML declared, by its `id`.

## The quick way: `tesserae new`

Installing Tesserae installs a `tesserae` command, which makes an
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
- `tesserae new notes --shell --custom-title-bar` makes the window
  undecorated (`decorations=False`, at least 640 by 400), so the shell's
  top bar is its [title bar](guide/custom-title-bars.md):
  it moves the window, and it has the minimize, maximize and close
  buttons. It goes with `--shell`.
- `--dir` makes the app somewhere other than here, or adds a screen to
  an app somewhere else.
- Nothing is overwritten: a folder that isn't empty, or a screen whose
  files exist, is refused with a one-line message (exit code 2).
- `python -m tesserae` is the same command.

## Release it

When the app is ready for its users, build it into one executable:

```bash
pip install "tesserae-ui[build]"
tesserae build --check
```

That makes `dist/notes` (`dist/notes.exe` on Windows), with every file
under the app's folder inside it, and `--check` runs it briefly to see it
start. It runs on the kind of computer it was built on, with nothing else
installed. `--name`, `--icon`, `--console`, `--include` and `--exclude`
adjust it; [Releasing Your App](guide/releasing.md) has the details.

## Next steps

- [Apps & Screens](guide/apps-and-screens.md) -- more than one screen,
  switching between them, the window's options.
- [Components & Embedding](guide/components.md) -- reusable,
  independently-stateful pieces of UI.
- [Repeater](guide/repeater.md) -- a real dynamic list driven by one
  `Signal`.
- [Themes & Fonts](guide/themes-and-fonts.md) -- colours, light and dark,
  and your own fonts.
- [Custom Title Bars](guide/custom-title-bars.md) -- drawing the window's
  own title bar.
- [Editor Support](guide/editor-support.md) -- completion and typo
  checking for your YAML files in VS Code.
