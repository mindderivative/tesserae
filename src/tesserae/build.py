"""`tesserae build` (M77): an app as one executable, with PyInstaller.

    tesserae build [app.py] [--name NAME] [--icon FILE] [--console]
                   [--include GLOB]... [--exclude GLOB]... [--check]

The app's folder is scanned rather than traced: an app loads files at any
time -- a screen opened later, a shell file's panels (whose
`*_ViewModel.py` it imports by path), an image or style file picked at
run time -- so every file under the folder goes into the executable at
the same relative place, except `.git`, virtual environments, `build`,
`dist`, `__pycache__` and hidden files; `--include`/`--exclude` globs
adjust that. The app's `.py` files are also analysed, so what they
import comes along. The result is `dist/<name>` (`.exe` on Windows), with
no console window on Windows and macOS unless `--console`. `--check`
runs it with `TESSERAE_MAX_FRAMES` set and reports whether it drew
frames and exited cleanly. An executable is built for the platform it's built on.

PyInstaller is an extra: `pip install tesserae-ui[build]`.
"""

from __future__ import annotations

import fnmatch
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

#: Folders never bundled, wherever they are in the app.
SKIPPED_DIRS = frozenset({"build", "dist", "__pycache__", "venv", "env", "node_modules"})
#: How many frames `--check` runs the executable for.
CHECK_FRAMES = 30


class BuildError(Exception):
    """A build that can't go ahead or didn't work, said on one line."""


@dataclass
class Collected:
    """What goes in: `files` are `(source, folder inside the app)`;
    `modules` the app's Python modules (by name) and `paths` their folders,
    for PyInstaller to analyse."""

    files: list[tuple[Path, str]]
    modules: list[str]
    paths: list[Path]


def _matches(relative: str, globs: Iterable[str]) -> bool:
    return any(fnmatch.fnmatch(relative, g) for g in globs)  # a folder that matches goes (or stays) whole


def collect_files(app_file: Path, include: Sequence[str] = (), exclude: Sequence[str] = ()) -> Collected:
    """The files under `app_file`'s folder that go into the executable.
    `include` globs (relative, `/`-separated paths) add back what the
    default skips; `exclude` globs leave out more."""
    root = app_file.parent
    files: list[tuple[Path, str]] = []
    modules: list[str] = []
    paths: set[Path] = set()
    for folder, dirs, names in os.walk(root):
        here = Path(folder)
        rel_dir = here.relative_to(root).as_posix()
        prefix = "" if rel_dir == "." else f"{rel_dir}/"
        kept = []
        for d in sorted(dirs):
            skipped = d in SKIPPED_DIRS or d.startswith(".") or (here / d / "pyvenv.cfg").is_file()
            if (not skipped or _matches(prefix + d, include)) and not _matches(prefix + d, exclude):
                kept.append(d)
        dirs[:] = kept
        for name in sorted(names):
            skipped = name.startswith(".") or name.endswith((".pyc", ".spec"))
            if (skipped and not _matches(prefix + name, include)) or _matches(prefix + name, exclude):
                continue
            path = here / name
            files.append((path, rel_dir))
            if name.endswith(".py") and path != app_file:
                modules.append(path.stem)
                paths.add(here)
    return Collected(files, modules, sorted(paths))


def pyinstaller_args(app_file: Path, name: str, collected: Collected, work: Path, dist: Path, *,
                     icon: Path | None = None, console: bool = False) -> list[str]:
    """PyInstaller's command line for the build."""
    args = [str(app_file), "--onefile", "--noconfirm", "--clean", "--name", name,
            "--distpath", str(dist), "--workpath", str(work / "build"), "--specpath", str(work),
            "--collect-data", "tesserae", "--collect-submodules", "tesserae",
            "--paths", str(app_file.parent)]
    for path in collected.paths:
        args += ["--paths", str(path)]
    for module in collected.modules:
        args += ["--hidden-import", module]
    for source, folder in collected.files:
        args += ["--add-data", f"{source}{os.pathsep}{folder}"]
    if not console:
        args.append("--windowed")  # no console window on Windows and macOS; nothing changes on Linux
    if icon is not None:
        args += ["--icon", str(icon)]
    return args


def executable_path(dist: Path, name: str) -> Path:
    return dist / (f"{name}.exe" if sys.platform == "win32" else name)


def build(app_file: str | Path = "app.py", *, name: str | None = None, icon: str | Path | None = None,
          console: bool = False, include: Sequence[str] = (), exclude: Sequence[str] = (),
          dist: str | Path | None = None) -> Path:
    """Builds `app_file`'s app into one executable and returns its path."""
    app_file = Path(app_file).resolve()
    if not app_file.is_file():
        raise BuildError(f"{app_file} isn't a file: give the app's entry point (app.py)")
    icon_path = Path(icon).resolve() if icon is not None else None
    if icon_path is not None and not icon_path.is_file():
        raise BuildError(f"{icon_path} isn't a file")
    try:
        import PyInstaller.__main__ as pyinstaller
    except ImportError:
        raise BuildError("building needs PyInstaller: pip install tesserae-ui[build]") from None
    name = name or app_file.parent.name
    dist_path = Path(dist).resolve() if dist is not None else app_file.parent / "dist"
    collected = collect_files(app_file, include, exclude)
    with tempfile.TemporaryDirectory(prefix="tesserae-build-") as work:
        pyinstaller.run(pyinstaller_args(app_file, name, collected, Path(work), dist_path,
                                         icon=icon_path, console=console))
    result = executable_path(dist_path, name)
    if not result.is_file():
        raise BuildError(f"PyInstaller finished without making {result}")
    return result


@dataclass
class Checked:
    """How a `check` went: the exit code, the frames the app drew (0 if it
    found no display, or never got as far as `App.run`), and its stderr."""

    returncode: int
    frames: int
    stderr: str


def check(executable: Path, frames: int = CHECK_FRAMES, timeout: float = 120.0) -> Checked:
    """Runs a built executable for `frames` frames from a folder of its own
    (so it can't lean on the app's files) and returns how it went."""
    with tempfile.TemporaryDirectory(prefix="tesserae-check-") as elsewhere:
        report = Path(elsewhere, "frames.txt")
        result = subprocess.run([str(executable)], cwd=elsewhere, capture_output=True, text=True, timeout=timeout,
                                env={**os.environ, "TESSERAE_MAX_FRAMES": str(frames),
                                     "TESSERAE_FRAMES_REPORT": str(report)})
        drawn = int(report.read_text(encoding="utf-8")) if report.is_file() else 0
    return Checked(result.returncode, drawn, result.stderr)
