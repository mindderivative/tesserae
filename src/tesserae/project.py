"""A project's files, found by name.

A project is a folder with standard places for each kind of file:

    Views/        Name_View.yaml, Name_Shell.yaml
    ViewModels/   Name_ViewModel.py
    Components/   Name_Component.yaml (and Name_Stylesheet.yaml, its look)
    Themes/       Name_Theme.yaml
    Styles/       Name_Stylesheet.yaml, Name_Style.yaml

`App(root=...)` is the project's root (the folder `app.py` is in, by default). `search=[...]` adds folders to
look in, for every kind; `recursive=True` looks through the whole project instead. A name that is in two places
is an error naming both, not a choice made for you. A path still works wherever a name does.
"""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from typing import Any, Iterable, Optional

__all__ = ["KINDS", "Project", "ProjectError", "is_name", "project_of", "resolve_view"]

#: Each kind of file: the end of its name, and the folders it is kept in.
KINDS: dict[str, tuple[str, tuple[str, ...]]] = {
    "view": ("_View.yaml", ("Views",)),
    "shell": ("_Shell.yaml", ("Views",)),
    "viewmodel": ("_ViewModel.py", ("ViewModels",)),
    "component": ("_Component.yaml", ("Components",)),
    "theme": ("_Theme.yaml", ("Themes",)),
    "stylesheet": ("_Stylesheet.yaml", ("Styles",)),
    "style": ("_Style.yaml", ("Styles",)),
}
#: Folders a whole-project search never goes into.
_SKIPPED = frozenset({"__pycache__", "node_modules", "build", "dist", "site", "site-packages"})


class ProjectError(LookupError):
    """A name that is nowhere, or in two places."""


def is_name(ref: Any) -> bool:
    """Whether `ref` is a bare name (`"Main"`), not a path (`"Views/Main_View.yaml"`, a `Path`)."""
    return isinstance(ref, str) and ref != "" and not any(c in ref for c in ("/", "\\")) and "." not in ref


class Project:
    """The files under `root`, found by name. See the module docstring."""

    def __init__(self, root: str | Path, search: Iterable[str | Path] = (), recursive: bool = False) -> None:
        self.root = Path(root).resolve()
        self.search = [Path(folder) for folder in search]
        self.recursive = recursive
        self._indexes: dict[str, dict[str, list[Path]]] = {}

    # -- where to look --------------------------------------------------------------------

    def folders(self, kind: str) -> list[Path]:
        """The folders that exist where `kind` is looked for, in order; with `recursive`, every folder under the root."""
        standard = KINDS[kind][1]
        found = [self.root / name for name in standard] + [folder if folder.is_absolute() else self.root / folder
                                                            for folder in self.search]
        folders = [folder for folder in found if folder.is_dir()]
        if self.recursive:
            folders = [self.root, *self._subfolders()]
        return folders

    def _subfolders(self) -> list[Path]:
        out: list[Path] = []
        for current, names, _ in os.walk(self.root):
            names[:] = sorted(n for n in names if not n.startswith(".") and n not in _SKIPPED
                              and not (Path(current, n) / "pyvenv.cfg").exists())
            out += [Path(current, n) for n in names]
        return out

    # -- finding --------------------------------------------------------------------------

    def _scan(self, kind: str) -> dict[str, list[Path]]:
        suffix = KINDS[kind][0]
        index: dict[str, list[Path]] = {}
        for folder in self.folders(kind):
            for path in sorted(folder.glob(f"*{suffix}")):
                if path.is_file():
                    index.setdefault(path.name.removesuffix(suffix), []).append(path)
        return index

    def index(self, kind: str) -> dict[str, Path]:
        """Every name of `kind` and its file. Raises `ProjectError` for a name in two places."""
        found = self._scan(kind)
        for name, paths in found.items():
            if len(paths) > 1:
                where = " and ".join(str(p.relative_to(self.root)) if p.is_relative_to(self.root) else str(p) for p in paths)
                raise ProjectError(f"{name}{KINDS[kind][0]} is in two places, {where}: keep one, or name them differently")
        return {name: paths[0] for name, paths in found.items()}

    def find(self, kind: str, name: str) -> Path:
        """The file of `kind` called `name`; `ProjectError` if there is none, or two."""
        index = self.index(kind)
        if name not in index:
            looked = ", ".join(str(f.relative_to(self.root)) if f.is_relative_to(self.root) else str(f)
                               for f in self.folders(kind)) or "no folder yet"
            raise ProjectError(f"no {kind} called {name!r} ({name}{KINDS[kind][0]}) in {looked}"
                               f" under {self.root}: add the folder to App(search=[...]) or pass the file's path")
        return index[name]

    def resolve(self, kind: str, ref: str | Path) -> Path:
        """`ref` as a file: a path is used as it is, a bare name is found."""
        return self.find(kind, ref) if is_name(ref) else Path(ref)

    def component_dirs(self) -> list[Path]:
        """The folders the components are in (each once), for `component:` to look in. A name in two is an error."""
        self.index("component")
        out: list[Path] = []
        for folder in self.folders("component"):
            if any(folder.glob(f"*{KINDS['component'][0]}")) or any(folder.glob(f"*{KINDS['stylesheet'][0]}")):
                out.append(folder)
        return out

    def style_dirs(self) -> list[Path]:
        """The folders that have `*_Style.yaml` files, for a node's `style:` that names one."""
        return [folder for folder in self.folders("style") if any(folder.glob(f"*{KINDS['style'][0]}"))]

    # -- ViewModels -----------------------------------------------------------------------

    def viewmodel(self, name: str) -> type:
        """The class `NameViewModel` in `Name_ViewModel.py`, imported. Its folder goes on `sys.path`, so the
        ViewModels can import each other by their file names."""
        path = self.find("viewmodel", name)
        return load_viewmodel(path, name)


