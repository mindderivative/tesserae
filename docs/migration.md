# Migrating

What to change in an existing app when you upgrade. Each section is the release you are moving to; the
[changelog](changelog.md) has everything else that changed.

## To 0.5.0

**This release changes the view language.** Everything you wrote before still loads: a view in the old syntax is read as it always was, and says
once per file how to move on. The new language is one shape (a node with a `widget:`), a ViewModel that serves several named views, rules in
stylesheets, and one expression language. [The View Language](guide/view-language.md) is the whole of it.

### Move a project

```bash
tesserae migrate-yaml            # reports what would change; writes nothing
tesserae migrate-yaml --write    # writes it, if every file checked out
```

It reads every `*_View.yaml`, `*_Component.yaml` and `*_Stylesheet.yaml` in the project, translates them, checks each result with the loader
the app uses, and writes only if all of them load (`--force` writes the ones that did). Keep the project in version control: the old files are
rewritten, and a fragment is renamed. The comments at the top of a file are kept; comments inside a file are not, and the report says which files had
them. Themes (`*_Theme.yaml`) and style files are left as they are.

| Before | After |
| --- | --- |
| `kind: X`, `component: X`, `view: X_View.yaml`, `include: X.yaml` | `widget: X` |
| `*_Component.yaml` | `*_View.yaml` (a view with `params:`) |
| `id: x` | `name: x`; the root's `id: root` is dropped |
| `with: {a: 1}` on a call | `a: 1` |
| `repeat: "{{ items }}"` | `for: item in items` with a `key:` (write the identity, `item.id`; the tool leaves a stand-in and says so) |
| `when: "{{ x }}"`, `{if: ..., then: ..., else: ...}` | `if: x` on the node, or on two nodes |
| `bindings: {text: "{{ x.get() }}"}` | `text: "{{ x.get() }}"` (and `{{ x }}` works) |
| `two_way: checked` | a bare reference on a model property: `checked: "{{ done }}"` |
| `kind: TextField` (the bare input) | `widget: TextInput`; the Material text field is now `widget: TextField` |
| `text: {content: Hi, typography_role: ...}`, `icon: {name: home}`, `image: {...}` | `text: Hi`, `typography_role: ...`, `icon: home`, the keys of `image` as properties |
| `bindings: {background: ...}` | `style: {background: ...}` |
| `interaction: {color: X}` | `interaction: X` |
| `navigate.{{ screen }}` | `navigate_to(screen)` |
| a stylesheet rule `kind: Rect` / `id: go` / `classes: [a]` | `widget: Rect` / `name: go` / `classes: [a]` |
| a component's `<Name>_Stylesheet.yaml`, rules by `id:` | rules `widget: Name`, with `part: <id>` (`root` is the widget itself) |

A view that has a `<Name>_ViewModel.py` beside it is named `name: <Name>`, the bind key. **The ViewModels are Python and are not rewritten;** the
report lists what each needs:

```python
class CounterViewModel(ViewModel):
    views = "Counter"                 # the views it serves

    def __init__(self):               # no `view` argument
        super().__init__()
        self.count = Signal(0)
```

```python
app.bind(CounterViewModel)
app.open_view("Counter")              # instead of app.load("Counter")
```

`ViewModel(view)` and `app.load(...)` still work for views in the old syntax, so a project can move one view at a time: migrate, then change that
view's ViewModel and its line in `app.py`.

### What the tool cannot do

- A widget name that is a parameter (`component: "{{ button }}"`) has no equivalent: a `variant` property on one widget replaces it.
- A call that sets a property its fragment does not declare (`disabled` on a `ButtonText`) is reported; the fragment needs to declare it.
- The shipped fragments (`ButtonFilled`, `NavigationRail`, ...) are not views in the new language yet, so a view that calls one cannot be
  opened with `app.open_view` yet; keep it on `app.load`.
- `Window`, `TitleBar` and `Dock` views, an Image `frame` binding, a ScrollView's `scroll_offset` and `on_key` are not drawn by `app.open_view` yet.
  The ones it cannot draw are errors that name the property, never silently dropped.
- A view written with `kind: TextField` was the bare input. It becomes `widget: TextInput`, and `widget: TextField` is the Material text field, so a migrated view keeps what it had; move to `TextField` when you want the label, supporting text and the rest.
- `foreground` is valid only on the widgets that draw text or glyphs; on a `Container` it is now an error that names them.

## To 0.4.6

