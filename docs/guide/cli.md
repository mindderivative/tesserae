# The `tesserae` Command

Installing Tesserae installs a `tesserae` command (`python -m tesserae` is the same).
It starts apps and screens from templates, builds an app into one executable, and finds
the editor schemas.

## Start an app

```bash
tesserae new notes
cd notes
python app.py
```

`notes/` has `app.py` and a `Home_View.yaml` / `Home_ViewModel.py` pair that follow the
[naming convention](naming-convention.md): a greeting from the app's
[shared state](apps-and-screens.md#shared-state) and a button that counts its clicks.
`app.py` gives Home the route `""`, so `python app.py <route>` opens on a screen by its
route (a [deep link](apps-and-screens.md#routes-and-deep-links)).

| Option | What it does |
| --- | --- |
| `--shell` | Adds an [app shell](app-shell.md) file, `Notes_Shell.yaml` (a top bar, a navigation rail over Home and Settings, a status bar), and a Settings screen. |
| `--custom-title-bar` | With `--shell`: no OS title bar. The shell's top bar is the [title bar](custom-title-bars.md): it moves the window and has the minimize, maximize and close buttons. The window is at least 640 by 400. |
| `--dir PARENT` | Makes the app in `PARENT` instead of here. |

Nothing is overwritten: a folder that isn't empty is refused with a one-line message (exit code 2).

## Add a screen

```bash
tesserae add screen Settings
```

This writes `Settings_View.yaml` and `Settings_ViewModel.py` (a title and a Back button that
calls `self.app.back()`) and adds its import, `app.load(...)` and route (`settings`) to
`app.py`, above the two marker comments `tesserae new` left there. Without the markers it
prints the lines to add. A CamelCase name gets a kebab-case route: `UserProfile` is
`user-profile`. `--dir` names the app's folder; a screen whose files exist is refused.

## Build an executable

```bash
pip install "tesserae-ui[build]"
tesserae build --check
```

Makes one file in `dist/` with every file under the app's folder inside it, and `--check` runs it
briefly to see it start. Options: `--name`, `--icon`, `--console`, `--include GLOB`,
`--exclude GLOB`, and for an installer `--installer` with `--app-version`, `--identifier`,
`--publisher` and `--description`. See [Releasing Your App](releasing.md).

## Find the editor schemas

```bash
tesserae schema            # where the YAML schemas are
tesserae schema --settings # the `yaml.schemas` setting for Red Hat's YAML language server
```

See [Editor Support](editor-support.md).
