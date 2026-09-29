"""M67 (#14): `tesserae new` and `tesserae add screen`. Each test makes an
app in `tmp_path` and runs it for real, in a subprocess: a small wrapper
swaps `App.run` for a check that clicks Home's button, follows a route
and renders a few frames, as the examples run on CI.
"""

import json
import subprocess
import sys
import textwrap

import pytest

from tesserae import cli

RUNNER = textwrap.dedent('''
    import json, runpy, sys
    from pathlib import Path
    import tesserae

    project = Path(sys.argv[1])
    sys.path.insert(0, str(project))
    sys.argv = ["app.py", *sys.argv[2:]]
    real_run = tesserae.App.run
    report = {}

    def run(app, max_frames=None, **kwargs):
        report["start"] = app.current
        report["location"] = app.location
        home = app._registered["Home"].view
        report["greeting"] = home.node("greeting").get("text")
        report["button"] = [home.node("button").get(k) for k in ("role", "label")]
        if app.current == "Home":
            app.window.simulate("click", node=home.node("button"))
            report["count"] = home.node("count").get("text")
        report["screens"] = sorted(app._registered)
        report["routes"] = [r.pattern for r in app._routes]
        report["shell"] = app._shell is not None
        report["rail"] = app._navigation[1] if app._navigation is not None else None
        report["size"] = [app.window.get("width"), app.window.get("height")]
        for name in report["screens"]:
            if name == "Home":
                continue
            app.navigate(name)
            app.window.simulate("click", node=app._registered[name].view.node("back"))  # its Back button
            report.setdefault("back_from", []).append((name, app.current))
        real_run(app, max_frames=3, **kwargs)
        report["ran"] = True

    tesserae.App.run = run
    runpy.run_path(str(project / "app.py"), run_name="__main__")
    print("REPORT " + json.dumps(report))
''')


def _run(project, *args):
    result = subprocess.run([sys.executable, "-c", RUNNER, str(project), *args], capture_output=True, text=True,
                            timeout=120)
    assert result.returncode == 0, result.stderr[-2000:]
    line = next(line for line in result.stdout.splitlines() if line.startswith("REPORT "))
    return json.loads(line[len("REPORT "):])


def test_new_makes_a_runnable_app(tmp_path):
    assert cli.main(["new", "my-notes", "--dir", str(tmp_path)]) == 0
    project = tmp_path / "my-notes"
    assert sorted(p.name for p in project.iterdir()) == ["Home_View.yaml", "Home_ViewModel.py", "app.py"]
    report = _run(project)
    assert report["start"] == "Home" and report["location"] == "" and report["ran"]
    assert report["greeting"] == "Hello from My Notes" and report["count"] == "Clicked 1 times"
    assert report["button"] == ["button", "Click me"]  # a ButtonFilled fragment, named (M69)
    assert report["screens"] == ["Home"] and not report["shell"] and report["size"] == [480, 320]


def test_add_screen_adds_a_pair_and_loads_and_routes_it(tmp_path, capsys):
    cli.main(["new", "notes", "--dir", str(tmp_path)])
    project = tmp_path / "notes"
    assert cli.main(["add", "screen", "UserProfile", "--dir", str(project)]) == 0
    assert "with the route 'user-profile'" in capsys.readouterr().out
    assert (project / "UserProfile_View.yaml").is_file() and (project / "UserProfile_ViewModel.py").is_file()
    lines = (project / "app.py").read_text().splitlines()
    marker = lines.index(cli.IMPORT_MARKER)  # each line goes just above its marker, as it says
    assert lines[marker - 1] == "from UserProfile_ViewModel import UserProfileViewModel"
    assert lines[lines.index(cli.LOAD_MARKER) - 1] == 'app.route("user-profile", "UserProfile")'
    report = _run(project)
    assert report["screens"] == ["Home", "UserProfile"] and report["routes"] == ["", "user-profile"]
    assert report["back_from"] == [["UserProfile", "Home"]]  # its Back button goes back
    deep = _run(project, "user-profile")  # a deep link from the command line
    assert deep["start"] == "UserProfile" and deep["location"] == "user-profile"