Nothing has to change if your app already runs on 0.4.5. The old names that 0.4.5 removed each raised an error saying what
replaced them; those messages are gone now, and an old name fails as any unknown name does: `App(decorations=False)` is a
`TypeError` ("unexpected keyword argument"), `app.load_shell`, `app.use_shell` and `app.decorations` are an `AttributeError`,
`from tesserae.shell import AppShell` is a `ModuleNotFoundError`, `tesserae new --shell` is "unrecognized arguments", and a
`*_Shell.yaml` is an ordinary view that doesn't fit the schema. If you meet one of them, [To 0.4.5](#to-045) is the table of what
replaces each.

## To 0.4.5

**This release is breaking.** There is one way to describe a window now, a `kind: Window` view ([Windows, Docks & Embedded
Views](guide/windows-and-docks.md)), so the older ways are removed. In this release each removed name raised an error that said what replaces
it; from 0.4.6 they fail as unknown names do ([To 0.4.6](#to-046)), so this table is where to look.

| Removed | Use instead |
| --- | --- |
| `*_Shell.yaml` and `app.load_shell(...)` | a `Window_View.yaml` of `kind: Window`, loaded with `app.load("Window")` |
| `tesserae.shell.AppShell` and `app.use_shell(...)` | the same window view; for docking from Python, `tesserae.docking.Dock` |
| `App(decorations=False)` | `App(borderless=True)`, or `borderless: true` on the `Window` |
| `app.decorations` (and `app.decorations = ...`) | `app.borderless`, which is the opposite |
| `tesserae new --shell` | `tesserae new --window` |
| the `tesserae-shell-schema.json` editor schema | none: a window view is a `*_View.yaml`, which has its schema |

### From a shell file

Before, `app.py` loaded the screens, routed them and loaded the shell:

```python
app = App(width=640, height=480, title="Tasks", decorations=False)
app.load("Main")
app.load("Settings")
app.route("", "Main")
app.route("settings", "Settings")
app.load_shell("Tasks")                       # Views/Tasks_Shell.yaml
```

```yaml
# Tasks_Shell.yaml
top_bar: {title: Tasks, style: {background: primary_container}}
navigation:
  items:
    - {screen: Main, icon: home}
    - {screen: Settings, icon: settings}
status_bar: {text: Ready, style: {height: 28}}
```

Now the window view holds the frame and the screens, and `app.py` loads one file:

```python
app = App(title="Tasks")
app.load("Window")                            # Views/Window_View.yaml
app.navigate_to("")
```

```yaml
# Window_View.yaml
id: root
kind: Window
title: Tasks
borderless: true
style: {width: 640, height: 480, background: surface, flex_direction: vertical}
title_bar: {title: Tasks, style: {background: primary_container}, buttons: [minimize, maximize, close]}
children:
  - id: body
    kind: Container
    style: {flex: fill, flex_direction: horizontal}
    children:
      - id: nav
        component: NavigationRailScreens
        with:
          items:
            - {label: Tasks, icon: home, screen: Main}
            - {label: Settings, icon: settings, screen: Settings}
      - id: screens
        kind: Container
        style: {flex: fill}
        children:
          - {id: main, view: Main_View.yaml, route: "", style: {flex: fill}}
          - {id: settings, view: Settings_View.yaml, route: settings, style: {flex: fill}}
  - id: status
    component: StatusBar
    with: {text: Ready, width: "100%"}
```

| In the shell file | In the window view |
| --- | --- |
| `top_bar: {title, leading_icon, trailing_icons, style}` | `title_bar: {title, icon, buttons, children, style}`; your icons are `children` |
| `navigation: {items}` (`screen`, `icon`) | a `NavigationRailScreens` with `items` of `label`, `icon`, `screen` |
| `navigation.on_navigate` | `handlers: {on_click: ...}` on your own nodes, or `navigate.<Screen>` |
| `status_bar: {text, style}` | a `StatusBar` component |
| `zones: {left: 220}`, `center`, `panels` | a `kind: Dock` with `kind: DockPanel`s: `style: {zone: left, width: 220}`; panels in one zone are tabs |
| a panel named `Files` (a screen or `Files_View.yaml`) | `- {id: files_view, view: Files_View.yaml}` inside a `DockPanel` |
| `app.load("Main")` and `app.route("", "Main")` | `view: Main_View.yaml` with `route: ""` in the window view |
| `shell.layout()` and `shell.restore(layout)` | `view.dock_host("dock").layout()` and `.restore(layout)` |
| `shell.size(side)` and `shell.set_size(side, px)` | `view.dock_host("dock").size(side)` and `.set_size(side, px)` |
| `app.screen("Files")` | `view.embedded("files_view")` |

### From `AppShell` and `use_shell`

Build the frame as a window view as above. A Python-built `Dock` (`from tesserae.docking import Dock`) is unchanged: `Dock(window)`,
`add_zone`, `add_panel`, `move`, `show` and the rest. `AppShell`'s own `layout()`, `restore()`, `size()` and `set_size()` are on
the `DockHost` of a `kind: Dock` (`view.dock_host(id)`), as in the table.

### From `decorations`

`decorations=False` is `borderless=True`, and `decorations=True` is `borderless=False` (the default). Read the state as
`app.borderless`; a binding that read `app.decorations` should be `not app.borderless`.

## To 0.4.4

Nothing had to change: shell files, `app.load_shell()` and `decorations=False` worked as before. New apps could write their frame as
a `kind: Window` view (`tesserae new notes --window`), and the shell file is being phased out, so an app that has one can move
over when it likes:

| In the shell file | In the window view |
| --- | --- |
| `top_bar: {title: Notes}` | `title_bar: {title: Notes}` on the `kind: Window` root |
| `navigation: {items: [...]}` | a `NavigationRailScreens` with the same items (`screen:` names a screen) |
| `status_bar: {text: Ready}` | a `StatusBar` component |
| `zones:` | a `kind: Dock` with `kind: DockPanel`s, each `style: {zone: left}` |
| `app.load("Main")` and `app.route("", "Main")` | `- {id: main, view: Main_View.yaml, route: ""}` in the window view |
| `App(decorations=False)` | `borderless: true` on the window (or `App(borderless=True)`) |

Then `app.load("Window")` replaces `app.load_shell(...)`. [Windows, Docks & Embedded Views](guide/windows-and-docks.md) has each form.
An app can't load a window view and a shell file together.

## To 0.4.3.3

Tesserae needs `tre` (`tesserae-engine`) 0.5.5 or newer, below 0.6: `pip install --upgrade tesserae-ui` brings it. Nothing in your code has
to change. Resizing a window, undecorated or with the OS's frame, no longer stalls on KDE Wayland: tre 0.5.4 stalled for up to a
second at a time while it was dragged, and 0.5.5 fixes that.

## To 0.4.3.1

Nothing has to change. A `*_Style.yaml` is written with its fields under `style:` now, and an `id:` if you like, and the
style files you have, which are only the fields, still load. [Style files](themes/index.md#style-files) has the form.

## To 0.4.2

Tesserae needs `tre` (`tesserae-engine`) 0.5.4 or newer, below 0.6: `pip install --upgrade tesserae-ui` brings it.
Nothing in your code has to change, but three things look or behave differently:

- **A window is scaled to its screen** (`App(dpi_scaling=True)` is the default). On a high-density screen a 16-pixel
  size is now the same size it is on a standard one, drawn with more pixels, and `width`, `height` and pointer
  positions are in those logical pixels. `App(dpi_scaling=False)` is the old behaviour. See
  [Window Options](guide/window-options.md).
- **Animations stop for a user who asked the OS for less motion**, and the theme is made at a higher contrast for one
  who asked for more. `App(reduced_motion=False, high_contrast=False)` ignores the OS.
- **Colours are drawn exactly as written**, which on some screens is a little darker than before.

## To 0.4.1

Nothing in your code has to change. `tesserae new` makes a [project](guide/projects.md) with files in `Views/`,
`ViewModels/`, `Components/`, `Themes/` and `Styles/`, found by name, and its first screen is `Main`, not `Home`.
An app with its files beside `app.py` keeps working, and `tesserae add screen` follows whichever layout it
finds.

## To 0.4.0

Where a node's children go, and how a node takes room, have new names. The engine's names are refused with
a message saying what replaces them (`style.align_items is now align_content ...`), so a view that uses
one fails to load and tells you.

| Was | Is |
| --- | --- |
| `align_items`, `justify_content` | `align_content`: one of nine positions (`top_left`, `top`, `top_right`, `left`, `center`, `right`, `bottom_left`, `bottom`, `bottom_right`) |
| `justify_content: space_between` / `space_around` / `space_evenly` | `spread: between` / `around` / `evenly` |
| `flex_grow: 1` | `flex: expand_horizontal` (in a row) or `expand_vertical` (in a column) |
| `flex_shrink: 0` | nothing: it is the default now |
| `flex_basis` | `width` or `height`, with `flex` |
| `align_self`, `justify_self` | `align_self`, one of the nine positions |
| `justify_items` | `align_cells` (a grid) |
| `align_content` on a wrapping node | `align_wrapped` |
| `align_content` and `justify_content` on a grid | `align_tracks` |

What an old pair becomes, in a row (`flex_direction: horizontal`, the default):

| Was | Is |
| --- | --- |
| `align_items: center` | `align_content: left` |
| `align_items: center`, `justify_content: center` | `align_content: center` |
| `justify_content: flex_end` | `align_content: top_right` |
| `align_items: flex_end` | `align_content: bottom_left` |
| `align_items: center`, `justify_content: space_between` | `spread: between`, `align_content: left` |

In a column the same words name the same places: `align_items: center` (across a column is horizontal)
is `align_content: top`.

Things that change with them:

- **A node is never squeezed by default.** Its size is its `width` and `height`, or its content. `flex_shrink` was 1,
  so a crowded parent shrank its children; now they keep their sizes and overflow. A `Text` that used to wrap
  because its parent was narrow now needs `flex: expand_horizontal` (or a `width`) to wrap.
- **Not setting `align_content` still stretches** children across the layout and starts them at the start.
  Setting it places them, so children that were stretched (`align_items: stretch`, the default) and a position
  that means centred along the other axis are not the same: use `flex: expand_vertical` (or `expand_horizontal`)
  on the children that should fill.
- **`baseline` is gone.** Nothing replaces it.
- **`flex` overrides the size** across the parent's layout: `flex: expand_vertical` in a row drops the node's `height`.
- **Python:** a style given to a widget (`top_app_bar(style=...)`) and `AppShell(styles=...)` take the new names too.
  Direct engine calls (`window.create(..., align_items=...)`) are the engine's, and unchanged.

## To 0.3.4

Nothing in your code has to change.

- The built-in components keep their look in `<Name>_Stylesheet.yaml` files and their structure in
  `<Name>_Component.yaml`. A view that uses `component: ButtonFilled` expands to exactly what it did.
  If you copied a built-in `*_Component.yaml` to restyle it, you can delete the copy and put just a
  `<Name>_Stylesheet.yaml` with the fields you change next to your views.
- A `*_Component.yaml` or `*_Stylesheet.yaml` in a view's own folder is now found. A file there named
  for a built-in component replaces or restyles it, so check that none is there by accident.

## To 0.3.3

- A view with no `theme_seed` resolves theme roles (`surface`, `primary`, ...) from MD3's baseline palette,
  where it used to fail. Nothing to change; add a `theme_seed=` to make the colours your own.
- A shell's top and status bars keep their height when the window is short.

## To 0.3.2

- Tesserae needs `tre` (`tesserae-engine`) 0.5.1 or newer, below 0.6.
- `app.run(keepalive=)` is off by default. A hot-reload watcher or a thread calling
  `thread_handle().call_soon` reaches an idle window without it. Pass `True` or a number to tick the loop
  regularly.

## To 0.3.0

- Tesserae needs `tre` 0.5.0.1 or newer, below 0.6.
- A shell file's navigation rail `navigate`s (with history) instead of jumping with `show`, so `back()`
  returns from a rail choice.
- Window options (`decorations`, `resize_border`, `min_width`, `fullscreen`, `system_menu`, `icon`) are on
  `App`, and the actions `minimize()`, `maximize()`, `restore()`, `toggle_maximized()` and `close()`.

## To 0.2

The widgets became Tesserae's own: built from `tre`'s building blocks, and returned as Tesserae objects.

- **Controls.** `checkbox`, `radio_button`, `switch`, `slider`, `spin_box`, `circular_progress`,
  `linear_progress`, `loading_indicator` and `time_picker_dial` return a control, not a `tre.Node`. Where
  you read `node.get_checked()` or `get_selected()`, read `control.checked.get()` or `control.selected.get()`.
  Where you called `set_checked(...)`, call `control.checked.set(...)`. Use the control's `.node` where you
  used the node. A checkbox, switch or radio button toggles itself when clicked, so an `on_click` that
  toggled it by hand should go. `spin_box` returns one `SpinBox`, not `(field, minus, plus)`. A slider's
  position is `control.value.get()`.
- **Composed widgets** return a `Widget`: `.node`, `.part(name)`, `on_click(fn)`, `set_theme(theme)`,
  `destroy()`.
- **Renamed arguments.** Old names raise `TypeError`:

    | Function | Was | Is |
    | --- | --- | --- |
    | `switch` | `on=` | `selected=` |
    | `divider` | `vertical=True` | `orientation="vertical"` |
    | `link` | `text` | `content` |
    | `dialog` | `text` | `supporting_text` |
    | `toolbar` | `tone="vibrant"` | `vibrant=True` |

- **Images and video.** `image(window, path, ...)` decodes the file itself, so the engine never receives a
  path. A missing or undecodable file is an `OSError`. `video(...)` is a blank surface until you call
  `video.frame(rgba, width, height)`.
- **Files.** `load_theme` and `load_stylesheet` refuse a file named for another kind (`*_Style.yaml`,
  `*_Stylesheet.yaml`, `*_Theme.yaml`); other names load as before.
