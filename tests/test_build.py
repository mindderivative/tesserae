"""M77: `tesserae build`, an app as one executable. What the scan bundles,
PyInstaller's command line, how `App.run` behaves in a built app
(`TESSERAE_MAX_FRAMES`, no hot reload), the command's mistakes, and one
real build of a generated shell app run from somewhere else.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

import tesserae.app
from tesserae import App, View, build, cli


def _app_folder(root: Path) -> Path:
    files = {
        "app.py": "", "Home_View.yaml": "", "Home_ViewModel.py": "", "Home_Style.yaml": "",
        "panels/Nav_ViewModel.py": "", "panels/Nav_View.yaml": "", "images/logo.png": "",
        ".git/config": "", ".env": "", ".config/keep.yaml": "", "__pycache__/x.pyc": "", "stray.pyc": "",
        "build/junk": "", "dist/old": "", "app.spec": "", "venv/pyvenv.cfg": "", "venv/lib/x.py": "",
        "myenv/pyvenv.cfg": "", "myenv/lib/y.py": "", "notes/draft.md": "", "notes/keep.txt": "",
    }
    for rel, text in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text)
    return root / "app.py"


def _bundled(collected):
    return sorted(Path(folder, source.name).as_posix() for source, folder in collected.files)


def test_the_scan_takes_the_app_and_skips_tooling(tmp_path):
    collected = build.collect_files(_app_folder(tmp_path))
    assert _bundled(collected) == [
        "Home_Style.yaml", "Home_View.yaml", "Home_ViewModel.py", "app.py", "images/logo.png",
        "notes/draft.md", "notes/keep.txt", "panels/Nav_View.yaml", "panels/Nav_ViewModel.py"]
    # every .py but the entry point is analysed, from its own folder
    assert collected.modules == ["Home_ViewModel", "Nav_ViewModel"]
    assert collected.paths == [tmp_path, tmp_path / "panels"]


def test_include_and_exclude_globs(tmp_path):
    collected = build.collect_files(_app_folder(tmp_path), include=[".config", ".env"], exclude=["notes/*.md"])
    bundled = _bundled(collected)
    assert ".config/keep.yaml" in bundled and ".env" in bundled
    assert "notes/draft.md" not in bundled and "notes/keep.txt" in bundled
    whole = build.collect_files(tmp_path / "app.py", exclude=["panels"])
    assert not any(b.startswith("panels/") for b in _bundled(whole)) and whole.modules == ["Home_ViewModel"]


def test_pyinstaller_args(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")  # one file on macOS has no --windowed (M78; tested below)
    app_file = _app_folder(tmp_path)
    collected = build.collect_files(app_file)
    args = build.pyinstaller_args(app_file, "demo", collected, tmp_path / "work", tmp_path / "dist")
    assert args[0] == str(app_file) and "--onefile" in args and "--windowed" in args and "--onedir" not in args
    pairs = list(zip(args, args[1:]))
    assert ("--name", "demo") in pairs and ("--distpath", str(tmp_path / "dist")) in pairs
    assert ("--collect-data", "tesserae") in pairs and ("--collect-submodules", "tesserae") in pairs
    assert ("--hidden-import", "Nav_ViewModel") in pairs and ("--paths", str(tmp_path / "panels")) in pairs
    assert ("--add-data", f"{tmp_path / 'panels' / 'Nav_View.yaml'}{os.pathsep}panels") in pairs
    assert ("--add-data", f"{tmp_path / 'Home_View.yaml'}{os.pathsep}.") in pairs
    console = build.pyinstaller_args(app_file, "demo", collected, tmp_path, tmp_path,
                                     console=True, icon=tmp_path / "i.ico")
    assert "--windowed" not in console and ("--icon", str(tmp_path / "i.ico")) in list(zip(console, console[1:]))


def test_executable_path_per_platform(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    assert build.executable_path(tmp_path, "demo") == tmp_path / "demo.exe"
    monkeypatch.setattr(sys, "platform", "darwin")
    assert build.executable_path(tmp_path, "demo") == tmp_path / "demo"


# -- App.run in a built app ----------------------------------------------------

class _FakeTre:
    def __init__(self):
        self.max_frames = "unset"

    def add_window(self, window):
        pass

    def thread_handle(self):
        return self

    def call_soon(self, fn):
        pass

    def run(self, max_frames=None):
        self.max_frames = max_frames


@pytest.fixture
def run_app(monkeypatch):
    """Runs a one-screen app on a fake `tre` loop; returns the loop and
    whether watchers started."""
    def run(**kwargs):
        fake, started = _FakeTre(), []
        monkeypatch.setattr(tesserae.app, "_TreApp", lambda: fake)
        app = App()
        monkeypatch.setattr(app, "_start_watchers", lambda handle: started.append(True))
        app.register("Home", View({"id": "root", "kind": "Container", "style": {"width": 10, "height": 10}},
                                  window=app.window), None)
        app.show("Home")
        app.run(**kwargs)
        return fake, bool(started)
    return run


def test_tesserae_max_frames_bounds_a_run(run_app, monkeypatch):
    monkeypatch.delenv("TESSERAE_MAX_FRAMES", raising=False)
    assert run_app()[0].max_frames is None
    monkeypatch.setenv("TESSERAE_MAX_FRAMES", "20")
    assert run_app()[0].max_frames == 20
    assert run_app(max_frames=5)[0].max_frames == 5  # the app's own bound wins
    monkeypatch.setenv("TESSERAE_MAX_FRAMES", "lots")
    with pytest.raises(ValueError, match="TESSERAE_MAX_FRAMES must be a whole number.*'lots'"):
        run_app()


def test_a_built_app_does_not_hot_reload(run_app, monkeypatch, logs):
    assert run_app(hot_reload=True)[1] is True
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    assert run_app(hot_reload=True)[1] is False
    assert any("hot reload is off in a built app" in m for m in logs.messages("INFO"))


# -- the command ---------------------------------------------------------------

def test_build_mistakes_are_one_line(tmp_path, capsys, monkeypatch):
    assert cli.main(["build", str(tmp_path / "nope.py")]) == 2
    assert "isn't a file: give the app's entry point" in capsys.readouterr().err
    app_file = _app_folder(tmp_path)
    assert cli.main(["build", str(app_file), "--icon", str(tmp_path / "none.ico")]) == 2
    assert "none.ico isn't a file" in capsys.readouterr().err
    monkeypatch.setitem(sys.modules, "PyInstaller", None)
    monkeypatch.setitem(sys.modules, "PyInstaller.__main__", None)
    assert cli.main(["build", str(app_file)]) == 2
    assert "pip install tesserae-ui[build]" in capsys.readouterr().err


def test_a_generated_shell_app_builds_and_runs_from_elsewhere(tmp_path, capsys, monkeypatch):
    """The real thing: `tesserae new --shell`, `tesserae build --check`.
    The shell's panels import their ViewModels by path, so this fails if
    the app's files aren't in the executable."""
    pytest.importorskip("PyInstaller")
    folder = cli.new("demo", tmp_path, shell=True)
    monkeypatch.chdir(folder)
    assert cli.main(["build", "--name", "Demo App"]) == 0, capsys.readouterr().err
    executable = build.executable_path(folder / "dist", "Demo App")
    assert f"built {executable}" in capsys.readouterr().out
    result = build.check(executable)
    assert result.returncode == 0, result.stderr
    if result.frames == 0:
        pytest.skip("no display reachable -- the executable drew no frames (CI's build-executable job has one)")
    assert result.frames == build.CHECK_FRAMES


@pytest.mark.skipif(sys.platform == "win32", reason="runs a script as the executable, by its #! line")
def test_check_runs_the_executable_elsewhere_with_a_frame_bound(tmp_path, monkeypatch):
    fake = tmp_path / "fake"
    fake.write_text(f"#!{sys.executable}\nimport os, sys\n"
                    "open(os.environ['TESSERAE_FRAMES_REPORT'], 'w').write(os.environ['TESSERAE_MAX_FRAMES'])\n"
                    "print(os.getcwd(), file=sys.stderr); sys.exit(3)\n")
    fake.chmod(0o755)
    monkeypatch.chdir(tmp_path)
    result = build.check(fake, frames=7)
    assert result.returncode == 3 and result.frames == 7
    cwd = result.stderr.strip()
    assert Path(cwd).resolve() != tmp_path.resolve() and "tesserae-check-" in cwd
    fake.write_text(f"#!{sys.executable}\n")  # returned without drawing, as with no display
    assert build.check(fake).frames == 0


def test_check_fails_an_app_that_drew_nothing(tmp_path, capsys, monkeypatch):
    (tmp_path / "app.py").write_text("")
    monkeypatch.setattr(build, "build", lambda *a, **k: build.Built(tmp_path / "app", []))
    monkeypatch.setattr(build, "check", lambda exe: build.Checked(0, 0, "no display"))
    assert cli.main(["build", "--check", str(tmp_path / "app.py")]) == 1
    assert "drew no frames: is there a display" in capsys.readouterr().err
    monkeypatch.setattr(build, "check", lambda exe: build.Checked(1, 0, "Traceback"))
    assert cli.main(["build", "--check", str(tmp_path / "app.py")]) == 1
    assert "exited with 1:\nTraceback" in capsys.readouterr().err


def test_a_run_reports_the_frames_it_drew(tmp_path, monkeypatch):
    """The real loop, in a fresh process: 12 frames asked for, 12 counted
    (or 0 where there's no display)."""
    report = tmp_path / "frames.txt"
    script = tmp_path / "run.py"
    script.write_text(
        "from tesserae import App, View\n"
        "app = App(width=60, height=40)\n"
        "app.register('Home', View({'id': 'root', 'kind': 'Container', 'style': {'width': 10, 'height': 10}},"
        " window=app.window), None)\n"
        "app.show('Home')\n"
        "seen = [0]\nhandle = app.thread_handle()\n"
        "def tick():\n    seen[0] += 1\n    handle.call_soon(tick)\n"
        "handle.call_soon(tick)\napp.run()\nprint(seen[0])\n")
    env = {**os.environ, "TESSERAE_MAX_FRAMES": "12", "TESSERAE_FRAMES_REPORT": str(report)}
    result = subprocess.run([sys.executable, str(script)], env=env, capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr
    seen = int(result.stdout)  # the script's own count, to tell no display from no report
    if seen == 0:
        pytest.skip("no display reachable -- App.run() drew no frames")
    assert int(report.read_text()) == seen == 12


# -- M78: installers -------------------------------------------------------------

def test_a_folder_build_and_the_windowed_rule(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    app_file = _app_folder(tmp_path)
    collected = build.collect_files(app_file)
    folder = build.pyinstaller_args(app_file, "demo", collected, tmp_path, tmp_path, onefile=False)
    assert "--onedir" in folder and "--onefile" not in folder and "--windowed" in folder
    monkeypatch.setattr(sys, "platform", "darwin")  # one file there runs from a terminal: PyInstaller 7 refuses a .app
    assert "--windowed" not in build.pyinstaller_args(app_file, "demo", collected, tmp_path, tmp_path)
    assert "--windowed" in build.pyinstaller_args(app_file, "demo", collected, tmp_path, tmp_path, onefile=False)


def test_app_info_checks_and_defaults():
    info = build.AppInfo("Demo App")
    assert (info.version, info.identifier, info.placeholder_identifier) == ("0.1.0", "com.example.demo-app", True)
    assert build.AppInfo("x", "2.10.3", "com.acme.x").placeholder_identifier is False
    with pytest.raises(build.BuildError, match="version '1.0-beta' isn't one installers take"):
        build.AppInfo("x", "1.0-beta")
    with pytest.raises(build.BuildError, match="identifier 'notes' isn't reverse-DNS"):
        build.AppInfo("x", identifier="notes")
    assert build.slug("  Demo  App! 2 ") == "demo-app-2" and build.slug("!!") == "app"


@pytest.mark.parametrize("platform, suffix", [("win32", ".ico"), ("darwin", ".icns"), ("linux", ".png")])
def test_a_png_icon_becomes_the_platforms_own(tmp_path, monkeypatch, platform, suffix):
    from PIL import Image

    png = tmp_path / "logo.png"
    Image.new("RGBA", (300, 200), (103, 80, 164, 255)).save(png)
    monkeypatch.setattr(sys, "platform", platform)
    out = build.platform_icon(png, tmp_path)
    assert out.suffix == suffix and Image.open(out).format == {".ico": "ICO", ".icns": "ICNS", ".png": "PNG"}[suffix]
    ico = tmp_path / "given.ico"
    ico.write_bytes(b"")
    assert build.platform_icon(ico, tmp_path) == ico and build.platform_icon(None, tmp_path) is None


def test_the_macos_installer_stamps_signs_and_makes_a_dmg(tmp_path, monkeypatch):
    """`hdiutil` and `codesign` are macOS's; here they're recorded, and
    CI's macOS job runs them for real."""
    import plistlib

    built = tmp_path / "built"
    contents = built / "Demo App.app" / "Contents"
    (contents / "MacOS").mkdir(parents=True)
    (contents / "MacOS" / "Demo App").write_text("")
    (contents / "Info.plist").write_bytes(plistlib.dumps({"CFBundleIdentifier": "old", "NSHighResolutionCapable": True}))
    ran = []
    monkeypatch.setattr(build, "_run", ran.append)
    info = build.AppInfo("Demo App", "1.2.0", "com.acme.demo", "Acme Ltd")
    result = build._macos(built, "Demo App", info, tmp_path / "dist", None)
    app = tmp_path / "dist" / "Demo App.app"
    assert result == build.Built(app / "Contents" / "MacOS" / "Demo App", [tmp_path / "dist" / "Demo App-1.2.0.dmg"])
    plist = plistlib.loads((app / "Contents" / "Info.plist").read_bytes())
    assert plist == {"CFBundleIdentifier": "com.acme.demo", "NSHighResolutionCapable": True,
                     "CFBundleShortVersionString": "1.2.0", "CFBundleVersion": "1.2.0",
                     "CFBundleDisplayName": "Demo App", "NSHumanReadableCopyright": "Acme Ltd"}
    assert ran[0] == ["codesign", "--force", "--deep", "--sign", "-", str(built / "Demo App.app")]
    assert ran[1] == ["hdiutil", "create", "-volname", "Demo App", "-srcfolder", str(built / "dmg"), "-ov",
                      "-format", "UDZO", str(tmp_path / "dist" / "Demo App-1.2.0.dmg")]
    assert os.readlink(built / "dmg" / "Applications") == "/Applications"  # drag it there
    assert (built / "dmg" / "Demo App.app" / "Contents" / "Info.plist").is_file()


def test_a_failing_tool_says_why(tmp_path):
    with pytest.raises(build.BuildError, match=r"python.* failed \(3\): nope"):
        build._run([sys.executable, "-c", "import sys; sys.stderr.write('nope'); sys.exit(3)"])


def test_installer_where_there_is_none_yet(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(sys, "platform", "sunos5")
    assert cli.main(["build", "--installer", str(_app_folder(tmp_path))]) == 2
    assert "--installer isn't ready on sunos5 yet" in capsys.readouterr().err


def test_cli_passes_the_installer_details_and_notes_a_placeholder(tmp_path, capsys, monkeypatch):
    seen = {}

    def fake_build(app, **kwargs):
        seen.update(kwargs)
        return build.Built(tmp_path / "app", [tmp_path / "App-1.0.dmg"])

    monkeypatch.setattr(build, "build", fake_build)
    app_file = _app_folder(tmp_path)
    assert cli.main(["build", str(app_file), "--installer", "--app-version", "1.0", "--publisher", "Acme"]) == 0
    out = capsys.readouterr().out
    assert seen["installer"] is True and seen["info"] == build.AppInfo(tmp_path.name, "1.0", None, "Acme")
    assert f"made {tmp_path / 'App-1.0.dmg'}" in out and "the identifier is a placeholder" in out
    assert cli.main(["build", str(app_file), "--installer", "--identifier", "com.acme.x"]) == 0
    assert "placeholder" not in capsys.readouterr().out
    assert cli.main(["build", str(app_file), "--app-version", "one"]) == 2
    assert "version 'one' isn't one installers take" in capsys.readouterr().err


# -- M78: Windows, with Inno Setup -------------------------------------------------

def test_the_inno_script():
    info = build.AppInfo("Demo App", "1.2.0", "com.acme.demo", "Acme Ltd", "Takes notes")
    folder, out, icon = Path("D:/a/dist/Demo App"), Path("D:/a/dist"), Path("D:/t/i.ico")  # as the OS writes them
    script = build.inno_script("Demo App", info, folder, out, icon)
    lines = script.splitlines()
    app_id = lines[1]
    assert app_id == "AppId={{" + str(build.uuid.uuid5(build.uuid.NAMESPACE_DNS, "com.acme.demo")) + "}"
    for line in ["AppName=Demo App", "AppVersion=1.2.0", "AppPublisher=Acme Ltd", "PrivilegesRequired=lowest",
                 "DefaultDirName={autopf}\\Demo App", f"OutputDir={out}", "OutputBaseFilename=Demo App-1.2.0-setup",
                 "VersionInfoVersion=1.2.0", "VersionInfoDescription=Takes notes", f"SetupIconFile={icon}",
                 f'Source: "{folder}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs',
                 'Name: "{autoprograms}\\Demo App"; Filename: "{app}\\Demo App.exe"']:
        assert line in lines, line
    bare = build.inno_script("x", build.AppInfo("x", identifier="com.acme.x"), Path("f"), Path("o"), Path("i.png"))
    assert "AppPublisher" not in bare and "SetupIconFile" not in bare and "VersionInfoDescription=x" in bare
    assert "\n\n\n" not in bare and app_id not in bare  # another identifier, another AppId


def test_finding_inno_setup(tmp_path, monkeypatch):
    for var in ("TESSERAE_ISCC", "ProgramFiles(x86)", "ProgramFiles", "LOCALAPPDATA"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setattr(build.shutil, "which", lambda name: None)
    assert build.find_iscc() is None
    cached = tmp_path / "cache" / "tesserae" / "tools" / f"innosetup-{build.INNO_VERSION}" / "ISCC.exe"
    cached.parent.mkdir(parents=True)
    cached.write_text("")
    assert build.find_iscc() == cached
    per_user = tmp_path / "local" / "Programs" / "Inno Setup 6" / "ISCC.exe"
    per_user.parent.mkdir(parents=True)
    per_user.write_text("")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    assert build.find_iscc() == per_user
    everyone = tmp_path / "pf86" / "Inno Setup 7" / "ISCC.exe"
    everyone.parent.mkdir(parents=True)
    everyone.write_text("")
    monkeypatch.setenv("ProgramFiles(x86)", str(tmp_path / "pf86"))
    assert build.find_iscc() == everyone
    monkeypatch.setattr(build.shutil, "which", lambda name: "/bin/iscc" if name == "iscc" else None)
    assert build.find_iscc() == Path("/bin/iscc")
    monkeypatch.setenv("TESSERAE_ISCC", "/x/ISCC.exe")
    assert build.find_iscc() == Path("/x/ISCC.exe")


def test_fetching_inno_setup_checks_its_digest(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    tools = tmp_path / "tesserae" / "tools"
    monkeypatch.setattr(build, "_download", lambda url, to: to.write_bytes(b"not inno"))
    ran = []
    monkeypatch.setattr(build, "_run", ran.append)
    with pytest.raises(build.BuildError, match="SHA-256 is .*: not using it"):
        build.fetch_iscc()
    assert ran == [] and not any(tools.iterdir())  # a bad download isn't run, or kept
    monkeypatch.setattr(build, "INNO_SHA256", build.hashlib.sha256(b"not inno").hexdigest())

    def portable(command):
        ran.append(command)
        (tools / f"innosetup-{build.INNO_VERSION}").mkdir()
        (tools / f"innosetup-{build.INNO_VERSION}" / "ISCC.exe").write_text("")

    monkeypatch.setattr(build, "_run", portable)
    assert build.fetch_iscc() == tools / f"innosetup-{build.INNO_VERSION}" / "ISCC.exe"
    setup = tools / f"innosetup-{build.INNO_VERSION}-x64.exe"
    assert ran == [[str(setup), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/CURRENTUSER", "/PORTABLE=1",
                    f"/DIR={tools / ('innosetup-' + build.INNO_VERSION)}"]]
    assert not setup.exists() and "fetching Inno Setup" in capsys.readouterr().out
    assert build.INNO_URL.endswith(f"innosetup-{build.INNO_VERSION}-x64.exe")


def test_the_windows_installer(tmp_path, monkeypatch):
    built = tmp_path / "built"
    (built / "Demo" / "_internal").mkdir(parents=True)
    (built / "Demo" / "Demo.exe").write_text("")
    (built / "Demo" / "_internal" / "lib.dll").write_text("")
    dist = tmp_path / "dist"
    ran = []

    def iscc(command):
        ran.append(command)
        (dist / "Demo-1.2.0-setup.exe").write_text("")

    monkeypatch.setattr(build, "_run", iscc)
    monkeypatch.setattr(build, "find_iscc", lambda: Path("C:/Inno/ISCC.exe"))
    result = build._windows(built, "Demo", build.AppInfo("Demo", "1.2.0", "com.acme.demo"), dist)
    assert result == build.Built(dist / "Demo" / "Demo.exe", [dist / "Demo-1.2.0-setup.exe"])
    assert (dist / "Demo" / "_internal" / "lib.dll").is_file()
    assert ran == [[str(Path("C:/Inno/ISCC.exe")), "/Q", str(built / "Demo.iss")]]
    raw = (built / "Demo.iss").read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf") and f"Source: \"{dist / 'Demo'}\\*\"".encode() in raw
    with pytest.raises(build.BuildError, match="can't be a Windows program name"):
        build._windows(built, "a:b", build.AppInfo("a:b"), dist)
    monkeypatch.setattr(build, "find_iscc", lambda: None)
    monkeypatch.setattr(build, "fetch_iscc", lambda: Path("C:/fetched/ISCC.exe"))
    build._windows(built, "Demo", build.AppInfo("Demo", "1.2.0"), dist)  # over a previous build
    assert ran[-1][0] == str(Path("C:/fetched/ISCC.exe"))


def test_app_details_on_one_line():
    with pytest.raises(build.BuildError, match="publisher can't span lines"):
        build.AppInfo("x", publisher="Acme\nEvil=1")


@pytest.mark.parametrize("platform", ["darwin", "win32"])
def test_installer_is_ready_on_macos_and_windows(tmp_path, capsys, monkeypatch, platform):
    def stop():
        raise build.BuildError("got as far as building")

    monkeypatch.setattr(sys, "platform", platform)
    monkeypatch.setattr(build, "_pyinstaller", stop)
    assert cli.main(["build", "--installer", str(_app_folder(tmp_path))]) == 2
    assert "got as far as building" in capsys.readouterr().err
