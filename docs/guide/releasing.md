# Releasing Your App

When the app is ready for its users, `tesserae build` makes it one
executable file. The people you give it to run it like any other program:
they don't install Python, Tesserae or anything else.

```bash
pip install "tesserae-ui[build]"
cd notes
tesserae build --check
```

That makes `dist/notes` (`dist/notes.exe` on Windows). `--check` then runs
it briefly from an empty folder and says whether it drew frames and exited
cleanly:

```text
built /home/you/notes/dist/notes
checked: it drew 30 frames and exited cleanly
```

The `build` extra adds [PyInstaller](https://pyinstaller.org), which does
the building. It's kept out of the everyday `pip install tesserae-ui`, so
an app that's never released doesn't carry it; without it, `tesserae
build` tells you what to install.

## One platform at a time

An executable runs on the kind of computer it was built on: build on
Windows for Windows users, on a Mac for Mac users, on Linux for Linux
users. There's no cross-building. Tesserae's supported platforms are
Linux x86-64, macOS on Apple silicon and Windows x64.

If you don't have all three, a CI service can build on each. Tesserae's
own CI does this for a generated app on every push; the same steps in
GitHub Actions, for your app's repository:

```yaml
jobs:
  build:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      # Linux runners have no display: a virtual one, software Vulkan, and
      # the keyboard library winit loads for a window (desktops have these).
      - if: runner.os == 'Linux'
        run: sudo apt-get update && sudo apt-get install -y xvfb mesa-vulkan-drivers libxkbcommon-x11-0
      - run: pip install "tesserae-ui[build]"
      - shell: bash
        run: |
          if [ "$RUNNER_OS" = "Linux" ]; then RUN="xvfb-run -a"; else RUN=""; fi
          $RUN tesserae build --check
      - uses: actions/upload-artifact@v4
        with:
          name: app-${{ matrix.os }}
          path: dist/
```

## What goes in

Everything under the app's folder (the folder `app.py` is in), at the
same place relative to it: view and style files, images, fonts, the
ViewModels. The app's folder is scanned, rather than only what the app
opens at start-up, because an app opens files later too: a screen the
user navigates to, an app shell's panels, an image picked at run time.

Left out, wherever they are:

- `.git` and other hidden files and folders (a name starting with `.`),
- virtual environments (any folder with a `pyvenv.cfg`), and folders
  named `venv` or `env`,
- `build`, `dist`, `__pycache__` and `node_modules`,
- `*.pyc` and `*.spec` files.

Two options adjust that, each taking a glob on the path relative to the
app's folder, `/`-separated, and repeatable:

```bash
tesserae build --include .settings.yaml --exclude "notes/*.md" --exclude drafts
```

A folder that matches is taken, or left out, whole.

The app's own `.py` files also go through PyInstaller's import analysis,
so the libraries they import come along. A library that's only imported
in some unusual way (by a string name, say) may need PyInstaller's own
`--hidden-import`; `tesserae build` covers the usual case.

## Finding files in a built app

A `tesserae new` app finds its files next to `app.py`:

```python
HERE = Path(__file__).parent
app.load(HERE / "Home_View.yaml", HomeViewModel)
```

Keep doing that. In a built app, `__file__` is inside the folder the
executable unpacks itself into, where every bundled file is, so these
paths work wherever it's run from. A path relative to the *current*
folder (`Path("Home_View.yaml")`) works when you run `python app.py`
from the app's folder, and fails in a built app run from anywhere else;
`--check` runs from an empty folder to catch exactly that.

That unpacked folder is temporary: it's made fresh on each start and
removed when the app exits. So **don't write files next to `app.py`** —
settings, documents, a database. Save them in the user's own folders
instead (`Path.home()`, or a per-platform app-data folder, which the
[`platformdirs`](https://pypi.org/project/platformdirs/) library finds).

## Options

| Option | What it does |
|---|---|
| `app.py` (positional) | The app's entry point; defaults to `app.py` here. |
| `--name NAME` | The executable's name; defaults to the app's folder name. |
| `--icon FILE` | The executable's icon: `.ico` on Windows, `.icns` on macOS. |
| `--console` | Keeps a console window (Windows and macOS), to see the app's log while debugging. Without it there's none. |
| `--include GLOB` | Bundles files the scan leaves out. |
| `--exclude GLOB` | Leaves more files out. |
| `--check` | Runs the result for 30 frames from an empty folder. |

PyInstaller's working files go in a temporary folder, so the app's
folder gains only `dist/`.

## How it behaves

- **Start-up** takes a little longer than `python app.py`: the executable
  unpacks itself first (on Linux, about 0.55 s against 0.23 s for a
  `tesserae new` app).
- **Size:** a `tesserae new --shell` app is about 41 MB on Linux, 25 MB on
  macOS and 30 MB on Windows, most of it Python itself and `tre`'s engine.
- **Hot reload is off.** There are no source files to edit, so
  `app.run(hot_reload=True)` logs that and runs without it.
- **Its log** goes to the console when there is one (`--console`, or
  started from a terminal on Linux).

### Running it for a set number of frames

Two environment variables, which `--check` uses, work for any Tesserae
app, built or not, when an automated test or CI runs it:

- `TESSERAE_MAX_FRAMES=n` stops `app.run()` after `n` frames, unless the
  app passes `max_frames` itself.
- `TESSERAE_FRAMES_REPORT=<file>` writes how many frames the run drew to
  that file. With no display a run draws none and returns at once, so a
  clean exit alone doesn't show the app worked.

## On each platform

- **Linux:** the executable needs what any desktop has: a display, a
  Vulkan driver, and `libxkbcommon-x11`. It's also tied to the system
  library (glibc) of the machine it was built on, and runs on that
  version or newer: build on the oldest Linux you want to support.
- **macOS:** `dist/` holds the single executable, which runs from a
  terminal, and beside it a `notes.app` that PyInstaller makes for a
  build without a console. Unsigned, either is stopped by Gatekeeper the
  first time; since macOS 15 (Sequoia) the user allows it in System
  Settings › Privacy & Security › Open Anyway. PyInstaller 7 will refuse
  that `.app` beside a single file; M78's installers make a proper one.
- **Windows:** unsigned, SmartScreen warns the first time it's run.

Installers — a proper `.app` in a `.dmg`, a Windows installer with a
Start-menu entry, a Linux package — and signing are the next step for
Tesserae (M78).
