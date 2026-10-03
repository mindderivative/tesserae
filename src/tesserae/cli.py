"""`tesserae`, the command line: scaffolding for a new app.

    tesserae new <name> [--shell [--custom-title-bar]] [--dir PARENT]
    tesserae add screen <Name> [--dir DIR]
    tesserae build [app.py] [--name N] [--icon F] [--console] [--include G] [--exclude G] [--check]
    tesserae schema [--settings]

`new` makes `<name>/` with `app.py` and a `Home` View/ViewModel pair
following the naming convention, runnable at once; `--shell` adds an app
shell file and a `Settings` screen. `add screen` adds a pair and, at the
marker comments `new` leaves in `app.py`, its import, `load()` and route.
Neither overwrites a file. The templates are in `tesserae/templates/`.
`build` makes the app one executable: see `tesserae.build`.
`schema` (0.3.2) says where the YAML schemas for Red Hat's YAML language
server are, and with `--settings` prints the `yaml.schemas` setting for them.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from string import Template
from typing import Optional, Sequence

TEMPLATES = Path(__file__).parent / "templates"
#: The lines `tesserae new` leaves in `app.py`; `add screen` inserts above them.
IMPORT_MARKER = "# (tesserae add screen adds each new screen's import above this line)"
LOAD_MARKER = "# (tesserae add screen adds each new screen's load and route above this line)"
SCHEMAS = Path(__file__).parent / "schema"
#: Each YAML schema and the files it is for, as `yaml.schemas` globs (a `!` leaves files out).
SCHEMA_FILES = {
    "tesserae-yaml-schema.json": ["**/*_View.yaml"],
    "tesserae-shell-schema.json": ["**/*_Shell.yaml"],
    "tesserae-component-schema.json": ["**/*_Component.yaml"],
    # Themes and stylesheets (and a component's stylesheet): the suffixes, and a guess at other names.
    "tesserae-theme-schema.json": ["**/*_Theme.yaml", "**/*_Stylesheet.yaml", "**/*theme*.yaml", "**/*stylesheet*.yaml",
                                   "!**/*_View.yaml", "!**/*_Shell.yaml", "!**/*_Component.yaml"],
}


class CliError(Exception):
    """A mistake to report on one line: exit code 2."""


def _render(template: str, **values: str) -> str:
    return Template((TEMPLATES / template).read_text(encoding="utf-8")).substitute(values)


def _words(name: str) -> list[str]:
    """`my-notes`, `my_notes` and `MyNotes` are all `["my", "notes"]`."""
    spaced = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", name)
    return [w.lower() for w in re.split(r"[-_\s]+", spaced) if w]


def screen_route(name: str) -> str:
    """A screen's route: `Settings` is `settings`, `UserProfile` `user-profile`."""
    return "-".join(_words(name))


def _write(path: Path, text: str) -> None:
    if path.exists():
        raise CliError(f"{path} already exists; nothing was overwritten")
    path.write_text(text, encoding="utf-8")


#: The folders a project keeps its files in, found by name: see `tesserae.project`.
PROJECT_FOLDERS = ("Views", "ViewModels", "Components", "Themes", "Styles")


def _make_venv(folder: Path) -> None:
    """`.venv` in `folder`, with Tesserae installed in it."""
    try:
        subprocess.run([sys.executable, "-m", "venv", str(folder / ".venv")], check=True, capture_output=True)
        python = folder / ".venv" / ("Scripts" if os.name == "nt" else "bin") / ("python.exe" if os.name == "nt" else "python")
        version = _version()
        requirement = f"tesserae-ui>={version}" if version != "unknown" else "tesserae-ui"
        subprocess.run([str(python), "-m", "pip", "install", "-q", requirement], check=True, capture_output=True)
    except (subprocess.CalledProcessError, OSError) as exc:
        detail = (getattr(exc, "stderr", b"") or b"").decode(errors="replace").strip().splitlines()[-1:] or [str(exc)]
        raise CliError(f"made the project, but its virtual environment failed ({detail[0]}); in {folder} run "
                       "`python -m venv .venv`, then `.venv/bin/pip install tesserae-ui`") from None