def project_of(parent: Any) -> Optional[Project]:
    """The project of the app that `parent` (a view, a component, a window) is in, or `None`."""
    from tesserae.follow import app_of

    app = app_of(getattr(parent, "window", parent))
    return app.project if app is not None else None


def resolve_view(project: Optional[Project], ref: str | Path, viewmodel_cls: Optional[type] = None) -> tuple[Path, type]:
    """The view file and the ViewModel class for `ref`: a path, or a name found in `project`. A class left out is
    found by the view's name, beside the view (`Name_ViewModel.py`) or in the project. One rule for `app.load`,
    `instantiate` and `Repeater`."""
    if is_name(ref):
        if project is None:
            raise ProjectError(f"{ref!r} is a name, but there is no project to look in: it needs an App "
                               "(its root and folders), or pass the file's path")
        path = project.find("view", ref)
    else:
        path = Path(ref)
    if viewmodel_cls is None:
        prefix = path.name.removesuffix(KINDS["view"][0])
        beside = path.with_name(f"{prefix}{KINDS['viewmodel'][0]}")
        if path.name.endswith(KINDS["view"][0]) and beside.is_file():
            viewmodel_cls = load_viewmodel(beside, prefix)
        elif project is not None:
            viewmodel_cls = project.viewmodel(prefix)
        else:
            raise ProjectError(f"no ViewModel class given, and {beside.name} isn't beside {path.name} "
                               "(and there is no project to look in)")
    return path, viewmodel_cls


def load_viewmodel(path: Path, name: str) -> type:
    """The class `<name>ViewModel` from the file `path`."""
    folder = str(path.parent)
    if folder not in sys.path:
        sys.path.insert(0, folder)
    module_name = path.stem
    existing = sys.modules.get(module_name)
    if existing is not None and Path(getattr(existing, "__file__", "") or "").resolve() != path.resolve():
        raise ProjectError(f"{module_name} is already imported from {existing.__file__}, not {path}")
    module = importlib.import_module(module_name)
    wanted = f"{name}ViewModel"
    cls: Optional[type] = getattr(module, wanted, None)
    if not isinstance(cls, type):
        classes = ", ".join(sorted(n for n, v in vars(module).items() if isinstance(v, type) and n.endswith("ViewModel")))
        raise ProjectError(f"{path.name} has no class {wanted}" + (f" (it has {classes})" if classes else ""))
    return cls
