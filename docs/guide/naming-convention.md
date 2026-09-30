# Naming Convention

Every real view is a `*_View.yaml` + `*_ViewModel.py` pair, mirroring
pyCopper's own real, validated MVVM naming -- enforced at **runtime**,
not just documented, by both `App.load` and `instantiate`:

```python
from tesserae import App
from Counter_ViewModel import CounterViewModel

app = App(width=240, height=120, title="My App")
view, viewmodel = app.load("Counter_View.yaml", CounterViewModel)
```

Raises `ValueError` immediately if:

- the view file doesn't end in `_View.yaml`,
- the `ViewModel`'s own defining file doesn't end in `_ViewModel.py`
  (checked via `inspect.getfile` against the class itself, not a
  string you pass separately), or
- the two prefixes don't match (`Counter_View.yaml` paired with
  `Settings_ViewModel.py`, say).

## Style, stylesheet and theme files

Three more names say what a YAML file is (M75):

| Suffix | What it holds | Used by |
|---|---|---|
| `*_Style.yaml` | one node's style: a mapping of style fields | a node's `style:`, a stylesheet or theme rule's `style:` |
| `*_Stylesheet.yaml` | a stylesheet: a `styles:` list of rules | `App(stylesheet=)`, `app.load(..., stylesheet=)`, `load_stylesheet` |
| `*_Theme.yaml` | a theme: `seed:`, `colors:`, `styles:`, ... | `App(default_theme=, custom_theme=)`, `load_theme` |

A node's `style:` given as a file must be a `*_Style.yaml` one. A file
named for one kind and loaded as another is refused, naming what its
name says it is -- `load_theme("card_Style.yaml")`, say. A theme or
stylesheet file with none of these suffixes (`themes/Brand.yaml`) loads
as before; the suffixes are recommended, not required.

## Why enforce this at all?

A `ViewModel` is scoped one-per-view-file by convention, so a
self-contained, independently-loadable pair is what lets `App`
register several and switch which one is shown without re-bootstrapping
each one from scratch. Catching a mismatched pair immediately, at load
time, is worth more than a cryptic failure much later when a handler
name doesn't resolve against the wrong `ViewModel`.

## Where it's checked

Both real call sites use the same shared check
(`tesserae.naming.check_naming_convention`):

- **`App.load`** -- for top-level screens.
- **`instantiate`** -- for embedded components (see
  [Components & Embedding](components.md)), so a mismatched component
  pair fails immediately at instantiation time too.

`App.register`/manually-constructed `Component`s bypass this (they
take an already-constructed `View`/`ViewModel` directly) -- the
convention is enforced at the two real *construction* entry points,
not retroactively on whatever you hand `register`.