def new(name: str, parent: Path, shell: bool = False, custom_title_bar: bool = False, venv: bool = True) -> Path:
    """Makes the project `name` in `parent` and returns its folder: its virtual environment (unless
    `venv=False`), the folders its files are found in, `app.py`, and a `Main` screen.
    `custom_title_bar` (with `shell`) makes its window undecorated,
    so the shell's top bar is its title bar."""
    if custom_title_bar and not shell:
        raise CliError("--custom-title-bar goes with --shell: the shell's top bar is the title bar "
                       "(without a shell, put a `kind: TitleBar` in a view)")
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", name):
        raise CliError(f"{name!r} isn't a project name: start with a letter; then letters, digits, - or _")
    folder = parent / name
    if folder.exists() and any(folder.iterdir()):
        raise CliError(f"{folder} isn't empty")
    folder.mkdir(parents=True, exist_ok=True)
    for sub in PROJECT_FOLDERS:
        (folder / sub).mkdir(exist_ok=True)
        if sub not in ("Views", "ViewModels"):
            (folder / sub / ".gitkeep").touch()  # an empty folder is kept by git
    words = _words(name)
    title = " ".join(w.capitalize() for w in words)
    camel = "".join(w.capitalize() for w in words)
    load_shell = f'app.load_shell("{camel}")  # Views/{camel}_Shell.yaml: a top bar, the rail, a status bar\n'
    size = {"width": "960", "height": "600"} if shell else {"width": "480", "height": "320"}
    window = (",\n          decorations=False, min_width=640, min_height=400"  # the shell's top bar is the title bar
              if custom_title_bar else "")
    _write(folder / "app.py", _render("app.py.tmpl", title=title, shell=load_shell if shell else "", window=window,
                                      **size))
    _write(folder / "Views" / "Main_View.yaml", _render("Main_View.yaml.tmpl"))
    _write(folder / "ViewModels" / "Main_ViewModel.py", _render("Main_ViewModel.py.tmpl"))
    if shell:
        _write(folder / "Views" / f"{camel}_Shell.yaml", _render("Shell.yaml.tmpl", title=title))
        add_screen("Settings", folder)
    if venv:
        _make_venv(folder)
    return folder


def add_screen(name: str, folder: Path) -> list[str]:
    """Adds the screen `name` (a `Name_View.yaml`/`Name_ViewModel.py` pair)
    to the app in `folder`, and its lines to `app.py` at the markers.
    Returns the lines it couldn't add (no `app.py`, or no markers)."""
    if not re.fullmatch(r"[A-Z][A-Za-z0-9]*", name):
        raise CliError(f"{name!r} isn't a screen name: CamelCase, starting with a capital (Settings, UserProfile)")
    if not folder.is_dir():
        raise CliError(f"{folder} isn't a folder")
    laid_out = (folder / "Views").is_dir() and (folder / "ViewModels").is_dir()  # a project, or the flat layout
    view = folder / "Views" / f"{name}_View.yaml" if laid_out else folder / f"{name}_View.yaml"
    viewmodel = folder / "ViewModels" / f"{name}_ViewModel.py" if laid_out else folder / f"{name}_ViewModel.py"
    for path in (view, viewmodel):  # both checked first, so a refusal writes neither
        if path.exists():
            raise CliError(f"{path} already exists; nothing was overwritten")
    title = " ".join(w.capitalize() for w in _words(name))
    _write(view, _render("Screen_View.yaml.tmpl", name=name, title=title))
    _write(viewmodel, _render("Screen_ViewModel.py.tmpl", name=name))
    route = f'app.route("{screen_route(name)}", "{name}")'
    app = folder / "app.py"
    text = app.read_text(encoding="utf-8") if app.is_file() else ""
    if laid_out:  # found by name: no import, no path
        imports, load_lines = [], [f'app.load("{name}")', route]
    else:
        imports = [f"from {name}_ViewModel import {name}ViewModel"]
        load_lines = [f'app.load(HERE / "{name}_View.yaml", {name}ViewModel)', route]
    if LOAD_MARKER not in text or (imports and IMPORT_MARKER not in text):
        return [*imports, *load_lines]
    if imports:
        text = text.replace(IMPORT_MARKER, f"{imports[0]}\n{IMPORT_MARKER}", 1)
    text = text.replace(LOAD_MARKER, "\n".join([*load_lines, LOAD_MARKER]), 1)
    app.write_text(text, encoding="utf-8")
    return []


