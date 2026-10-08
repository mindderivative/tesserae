"""`tesserae new` and `tesserae add screen`. Each test makes a project in
`tmp_path` (with `--no-venv`: the virtual environment is tested apart) and runs
it for real, in a subprocess: a small wrapper swaps `App.run` for a check that
clicks Main's button, follows a route
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
        home = app._registered["Main"].view
        report["greeting"] = home.node("greeting").get("text")
        report["button"] = [home.node("button").get(k) for k in ("role", "label")]
        if app.current == "Main":
            app.window.simulate("click", node=home.node("button"))
            report["count"] = home.node("count").get("text")
        report["screens"] = sorted(app._registered)
        report["routes"] = [r.pattern for r in app._routes]
        report["size"] = [app.window.get("width"), app.window.get("height")]
        report["borderless"] = app.borderless
        for name in report["screens"]:
            if name in ("Main", "Window"):  # a window app registers its window view too
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
    assert cli.main(["new", "my-notes", "--no-venv", "--dir", str(tmp_path)]) == 0
    project = tmp_path / "my-notes"
    assert sorted(p.name for p in project.iterdir()) == ["Components", "Styles", "Themes", "ViewModels", "Views", "app.py"]
    assert (project / "Views" / "Main_View.yaml").is_file() and (project / "ViewModels" / "Main_ViewModel.py").is_file()
    assert (project / "Components" / ".gitkeep").is_file()
    report = _run(project)
    assert report["start"] == "Main" and report["location"] == "" and report["ran"]
    assert report["greeting"] == "Hello from My Notes" and report["count"] == "Clicked 1 times"
    assert report["button"] == ["button", "Click me"]  # a ButtonFilled fragment, named (M69)
    assert report["screens"] == ["Main"] and report["size"] == [480, 320]


def test_add_screen_adds_a_pair_and_loads_and_routes_it(tmp_path, capsys):
    cli.main(["new", "notes", "--no-venv", "--dir", str(tmp_path)])
    project = tmp_path / "notes"
    assert cli.main(["add", "screen", "UserProfile", "--dir", str(project)]) == 0
    assert "with the route 'user-profile'" in capsys.readouterr().out
    assert (project / "Views" / "UserProfile_View.yaml").is_file()
    assert (project / "ViewModels" / "UserProfile_ViewModel.py").is_file()
    lines = (project / "app.py").read_text().splitlines()
    marker = lines.index(cli.LOAD_MARKER)  # the lines go just above the marker, as it says; found by name, so no import
    assert lines[marker - 2:marker] == ['app.load("UserProfile")', 'app.route("user-profile", "UserProfile")']
    assert "UserProfile_ViewModel" not in "\n".join(lines)
    report = _run(project)
    assert report["screens"] == ["Main", "UserProfile"] and report["routes"] == ["", "user-profile"]
    assert report["back_from"] == [["UserProfile", "Main"]]  # its Back button goes back
    deep = _run(project, "user-profile")  # a deep link from the command line
    assert deep["start"] == "UserProfile" and deep["location"] == "user-profile"


def test_new_with_a_shell_says_what_replaced_it(tmp_path, capsys):
    """0.4.5 (#108): `--shell` was removed; it says to use `--window`."""
    assert cli.main(["new", "studio", "--shell", "--no-venv", "--dir", str(tmp_path)]) == 2
    err = capsys.readouterr().err
    assert "`tesserae new --shell` was removed" in err and "tesserae new --window" in err
    assert not (tmp_path / "studio").exists()


def test_a_custom_title_bar_goes_with_a_window(tmp_path, capsys):
    assert cli.main(["new", "lonely", "--custom-title-bar", "--dir", str(tmp_path)]) == 2
    assert "--custom-title-bar goes with --window" in capsys.readouterr().err


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
    assert cli.main(["new", "empty", "--no-venv", "--dir", str(tmp_path)]) == 0  # an empty folder is fine
    project = tmp_path / "empty"
    (project / "ViewModels" / "Settings_ViewModel.py").write_text("# mine")
    before = (project / "app.py").read_text()
    assert cli.main(["add", "screen", "Settings", "--dir", str(project)]) == 2
    assert "already exists" in capsys.readouterr().err
    assert not (project / "Views" / "Settings_View.yaml").exists() and (project / "app.py").read_text() == before
    assert cli.main(["add", "screen", "Settings", "--dir", str(tmp_path / "missing")]) == 2
    assert "isn't a folder" in capsys.readouterr().err


def test_routes_and_words():
    assert [cli.screen_route(n) for n in ("Settings", "UserProfile", "Home2Go")] == ["settings", "user-profile", "home2-go"]
    assert cli._words("my-notes") == cli._words("my_notes") == cli._words("MyNotes") == ["my", "notes"]


def test_the_command_and_python_m_run(tmp_path):
    version = subprocess.run([sys.executable, "-m", "tesserae", "--version"], capture_output=True, text=True)
    assert version.returncode == 0 and version.stdout.startswith("tesserae ")
    made = subprocess.run([sys.executable, "-m", "tesserae", "new", "app", "--no-venv", "--dir", str(tmp_path)],
                          capture_output=True, text=True)
    assert made.returncode == 0 and (tmp_path / "app" / "app.py").is_file()
    bad = subprocess.run([sys.executable, "-m", "tesserae", "new", "9"], capture_output=True, text=True, cwd=tmp_path)
    assert bad.returncode == 2 and bad.stderr.startswith("tesserae: ")


def test_schema_says_where_the_yaml_schemas_are_and_prints_the_setting(capsys):
    """0.3.2 (#79): `tesserae schema` and `--settings`, for Red Hat's YAML language server."""
    assert cli.main(["schema"]) == 0
    listing = capsys.readouterr().out
    for name in cli.SCHEMA_FILES:
        assert str(cli.SCHEMAS / name) in listing and (cli.SCHEMAS / name).is_file()
    assert "**/*_View.yaml" in listing and "editor-support" in listing

    assert cli.main(["schema", "--settings"]) == 0
    setting = json.loads(capsys.readouterr().out)["yaml.schemas"]
    assert setting[str(cli.SCHEMAS / "tesserae-yaml-schema.json")] == ["**/*_View.yaml"]
    assert set(setting) == {str(cli.SCHEMAS / name) for name in cli.SCHEMA_FILES}


def _fake_run(monkeypatch, fail=False):
    calls = []

    def run(command, **kwargs):
        calls.append(command)
        if fail and "pip" in command:
            raise subprocess.CalledProcessError(1, command, stderr=b"ERROR: no network\n")
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(cli.subprocess, "run", run)
    return calls


def test_new_makes_a_virtual_environment_with_tesserae_in_it(tmp_path, monkeypatch):
    calls = _fake_run(monkeypatch)
    assert cli.main(["new", "notes", "--dir", str(tmp_path)]) == 0
    venv, install = calls
    assert venv[1:3] == ["-m", "venv"] and venv[3] == str(tmp_path / "notes" / ".venv")
    assert install[1:4] == ["-m", "pip", "install"] and install[-1].startswith("tesserae-ui")
    assert str(tmp_path / "notes" / ".venv") in install[0]


def test_no_venv_makes_none(tmp_path, monkeypatch):
    calls = _fake_run(monkeypatch)
    assert cli.main(["new", "notes", "--no-venv", "--dir", str(tmp_path)]) == 0 and calls == []


def test_a_failed_install_keeps_the_project_and_says_how_to_finish(tmp_path, monkeypatch, capsys):
    _fake_run(monkeypatch, fail=True)
    assert cli.main(["new", "notes", "--dir", str(tmp_path)]) == 2
    err = capsys.readouterr().err
    assert err.startswith("tesserae: made the project, but its virtual environment failed (ERROR: no network)")
    assert "pip install tesserae-ui" in err and (tmp_path / "notes" / "app.py").is_file()


def test_new_with_a_window(tmp_path):
    """0.4.4 (#101): `--window` makes a `kind: Window` view whose screens are routed `view:` nodes."""
    assert cli.main(["new", "studio", "--window", "--no-venv", "--dir", str(tmp_path)]) == 0
    project = tmp_path / "studio"
    assert (project / "Views" / "Window_View.yaml").is_file() and not list(project.glob("Views/*_Shell.yaml"))
    assert "load_shell" not in (project / "app.py").read_text()
    report = _run(project)
    assert report["ran"] and report["screens"] == ["Main", "Settings", "Window"]
    assert report["routes"] == ["", "settings"] and report["size"] == [960, 600]
    assert report["back_from"] == [["Settings", "Main"]]
    assert report["borderless"] is False
    assert _run(project, "settings")["start"] == "Settings"


def test_new_with_a_borderless_window(tmp_path):
    assert cli.main(["new", "studio", "--window", "--custom-title-bar", "--no-venv", "--dir", str(tmp_path)]) == 0
    report = _run(tmp_path / "studio")
    assert report["ran"] and report["borderless"] is True


def test_add_screen_to_a_window_project_says_where_the_view_node_goes(tmp_path, capsys):
    assert cli.main(["new", "studio", "--window", "--no-venv", "--dir", str(tmp_path)]) == 0
    project = tmp_path / "studio"
    assert cli.main(["add", "screen", "UserProfile", "--dir", str(project)]) == 0
    out = capsys.readouterr().out
    assert 'view: UserProfile_View.yaml, route: "user-profile"' in out and "Window_View.yaml" in out
    assert (project / "Views" / "UserProfile_View.yaml").is_file()
