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
no console window on Windows unless `--console` (on macOS it runs from a
terminal; its `.app` comes with `--installer`). `--check`
runs it with `TESSERAE_MAX_FRAMES` set and reports whether it drew
frames and exited cleanly. An executable is built for the platform it's built on.

`--installer` (M78) makes this platform's installer instead, from a
one-folder build (which starts faster than one file): on macOS a `.app`
in a `.dmg`. `--app-version`, `--identifier`, `--publisher` and
`--description` fill in its details, and a PNG `--icon` is made into the
platform's own format.

PyInstaller is an extra: `pip install tesserae-ui[build]`.
"""

from __future__ import annotations

import fnmatch
import os
import plistlib
import re
import shutil
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
                     icon: Path | None = None, console: bool = False, onefile: bool = True) -> list[str]:
    """PyInstaller's command line for the build: one file, or (for an
    installer) one folder, which on macOS is a `.app`."""
    args = [str(app_file), "--onefile" if onefile else "--onedir", "--noconfirm", "--clean", "--name", name,
            "--distpath", str(dist), "--workpath", str(work / "build"), "--specpath", str(work),
            "--collect-data", "tesserae", "--collect-submodules", "tesserae",
            "--paths", str(app_file.parent)]
    for path in collected.paths:
        args += ["--paths", str(path)]
    for module in collected.modules:
        args += ["--hidden-import", module]
    for source, folder in collected.files:
        args += ["--add-data", f"{source}{os.pathsep}{folder}"]
    # No console window on Windows, and a `.app` on macOS -- but not from one
    # file there, which PyInstaller 7 refuses (M78): that one runs from a
    # terminal. Nothing changes on Linux.
    if not console and not (onefile and sys.platform == "darwin"):
        args.append("--windowed")
    if icon is not None:
        args += ["--icon", str(icon)]
    return args


def executable_path(dist: Path, name: str) -> Path:
    return dist / (f"{name}.exe" if sys.platform == "win32" else name)


# -- an installer's details (M78) -----------------------------------------------

@dataclass
class AppInfo:
    """What an installer says about the app. `identifier` is reverse-DNS
    (`com.yourcompany.notes`): macOS keys the app's settings on it and
    Windows its install."""

    name: str
    version: str = "0.1.0"
    identifier: str | None = None
    publisher: str = ""
    description: str = ""

    def __post_init__(self) -> None:
        if not re.fullmatch(r"\d+(\.\d+){0,3}", self.version):
            raise BuildError(f"version {self.version!r} isn't one installers take: numbers and dots, "
                             "like 1.2 or 1.2.3")
        if self.identifier is None:
            self.identifier = f"com.example.{slug(self.name)}"
        elif not re.fullmatch(r"[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+", self.identifier):
            raise BuildError(f"identifier {self.identifier!r} isn't reverse-DNS, like com.yourcompany.notes")

    @property
    def placeholder_identifier(self) -> bool:
        return self.identifier == f"com.example.{slug(self.name)}"


def slug(name: str) -> str:
    """`name` as a lower-case word with dashes: `Demo App` is `demo-app`."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "app"


def platform_icon(icon: Path | None, work: Path) -> Path | None:
    """The icon PyInstaller wants here: a PNG becomes an `.ico` on Windows
    and an `.icns` on macOS (with Pillow); anything else is used as given."""
    if icon is None or icon.suffix.lower() != ".png" or sys.platform not in ("win32", "darwin"):
        return icon
    from PIL import Image

    image = Image.open(icon).convert("RGBA")
    if sys.platform == "win32":
        out = work / f"{icon.stem}.ico"
        image.save(out, sizes=[(s, s) for s in (16, 24, 32, 48, 64, 128, 256)])
    else:
        out = work / f"{icon.stem}.icns"
        image.resize((1024, 1024)).save(out)
    return out


# -- building -------------------------------------------------------------------

@dataclass
class Built:
    """What a build made: `executable`, what `--check` runs, and
    `installers`, what to give users (none for a single file, which is
    itself the thing to give)."""

    executable: Path
    installers: list[Path]