def _version() -> str:
    from importlib.metadata import PackageNotFoundError, version

    try:
        return version("tesserae-ui")
    except PackageNotFoundError:  # a checkout that isn't installed
        return "unknown"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tesserae", description="Scaffolding for Tesserae apps.")
    parser.add_argument("--version", action="version", version=f"tesserae {_version()}")
    commands = parser.add_subparsers(dest="command", required=True)
    new_cmd = commands.add_parser("new", help="make a new app")
    new_cmd.add_argument("name", help="the app's folder name, e.g. notes or my-notes")
    new_cmd.add_argument("--shell", action="store_true",
                         help="add an app shell (top bar, rail, status bar) and a Settings screen")
    new_cmd.add_argument("--dir", type=Path, default=Path("."), help="where to make it (default: here)")
    new_cmd.add_argument("--no-venv", action="store_true", help="don't make a virtual environment in the project")
    new_cmd.add_argument("--custom-title-bar", action="store_true",
                         help="with --shell: no OS title bar; the shell's top bar is the title bar")
    add_cmd = commands.add_parser("add", help="add to an app")
    what = add_cmd.add_subparsers(dest="what", required=True)
    screen_cmd = what.add_parser("screen", help="add a screen: a View/ViewModel pair")
    screen_cmd.add_argument("name", help="the screen's CamelCase name, e.g. Settings")
    screen_cmd.add_argument("--dir", type=Path, default=Path("."), help="the app's folder (default: here)")
    schema_cmd = commands.add_parser("schema", help="where the YAML schemas for editors are")
    schema_cmd.add_argument("--settings", action="store_true",
                            help="print the `yaml.schemas` setting for Red Hat's YAML language server")
    build_cmd = commands.add_parser("build", help="build the app into one executable (needs tesserae-ui[build])")
    build_cmd.add_argument("app", nargs="?", type=Path, default=Path("app.py"),
                           help="the app's entry point (default: app.py)")
    build_cmd.add_argument("--name", help="the executable's name (default: the app's folder name)")
    build_cmd.add_argument("--icon", type=Path, help="an icon file (.ico on Windows, .icns on macOS)")
    build_cmd.add_argument("--console", action="store_true", help="keep a console window (Windows and macOS)")
    build_cmd.add_argument("--include", action="append", default=[], metavar="GLOB",
                           help="bundle files the scan skips, e.g. .config (repeatable)")
    build_cmd.add_argument("--exclude", action="append", default=[], metavar="GLOB",
                           help="leave files out, e.g. 'notes/*.md' (repeatable)")
    build_cmd.add_argument("--check", action="store_true", help="run the executable briefly to check it starts")
    build_cmd.add_argument("--installer", action="store_true",
                           help="make this platform's installer (macOS: a .app in a .dmg)")
    build_cmd.add_argument("--app-version", default="0.1.0", help="the installer's version, e.g. 1.2.0")
    build_cmd.add_argument("--identifier", help="reverse-DNS, e.g. com.yourcompany.notes")
    build_cmd.add_argument("--publisher", default="", help="who makes the app")
    build_cmd.add_argument("--description", default="", help="a line about the app")
    return parser


def _schema(args: argparse.Namespace) -> int:
    """Prints the schemas' places, or the setting that maps them to their files."""
    import json

    missing = [name for name in SCHEMA_FILES if not (SCHEMAS / name).is_file()]
    if missing:
        raise CliError(f"this install has no {', '.join(missing)}")
    if args.settings:
        print(json.dumps({"yaml.schemas": {str(SCHEMAS / name): globs for name, globs in SCHEMA_FILES.items()}}, indent=2))
        return 0
    for name, globs in SCHEMA_FILES.items():
        print(f"{SCHEMAS / name}\n    for {', '.join(g for g in globs if not g.startswith('!'))}")
    print("\nFor Red Hat's YAML language server, `tesserae schema --settings` prints the setting. See "
          "https://mindderivative.github.io/tesserae/guide/editor-support/")
    return 0


def _build(args: argparse.Namespace) -> int:
    from tesserae import build

    try:
        info = build.AppInfo(args.name or Path(args.app).resolve().parent.name, args.app_version, args.identifier,
                             args.publisher, args.description)
        built = build.build(args.app, name=args.name, icon=args.icon, console=args.console, include=args.include,
                            exclude=args.exclude, installer=args.installer, info=info)
    except build.BuildError as exc:
        raise CliError(str(exc)) from None
    executable = built.executable
    print(f"built {executable}")
    for made in built.installers:
        print(f"made {made}")
    for skipped in built.skipped:
        print(f"skipped {skipped}")
    if args.installer and info.placeholder_identifier:
        print(f"note: the identifier is a placeholder, {info.identifier}; give yours with --identifier "
              "before releasing")
    if args.check:
        result = build.check(executable)
        if result.returncode != 0:
            print(f"tesserae: {executable.name} exited with {result.returncode}:\n{result.stderr}", file=sys.stderr)
            return 1
        if result.frames == 0:
            print(f"tesserae: {executable.name} exited cleanly but drew no frames: is there a display to open "
                  f"a window on?\n{result.stderr}", file=sys.stderr)
            return 1
        print(f"checked: it drew {result.frames} frames and exited cleanly")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    """The `tesserae` command. Returns its exit code: 2 for a mistake,
    reported on one line."""
    args = _parser().parse_args(argv)
    try:
        if args.command == "build":
            return _build(args)
        if args.command == "schema":
            return _schema(args)
        if args.command == "new":
            folder = new(args.name, args.dir, shell=args.shell, custom_title_bar=args.custom_title_bar,
                         venv=not args.no_venv)
            activate = "source .venv/bin/activate" if os.name != "nt" else r".venv\Scripts\activate"
            steps = f"cd {folder}\n    " + (f"{activate}\n    " if not args.no_venv else "") + "python app.py"
            print(f"made {folder}; run it with\n\n    {steps}\n")
        else:
            missing = add_screen(args.name, args.dir)
            if missing:
                print(f"added {args.name}_View.yaml and {args.name}_ViewModel.py; app.py has no markers, "
                      "so add these lines to it:\n\n    " + "\n    ".join(missing) + "\n")
            else:
                print(f"added {args.name}_View.yaml and {args.name}_ViewModel.py, and loaded it in app.py "
                      f"with the route {screen_route(args.name)!r}")
    except CliError as exc:
        print(f"tesserae: {exc}", file=sys.stderr)
        return 2
    return 0
