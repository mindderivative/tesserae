# Projects

A project is a folder with a place for each kind of file. Tesserae finds a file by its name, so
`app.open_view("Main")` is enough and a view says `widget: Stat` without a path. `tesserae new` makes one:

```bash
tesserae new notes
cd notes
source .venv/bin/activate     # Windows: .venv\Scripts\activate
python app.py
```

```text
notes/
  .venv/              a virtual environment with Tesserae in it
  app.py
  Views/              Main_View.yaml, Window_View.yaml (the window), Name_View.yaml: every screen and every view you call
  ViewModels/         Main_ViewModel.py
  Components/         Name_Component.yaml: fragments in the older syntax, which you won't write new
  Themes/             Name_Theme.yaml
  Styles/             Name_Stylesheet.yaml
```

The files `tesserae new` writes (`Main` and the `Settings` that `tesserae add screen` adds) are in the older view
syntax, which still loads and says so when it runs; [`tesserae migrate-yaml`](cli.md#move-a-project-to-the-current-syntax) moves them, and the
[project tutorial](../tutorial-project.md) shows the app written in the current one.

The [project tutorial](../tutorial-project.md) builds an app in one, step by step, beside the
[flat-folder tutorial](../tutorial.md).

`--no-venv` makes the folders and files without the virtual environment (the environment needs the network to
install Tesserae). [The `tesserae` command](cli.md) has the rest.

## Finding files by name

| You write | Tesserae opens |
| --- | --- |
| `app.open_view("Main")` | `Views/Main_View.yaml` |
| `app.bind(app.project.viewmodel("Main"))` | `ViewModels/Main_ViewModel.py`, the class `MainViewModel`, imported for you |
| `app.open_view("Window")` | `Views/Window_View.yaml`, the window (a `widget: Window` view) |
| `widget: Side` in a view | the view `Side`: `Views/Side_View.yaml`, or one of the views Tesserae ships; a name of yours wins |
| `App(custom_theme="Brand")` | `Themes/Brand_Theme.yaml` |
| `App(stylesheet="Page")` | `Styles/Page_Stylesheet.yaml` |

A **path** works wherever a name does: `app.open_view(HERE / "Views" / "Main_View.yaml")`. A string with a `/` or a `.` is a
path too, read from the folder you run in, so build it from `HERE` (the script's folder) and it works from anywhere. A name has
no `/` and no `.`. The older syntax finds more by name: `app.load("Main")` pairs a view
with its ViewModel, `component: Stat` finds `Components/Stat_Component.yaml`, and `Repeater(view, items, "Row", into=node)` and
`instantiate(view, "Row", into=node)` find `Views/Row_View.yaml` and its ViewModel.

The project's root is `App(root=...)`, which defaults to the folder of the script that runs (`app.py`).
`tesserae new` passes `root=HERE` so it doesn't depend on where you start it from.

A ViewModel is imported from its file, and its folder goes on Python's path, so a ViewModel can import another
by its file name (`from Helper_ViewModel import HelperViewModel`).

## More places to look

```python
app = App(root=HERE, search=["shared", "../common/ui"])
```

`search=` adds folders, relative to the root or absolute, to look in for every kind of file, after the
standard ones. `search=["."]` makes the root itself one of them, which is how an app whose files all sit side by side
(a flat folder, as in the [tutorial](../tutorial.md)) finds its views by name. To look through the whole project instead, give the app `recursive=True`: every folder under
the root is searched for every kind, except hidden folders, virtual environments, `__pycache__`,
`node_modules`, `build`, `dist` and `site`. It is slower in a big tree, and it finds files you didn't
mean to use, which is why it is opt-in.

```python
app = App(root=HERE, recursive=True)
```

## A name in two places

If two folders have a file with the same name, Tesserae stops and says so, rather than choose:

```text
ProjectError: Main_View.yaml is in two places, Views/Main_View.yaml and shared/Main_View.yaml: keep one, or name them differently
```

A name that is nowhere says where it looked:

```text
ProjectError: no view called 'Nope' (Nope_View.yaml) in Views under /home/you/notes: add the folder to App(search=[...]) or pass the file's path
```

## Adding to a project

`tesserae add screen Settings` writes `Views/Settings_View.yaml` and `ViewModels/Settings_ViewModel.py` and adds
`app.load("Settings")` and its route to `app.py` ([the command](cli.md#add-a-screen)). In a project written in the current
syntax a screen is a view in `Views/` with a `name:`, a ViewModel in `ViewModels/` that serves it, and a `bind` and an
`open_view` in `app.py`; a view you call is a file in `Views/`; a theme or a stylesheet is a file in `Themes/` or `Styles/`.
Nothing else needs registering.

The API is [`tesserae.project`](../api/python.md#projects); an app's is `app.project`.
