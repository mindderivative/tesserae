# Naming Convention

A screen is a `<Name>_View.yaml` and a `<Name>_ViewModel.py`. The names are how Tesserae joins them, and how it
finds them in a [project](projects.md):

| File | What it is | Its name is |
|---|---|---|
| `Counter_View.yaml` | a view | `Counter`: what `app.open_view("Counter")` and `widget: Counter` say |
| `Counter_ViewModel.py` | its ViewModel, the class `CounterViewModel` | `Counter`: what `app.project.viewmodel("Counter")` finds |
| `Brand_Theme.yaml` | a theme | `Brand`: `App(custom_theme="Brand")` |
| `Tasks_Stylesheet.yaml` | a stylesheet of rules | `Tasks`: `App(stylesheet="Tasks")` |

The part before the suffix is the **name**, and it is CamelCase. Which ViewModel serves which view is not decided by the file
names but by a second name, the view's **bind key**:

```yaml
# Counter_View.yaml
name: Counter            # the bind key
widget: Container
```

```python
# Counter_ViewModel.py
class CounterViewModel(ViewModel):
    views = "Counter"    # the bind keys it serves: a string, or a list for several
```

```python
app.bind(CounterViewModel)
app.open_view("Counter")
```

Keep the bind key equal to the file's name, so one name finds the view, the ViewModel and the screen
(`app.show("Counter")`, `app.navigate("Counter")`). A view with no `name:` is not bound to any ViewModel, and is
registered under its file's name.

## What is checked

- **A ViewModel that is not found.** `app.project.viewmodel("Counter")` imports `Counter_ViewModel.py` and takes the class
  `CounterViewModel`. A file with no such class is an error that lists the `*ViewModel` classes it has.
- **A name no ViewModel has.** Every name a view reads and every action a handler calls is looked up when the view
  opens, and a miss is an error that names the file, line and column and the nearest name:
  `Counter_View.yaml:5:43: 'cont' is not defined (did you mean 'count')`.
- **A mismatched pair.** A ViewModel whose `views` names a view that does not exist, because the keys differ in case or
  spelling, is reported by `app.check()`:
  `CounterViewModel serves the view 'counter', but no view has that name`. The view itself then has no ViewModel, and
  fails on the first name it needs. `assert app.check() == []` in a test is the cheap way to keep the two in step.
- **Two ViewModels for one view.** `app.bind` refuses the second.

## Stylesheet and theme files

Two more names say what a YAML file is:

| Suffix | What it holds | Used by |
|---|---|---|
| `*_Stylesheet.yaml` | a stylesheet: a `styles:` list of rules that name a `widget` | `App(stylesheet=)`, `load_stylesheet` |
| `*_Theme.yaml` | a theme: `seed:`, `colors:`, `typography:`, `components:` | `App(default_theme=, custom_theme=)`, `load_theme` |

A file named for one kind and loaded as another is refused, naming what its name says it is: `load_theme("card_Stylesheet.yaml")`,
say. A theme or stylesheet file with neither suffix (`themes/Brand.yaml`) still loads; the suffixes are recommended, not required.

## The views Tesserae ships

Tesserae's own components are views of the same kind: `Button_View.yaml` with its rules in `Button_Stylesheet.yaml`, in the
package. A view of yours named `Button` (a file `Views/Button_View.yaml`) is found first and replaces it, and the shipped rules
for `Button` are not used for it: its look is then your own `style:` and the rules in your app's stylesheet. See
[Stylesheets](../stylesheets/index.md).

## Why a convention at all?

A name that is the same everywhere is a name nobody has to look up: the view, its ViewModel, its route and its tests all say
`Counter`. A project that follows it can open and join screens with the names alone, and a mismatch is caught when the view
opens, not later when a handler does nothing.

## Views in the older syntax

A view written with `kind:` and `id:` is paired by file name alone: `app.load("Counter")` checks that `Counter_View.yaml` and the
`Counter_ViewModel.py` that defines the ViewModel class (found with `inspect.getfile`, not a string you pass) have the same
prefix, and raises `ValueError` immediately if the view does not end in `_View.yaml`, the ViewModel's file does not end in
`_ViewModel.py`, or the prefixes differ. `instantiate` does the same check for an embedded component
(`tesserae.naming.check_naming_convention` is the shared code); `App.register` and a `Component` built by hand take what you
give them. `tesserae migrate-yaml` moves such a project to the names above ([Migrating](../migration.md)).
