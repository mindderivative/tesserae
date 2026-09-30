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


def test_pyinstaller_args(tmp_path):
    app_file = _app_folder(tmp_path)
    collected = build.collect_files(app_file)
    args = build.pyinstaller_args(app_file, "demo", collected, tmp_path / "work", tmp_path / "dist")
    assert args[0] == str(app_file) and "--onefile" in args and "--windowed" in args
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
    monkeypatch.setattr(build, "build", lambda *a, **k: tmp_path / "app")
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
