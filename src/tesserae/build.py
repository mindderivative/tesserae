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
import hashlib
import io
import os
import plistlib
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import time
import tempfile
import urllib.request
import uuid
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
        for field in ("name", "publisher", "description"):
            if any(c in getattr(self, field) for c in "\r\n"):
                raise BuildError(f"the app's {field} can't span lines")

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
            return _INSTALLERS[sys.platform](work / "dist", name, info, dist_path, platform_icon(icon_path, work))
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


def _macos(built: Path, name: str, info: AppInfo, dist: Path, icon: Path | None = None) -> Built:
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


# -- Windows: Inno Setup (M78) --------------------------------------------------

#: The Inno Setup Tesserae fetches when there's none here: pinned, and
#: checked against GitHub's own digest for the release asset.
INNO_VERSION = "7.1.0"
INNO_URL = f"https://github.com/jrsoftware/issrc/releases/download/is-7_1_0/innosetup-{INNO_VERSION}-x64.exe"
INNO_SHA256 = "0362a383ed217d4c4239b5933866dd96d3eb2102737da92f80f6057a4b40df2f"


def tools_dir() -> Path:
    """Where Tesserae keeps the packaging tools it fetches."""
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache"
    return Path(base) / "tesserae" / "tools"


def find_iscc() -> Path | None:
    """Inno Setup's compiler: `TESSERAE_ISCC`, then the PATH, then where
    Inno Setup 7 or 6 installs (for everyone or per user), then the copy
    Tesserae fetched."""
    if os.environ.get("TESSERAE_ISCC"):
        return Path(os.environ["TESSERAE_ISCC"])
    on_path = shutil.which("iscc")
    if on_path:
        return Path(on_path)
    roots = [os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles")]
    if os.environ.get("LOCALAPPDATA"):
        roots.append(str(Path(os.environ["LOCALAPPDATA"]) / "Programs"))
    for root in filter(None, roots):
        for version in ("7", "6"):
            candidate = Path(root) / f"Inno Setup {version}" / "ISCC.exe"
            if candidate.is_file():
                return candidate
    cached = tools_dir() / f"innosetup-{INNO_VERSION}" / "ISCC.exe"
    return cached if cached.is_file() else None


def _download(url: str, to: Path) -> None:
    with urllib.request.urlopen(url, timeout=120) as response, to.open("wb") as out:
        shutil.copyfileobj(response, out)


def _fetch(what: str, url: str, sha256: str, to: Path) -> Path:
    """Downloads `url` to `to` (once: a file already there is kept) and
    checks it against its pinned SHA-256, deleting it if it doesn't match."""
    if to.is_file():
        return to
    to.parent.mkdir(parents=True, exist_ok=True)
    print(f"fetching {what} from {url.split('/releases/')[0].removeprefix('https://')}, once, into {to.parent}")
    _download(url, to)
    digest = hashlib.sha256(to.read_bytes()).hexdigest()
    if digest != sha256:
        to.unlink()
        raise BuildError(f"the {what} download's SHA-256 is {digest}, not {sha256}: not using it")
    return to


def fetch_iscc() -> Path:
    """Fetches the pinned Inno Setup into `tools_dir()`, checks its
    digest, and unpacks it there in portable mode (installing nothing)."""
    tools = tools_dir()
    setup = _fetch(f"Inno Setup {INNO_VERSION} (14 MB)", INNO_URL, INNO_SHA256,
                   tools / f"innosetup-{INNO_VERSION}-x64.exe")
    folder = tools / f"innosetup-{INNO_VERSION}"
    _run([str(setup), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/CURRENTUSER", "/PORTABLE=1",
          f"/DIR={folder}"])
    setup.unlink()
    iscc = folder / "ISCC.exe"
    if not iscc.is_file():
        raise BuildError(f"Inno Setup's setup finished without making {iscc}")
    return iscc


def inno_script(name: str, info: AppInfo, folder: Path, out: Path, icon: Path | None) -> str:
    """The Inno Setup script: a per-user install (no admin rights needed,
    though an admin may choose everyone) into Programs, a Start-menu entry,
    an optional desktop one, and an uninstaller. Its AppId comes from the
    identifier, so a new version replaces the old."""
    app_id = uuid.uuid5(uuid.NAMESPACE_DNS, info.identifier)
    lines = [
        "[Setup]",
        f"AppId={{{{{app_id}}}",
        f"AppName={name}",
        f"AppVersion={info.version}",
        f"AppVerName={name} {info.version}",
        f"AppPublisher={info.publisher}" if info.publisher else None,
        f"DefaultDirName={{autopf}}\\{name}",
        f"DefaultGroupName={name}",
        "DisableProgramGroupPage=yes",
        "PrivilegesRequired=lowest",
        "PrivilegesRequiredOverridesAllowed=dialog",
        f"OutputDir={out}",
        f"OutputBaseFilename={name}-{info.version}-setup",
        "Compression=lzma2",
        "SolidCompression=yes",
        "WizardStyle=modern",
        "ArchitecturesAllowed=x64compatible",
        "ArchitecturesInstallIn64BitMode=x64compatible",
        f"UninstallDisplayIcon={{app}}\\{name}.exe",
        f"VersionInfoVersion={info.version}",
        f"VersionInfoDescription={info.description or name}",
        f"SetupIconFile={icon}" if icon is not None and icon.suffix.lower() == ".ico" else None,
        "",
        "[Tasks]",
        'Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; '
        'GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked',
        "",
        "[Files]",
        f'Source: "{folder}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs',
        "",
        "[Icons]",
        f'Name: "{{autoprograms}}\\{name}"; Filename: "{{app}}\\{name}.exe"',
        f'Name: "{{autodesktop}}\\{name}"; Filename: "{{app}}\\{name}.exe"; Tasks: desktopicon',
        "",
        "[Run]",
        f'Filename: "{{app}}\\{name}.exe"; Description: "{{cm:LaunchProgram,{name}}}"; '
        "Flags: nowait postinstall skipifsilent",
    ]
    return "\n".join(line for line in lines if line is not None) + "\n"


def _windows(built: Path, name: str, info: AppInfo, dist: Path, icon: Path | None = None) -> Built:
    """The app's folder in `dist/<name>`, and `<name>-<version>-setup.exe`
    made from it with Inno Setup (found, or fetched once)."""
    if any(c in name for c in '\\/:*?"<>|{}'):
        raise BuildError(f"{name!r} can't be a Windows program name: leave out \\ / : * ? \" < > | {{ }}")
    folder = built / name
    if not (folder / f"{name}.exe").is_file():
        raise BuildError(f"PyInstaller finished without making {folder / (name + '.exe')}")
    iscc = find_iscc() or fetch_iscc()
    dist.mkdir(parents=True, exist_ok=True)
    final = dist / name
    if final.exists():
        shutil.rmtree(final)
    shutil.copytree(folder, final)
    script = built / f"{name}.iss"
    script.write_text(inno_script(name, info, final, dist, icon), encoding="utf-8-sig")  # Inno reads UTF-8 by its BOM
    _run([str(iscc), "/Q", str(script)])
    setup = dist / f"{name}-{info.version}-setup.exe"
    if not setup.is_file():
        raise BuildError(f"Inno Setup finished without making {setup}")
    return Built(final / f"{name}.exe", [setup])


# -- Linux: AppImage, .deb, pacman (M78) -------------------------------------------

#: `appimagetool` and the AppImage runtime it puts at the front of an
#: AppImage, pinned and checked against GitHub's digests; passing the
#: runtime keeps `appimagetool` from downloading one on every build.
APPIMAGETOOL_URL = "https://github.com/AppImage/appimagetool/releases/download/1.9.1/appimagetool-x86_64.AppImage"
APPIMAGETOOL_SHA256 = "ed4ce84f0d9caff66f50bcca6ff6f35aae54ce8135408b3fa33abfc3cb384eb0"
RUNTIME_URL = "https://github.com/AppImage/type2-runtime/releases/download/20251108/runtime-x86_64"
RUNTIME_SHA256 = "2fca8b443c92510f1483a883f60061ad09b46b978b2631c807cd873a47ec260d"

#: What the app needs from a Linux system that PyInstaller doesn't bundle:
#: the Vulkan loader (and a driver) and the X11 keyboard library winit loads.
DEB_DEPENDS = "libvulkan1, libxkbcommon-x11-0"
DEB_RECOMMENDS = "mesa-vulkan-drivers"
PACMAN_DEPENDS = ("vulkan-icd-loader", "libxkbcommon-x11")
PACMAN_OPTDEPENDS = ("vulkan-driver: a Vulkan driver for the GPU",)


def linux_icon(icon: Path | None, out: Path) -> Path:
    """A 256 px PNG for the desktop entry: the app's icon fitted to a
    square, or, with none, a plain one (AppImage needs an icon)."""
    from PIL import Image

    square = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    if icon is not None and icon.suffix.lower() == ".png":
        image = Image.open(icon).convert("RGBA")
        image.thumbnail((256, 256))
        square.paste(image, ((256 - image.width) // 2, (256 - image.height) // 2))
    else:
        square.paste((103, 80, 164, 255), (32, 32, 224, 224))
    square.save(out)
    return out


def desktop_entry(name: str, info: AppInfo, exec_path: str) -> str:
    """The freedesktop.org entry that puts the app in the menu."""
    quoted = exec_path if " " not in exec_path else f'"{exec_path}"'
    lines = ["[Desktop Entry]", "Type=Application", f"Name={name}", f"Exec={quoted}", f"Icon={info.identifier}",
             "Terminal=false", "Categories=Utility;"]
    if info.description:
        lines.insert(3, f"Comment={info.description}")
    return "\n".join(lines) + "\n"


def _tree(folder: Path) -> list[tuple[str, Path]]:
    """`folder`'s files and folders as (relative POSIX path, path), sorted."""
    return sorted((p.relative_to(folder).as_posix(), p) for p in folder.rglob("*"))


def _add(tar: tarfile.TarFile, arcname: str, path: Path | None = None, *, data: bytes | None = None,
         mode: int = 0o644, link: str | None = None, folder: bool = False) -> None:
    """One entry, owned by root, as a system package's files are."""
    info = tarfile.TarInfo(arcname)
    info.uname = info.gname = "root"  # uid and gid are 0 already
    info.mtime = int(time.time())
    if link is not None:
        info.type, info.linkname, info.mode = tarfile.SYMTYPE, link, 0o777
        tar.addfile(info)
    elif folder or (path is not None and path.is_dir() and not path.is_symlink()):
        info.type, info.mode = tarfile.DIRTYPE, 0o755
        tar.addfile(info)
    elif path is not None and path.is_symlink():
        info.type, info.linkname, info.mode = tarfile.SYMTYPE, os.readlink(path), 0o777
        tar.addfile(info)
    else:
        content = data if data is not None else path.read_bytes()
        info.size = len(content)
        executable = path is not None and path.stat().st_mode & stat.S_IXUSR
        info.mode = 0o755 if executable else mode
        tar.addfile(info, io.BytesIO(content))


def _system_files(tar: tarfile.TarFile, app: Path, name: str, info: AppInfo, icon: Path, prefix: str = "") -> int:
    """The installed layout, under `prefix`: the app in `/opt/<slug>`, a
    `/usr/bin/<slug>` link, the desktop entry and the icon. Returns the
    bytes installed."""
    pkg = slug(name)
    size = 0
    parents = ["opt", "usr", "usr/bin", "usr/share", "usr/share/applications", "usr/share/icons",
               "usr/share/icons/hicolor", "usr/share/icons/hicolor/256x256", "usr/share/icons/hicolor/256x256/apps"]
    for folder in parents:
        _add(tar, prefix + folder, folder=True)
    _add(tar, f"{prefix}opt/{pkg}", folder=True)
    for rel, path in _tree(app):
        _add(tar, f"{prefix}opt/{pkg}/{rel}", path)
        size += path.stat().st_size if path.is_file() and not path.is_symlink() else 0
    _add(tar, f"{prefix}usr/bin/{pkg}", link=f"/opt/{pkg}/{name}")
    entry = desktop_entry(name, info, f"/opt/{pkg}/{name}").encode()
    _add(tar, f"{prefix}usr/share/applications/{info.identifier}.desktop", data=entry)
    _add(tar, f"{prefix}usr/share/icons/hicolor/256x256/apps/{info.identifier}.png", data=icon.read_bytes())
    return size + len(entry) + icon.stat().st_size


def _ar(members: list[tuple[str, bytes]]) -> bytes:
    """A common-format `ar` archive, as a `.deb` is."""
    out = [b"!<arch>\n"]
    for member, content in members:
        out.append(f"{member:<16}{int(time.time()):<12}{0:<6}{0:<6}{'100644':<8}{len(content):<10}`\n".encode())
        out.append(content + (b"\n" if len(content) % 2 else b""))
    return b"".join(out)


def make_deb(app: Path, name: str, info: AppInfo, icon: Path, out: Path) -> Path:
    """A `.deb` (Debian, Ubuntu and their kin): control and data tars in
    an `ar` archive, written here rather than with `dpkg-deb`."""
    pkg = slug(name)
    data = io.BytesIO()
    with tarfile.open(fileobj=data, mode="w:gz", format=tarfile.GNU_FORMAT) as tar:
        size = _system_files(tar, app, name, info, icon, prefix="./")
    control_text = "\n".join([
        f"Package: {pkg}", f"Version: {info.version}", "Architecture: amd64",
        f"Maintainer: {info.publisher or name}", f"Installed-Size: {(size + 1023) // 1024}",
        f"Depends: {DEB_DEPENDS}", f"Recommends: {DEB_RECOMMENDS}", "Section: utils", "Priority: optional",
        f"Description: {info.description or name}", ""]).encode()
    control = io.BytesIO()
    with tarfile.open(fileobj=control, mode="w:gz", format=tarfile.GNU_FORMAT) as tar:
        _add(tar, ".", folder=True)
        _add(tar, "./control", data=control_text)
    deb = out / f"{pkg}_{info.version}_amd64.deb"
    deb.write_bytes(_ar([("debian-binary", b"2.0\n"), ("control.tar.gz", control.getvalue()),
                         ("data.tar.gz", data.getvalue())]))
    return deb


def make_pacman(app: Path, name: str, info: AppInfo, icon: Path, out: Path) -> Path:
    """An Arch Linux package: `.PKGINFO` and the files in one tar, xz
    compressed (pacman reads it as it reads zstd, and Python has no zstd
    before 3.14)."""
    pkg = slug(name)
    body = io.BytesIO()
    with tarfile.open(fileobj=body, mode="w", format=tarfile.GNU_FORMAT) as files:
        size = _system_files(files, app, name, info, icon)
    pkginfo = "\n".join([
        f"pkgname = {pkg}", f"pkgbase = {pkg}", f"pkgver = {info.version}-1",
        f"pkgdesc = {info.description or name}", f"builddate = {int(time.time())}",
        f"packager = {info.publisher or 'Unknown Packager'}", f"size = {size}", "arch = x86_64",
        "license = custom", *(f"depend = {d}" for d in PACMAN_DEPENDS),
        *(f"optdepend = {d}" for d in PACMAN_OPTDEPENDS), ""]).encode()
    package = out / f"{pkg}-{info.version}-1-x86_64.pkg.tar.xz"
    with tarfile.open(package, mode="w:xz", format=tarfile.GNU_FORMAT) as tar:
        _add(tar, ".PKGINFO", data=pkginfo)
        body.seek(0)
        with tarfile.open(fileobj=body) as files:
            for member in files.getmembers():
                tar.addfile(member, files.extractfile(member) if member.isfile() else None)
    return package


def make_appimage(app: Path, name: str, info: AppInfo, icon: Path, work: Path, out: Path) -> Path:
    """An AppImage (runs on most distributions, with no install step):
    an AppDir with the app, an `AppRun`, the desktop entry and icon,
    packed by the pinned `appimagetool` with the pinned runtime."""
    tools = tools_dir()
    tool = _fetch("appimagetool 1.9.1 (15 MB)", APPIMAGETOOL_URL, APPIMAGETOOL_SHA256,
                  tools / "appimagetool-1.9.1-x86_64.AppImage")
    tool.chmod(0o755)
    runtime = _fetch("the AppImage runtime (1 MB)", RUNTIME_URL, RUNTIME_SHA256, tools / "runtime-20251108-x86_64")
    appdir = work / f"{slug(name)}.AppDir"
    shutil.copytree(app, appdir / "usr" / "lib" / slug(name), symlinks=True)
    run = appdir / "AppRun"
    run.write_text(f'#!/bin/sh\nHERE="$(dirname "$(readlink -f "$0")")"\n'
                   f'exec "$HERE/usr/lib/{slug(name)}/{name}" "$@"\n', encoding="utf-8")
    run.chmod(0o755)
    (appdir / f"{info.identifier}.desktop").write_text(desktop_entry(name, info, "AppRun"), encoding="utf-8")
    shutil.copy(icon, appdir / f"{info.identifier}.png")
    shutil.copy(icon, appdir / ".DirIcon")
    image = out / f"{name}-{info.version}-x86_64.AppImage"
    env = {**os.environ, "ARCH": "x86_64", "APPIMAGE_EXTRACT_AND_RUN": "1"}  # no FUSE needed, as in CI
    result = subprocess.run([str(tool), "--no-appstream", "--runtime-file", str(runtime), str(appdir), str(image)],
                            capture_output=True, text=True, env=env)
    if result.returncode != 0 or not image.is_file():
        raise BuildError(f"appimagetool failed ({result.returncode}): {(result.stderr or result.stdout).strip()}")
    return image


def _linux(built: Path, name: str, info: AppInfo, dist: Path, icon: Path | None = None) -> Built:
    """The app's folder in `dist/<name>`, and from it an AppImage, a
    `.deb` and a pacman package."""
    if "/" in name or name.startswith("."):
        raise BuildError(f"{name!r} can't be a Linux program name: no / and no leading .")
    folder = built / name
    if not (folder / name).is_file():
        raise BuildError(f"PyInstaller finished without making {folder / name}")
    dist.mkdir(parents=True, exist_ok=True)
    final = dist / name
    if final.exists():
        shutil.rmtree(final)
    shutil.copytree(folder, final, symlinks=True)
    png = linux_icon(icon, built / "icon.png")
    made = [make_appimage(final, name, info, png, built, dist), make_deb(final, name, info, png, dist),
            make_pacman(final, name, info, png, dist)]
    return Built(final / name, made)


#: Each platform's installer, from PyInstaller's one-folder build.
_INSTALLERS = {"darwin": _macos, "win32": _windows, "linux": _linux}


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