def test_new_with_a_shell(tmp_path):
    assert cli.main(["new", "studio", "--shell", "--dir", str(tmp_path)]) == 0
    project = tmp_path / "studio"
    assert (project / "Studio_Shell.yaml").is_file() and (project / "Settings_View.yaml").is_file()
    report = _run(project)
    assert report["shell"] and report["screens"] == ["Home", "Settings"] and report["routes"] == ["", "settings"]
    assert report["rail"] == ["Home", "Settings"] and report["size"] == [960, 600]
    assert report["back_from"] == [["Settings", "Home"]]


@pytest.mark.parametrize("app_py", ["# an app of my own\n", f"# half of it\n{cli.IMPORT_MARKER}\n"])
def test_without_markers_add_screen_prints_the_lines(tmp_path, capsys, app_py):
    (tmp_path / "app.py").write_text(app_py)
    assert cli.main(["add", "screen", "Settings", "--dir", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "add these lines to it" in out and 'app.load(HERE / "Settings_View.yaml", SettingsViewModel)' in out
    assert 'app.route("settings", "Settings")' in out and "from Settings_ViewModel import SettingsViewModel" in out
    assert (tmp_path / "app.py").read_text() == app_py  # left alone


@pytest.mark.parametrize("argv, message", [
    (["new", "2fast"], "isn't a project name"),
    (["new", "my app"], "isn't a project name"),
    (["add", "screen", "settings"], "isn't a screen name"),
    (["add", "screen", "User_Profile"], "isn't a screen name"),
])
def test_bad_names_are_refused(tmp_path, capsys, argv, message):
    assert cli.main([*argv, "--dir", str(tmp_path)]) == 2
    err = capsys.readouterr().err
    assert err.startswith("tesserae: ") and message in err and err.count("\n") == 1


def test_nothing_is_overwritten(tmp_path, capsys):
    (tmp_path / "busy").mkdir()
    (tmp_path / "busy" / "notes.txt").write_text("mine")
    assert cli.main(["new", "busy", "--dir", str(tmp_path)]) == 2
    assert "isn't empty" in capsys.readouterr().err
    (tmp_path / "empty").mkdir()
    assert cli.main(["new", "empty", "--dir", str(tmp_path)]) == 0  # an empty folder is fine
    project = tmp_path / "empty"
    (project / "Settings_ViewModel.py").write_text("# mine")
    before = (project / "app.py").read_text()
    assert cli.main(["add", "screen", "Settings", "--dir", str(project)]) == 2
    assert "already exists" in capsys.readouterr().err
    assert not (project / "Settings_View.yaml").exists() and (project / "app.py").read_text() == before
    assert cli.main(["add", "screen", "Settings", "--dir", str(tmp_path / "missing")]) == 2
    assert "isn't a folder" in capsys.readouterr().err


def test_routes_and_words():
    assert [cli.screen_route(n) for n in ("Settings", "UserProfile", "Home2Go")] == ["settings", "user-profile", "home2-go"]
    assert cli._words("my-notes") == cli._words("my_notes") == cli._words("MyNotes") == ["my", "notes"]


def test_the_command_and_python_m_run(tmp_path):
    version = subprocess.run([sys.executable, "-m", "tesserae", "--version"], capture_output=True, text=True)
    assert version.returncode == 0 and version.stdout.startswith("tesserae ")
    made = subprocess.run([sys.executable, "-m", "tesserae", "new", "app", "--dir", str(tmp_path)],
                          capture_output=True, text=True)
    assert made.returncode == 0 and (tmp_path / "app" / "app.py").is_file()
    bad = subprocess.run([sys.executable, "-m", "tesserae", "new", "9"], capture_output=True, text=True, cwd=tmp_path)
    assert bad.returncode == 2 and bad.stderr.startswith("tesserae: ")