def _pyinstaller():
    try:
        import PyInstaller.__main__ as pyinstaller
    except ImportError:
        raise BuildError("building needs PyInstaller: pip install tesserae-ui[build]") from None
    return pyinstaller


def build(app_file: str | Path = "app.py", *, name: str | None = None, icon: str | Path | None = None,
          console: bool = False, include: Sequence[str] = (), exclude: Sequence[str] = (),
          dist: str | Path | None = None, installer: bool = False, info: AppInfo | None = None) -> Built:
    """Builds `app_file`'s app into one executable, or with `installer`
    into this platform's installer, in `dist` (the app's `dist/`)."""
    app_file = Path(app_file).resolve()
    if not app_file.is_file():
        raise BuildError(f"{app_file} isn't a file: give the app's entry point (app.py)")
    icon_path = Path(icon).resolve() if icon is not None else None
    if icon_path is not None and not icon_path.is_file():
        raise BuildError(f"{icon_path} isn't a file")
    name = name or app_file.parent.name
    info = info or AppInfo(name)
    if installer and sys.platform not in _INSTALLERS:
        raise BuildError(f"--installer isn't ready on {sys.platform} yet; tesserae build without it makes "
                         "a single executable")
    pyinstaller = _pyinstaller()
    dist_path = Path(dist).resolve() if dist is not None else app_file.parent / "dist"
    collected = collect_files(app_file, include, exclude)
    with tempfile.TemporaryDirectory(prefix="tesserae-build-") as tmp:
        work = Path(tmp)
        args = pyinstaller_args(app_file, name, collected, work, work / "dist" if installer else dist_path,
                                icon=platform_icon(icon_path, work), console=console, onefile=not installer)
        pyinstaller.run(args)
        if installer:
            return _INSTALLERS[sys.platform](work / "dist", name, info, dist_path)
    result = executable_path(dist_path, name)
    if not result.is_file():
        raise BuildError(f"PyInstaller finished without making {result}")
    return Built(result, [])


def _run(command: list[str]) -> None:
    """Runs a packaging tool, raising its own words if it fails."""
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise BuildError(f"{Path(command[0]).name} failed ({result.returncode}): "
                         f"{(result.stderr or result.stdout).strip()}")


def _macos(built: Path, name: str, info: AppInfo, dist: Path) -> Built:
    """The `.app` (with the installer's details in its `Info.plist`, then
    signed again, ad hoc, since the edit breaks PyInstaller's signature and
    Apple silicon runs nothing unsigned) and a `.dmg` holding it beside a
    link to Applications, to drag it to."""
    app = built / f"{name}.app"
    if not app.is_dir():
        raise BuildError(f"PyInstaller finished without making {app}")
    plist_path = app / "Contents" / "Info.plist"
    with plist_path.open("rb") as f:
        plist = plistlib.load(f)
    plist.update({"CFBundleShortVersionString": info.version, "CFBundleVersion": info.version,
                  "CFBundleDisplayName": name, "CFBundleIdentifier": info.identifier})
    if info.publisher:
        plist["NSHumanReadableCopyright"] = info.publisher
    with plist_path.open("wb") as f:
        plistlib.dump(plist, f)
    _run(["codesign", "--force", "--deep", "--sign", "-", str(app)])
    dist.mkdir(parents=True, exist_ok=True)
    final = dist / app.name
    if final.exists():
        shutil.rmtree(final)
    shutil.copytree(app, final, symlinks=True)
    staging = built / "dmg"
    staging.mkdir()
    shutil.copytree(app, staging / app.name, symlinks=True)
    (staging / "Applications").symlink_to("/Applications")
    dmg = dist / f"{name}-{info.version}.dmg"
    _run(["hdiutil", "create", "-volname", name, "-srcfolder", str(staging), "-ov", "-format", "UDZO", str(dmg)])
    return Built(final / "Contents" / "MacOS" / name, [dmg])


#: Each platform's installer, from PyInstaller's one-folder build.
_INSTALLERS = {"darwin": _macos}


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
