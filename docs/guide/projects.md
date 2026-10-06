# Projects

A project is a folder with a place for each kind of file. Tesserae finds a file by its name, so
`app.load("Main")` is enough and a view says `component: Stat` without a path. `tesserae new` makes one:

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
  Views/              Main_View.yaml, and Name_Shell.yaml
  ViewModels/         Main_ViewModel.py
  Components/         Name_Component.yaml, and Name_Stylesheet.yaml for its look
  Themes/             Name_Theme.yaml
  Styles/             Name_Stylesheet.yaml, Name_Style.yaml
```

The [project tutorial](../tutorial-project.md) builds an app in one, step by step, beside the
[flat-folder tutorial](../tutorial.md).

`--no-venv` makes the folders and files without the virtual environment (the environment needs the network to
install Tesserae). [The `tesserae` command](cli.md) has the rest.

## Finding files by name

| You write | Tesserae opens |
| --- | --- |
| `app.load("Main")` | `Views/Main_View.yaml`, and `Main`'s ViewModel: `ViewModels/Main_ViewModel.py`, class `MainViewModel` |
| `app.load_shell("Frame")` | `Views/Frame_Shell.yaml` |
| `Repeater(view, items, "Row", into=node)` and `instantiate(view, "Row", into=node)` | `Views/Row_View.yaml`, and `Row`'s ViewModel (`RowViewModel`), as `app.load` does |
| `component: Stat` | `Components/Stat_Component.yaml`, and `Components/Stat_Stylesheet.yaml` |
| `App(custom_theme="Brand")` | `Themes/Brand_Theme.yaml` |
| `App(stylesheet="Page")` or `load(..., stylesheet="Page")` | `Styles/Page_Stylesheet.yaml` |
| `style: row_Style.yaml` | next to the view, or in `Styles/` |
| a panel `Side` in a shell file | the screen `Side`, or `Views/Side_View.yaml` |

A **path** works wherever a name does, as it always has: `app.load("Views/Main_View.yaml")`, or a `Path`.
A name has no `/` and no `.`. Fragments and style files next to the view are still found first.

The project's root is `App(root=...)`, which defaults to the folder of the script that runs (`app.py`).
`tesserae new` passes `root=HERE` so it doesn't depend on where you start it from.

A ViewModel is imported from its file, and its folder goes on Python's path, so a ViewModel can import another
by its file name (`from Helper_ViewModel import HelperViewModel`).

## More places to look

```python
app = App(root=HERE, search=["shared", "../common/ui"])
```

`search=` adds folders, relative to the root or absolute, to look in for every kind of file, after the
standard ones. To look through the whole project instead, give the app `recursive=True`: every folder under
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
`app.load("Settings")` and its route to `app.py`. A component is a file in `Components/`; a theme, a stylesheet or a
style file is a file in `Themes/` or `Styles/`. Nothing needs registering: hot reload watches what a view uses.

The API is [`tesserae.project`](../api/python.md#projects); an app's is `app.project`.
