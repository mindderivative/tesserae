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
    import json, re, runpy, sys
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
        window = "Window" in app._opened  # a window app: its screens are routed calls inside the window's view
        host = app._opened["Window" if window else "Main"]
        prefix = "root.screens.main." if window else "root."
        home = lambda name: host.node(prefix + name)
        report["greeting"] = home("greeting").get("text")
        report["button"] = [home("button").get(k) for k in ("role", "label")]
        if app.current == "Main":
            app.window.simulate("click", node=home("button"))
            report["count"] = home("count").get("text")
        report["screens"] = sorted(app._registered)
        report["routes"] = [r.pattern for r in app._routes]
        report["size"] = [app.window.get("width"), app.window.get("height")]
        report["borderless"] = app.borderless
        for name in report["screens"]:
            if name in ("Main", "Window"):  # a window app registers its window view too
                continue
            app.navigate(name)
            where = host if window else app._opened[name]
            back = f"root.screens.{re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()}.back" if window else "root.back"
            app.window.simulate("click", node=where.node(back))  # its Back button
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
    assert report["button"] == ["button", "Click me"]
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
    assert lines[marker - 3:marker] == ['app.bind(app.project.viewmodel("UserProfile"))', 'app.open_view("UserProfile")',
                                        'app.route("user-profile", "UserProfile")']
    assert "UserProfile_ViewModel" not in "\n".join(lines)
    report = _run(project)
    assert report["screens"] == ["Main", "UserProfile"] and report["routes"] == ["", "user-profile"]
    assert report["back_from"] == [["UserProfile", "Main"]]  # its Back button goes back
    deep = _run(project, "user-profile")  # a deep link from the command line
    assert deep["start"] == "UserProfile" and deep["location"] == "user-profile"


def test_a_custom_title_bar_goes_with_a_window(tmp_path, capsys):
    assert cli.main(["new", "lonely", "--custom-title-bar", "--dir", str(tmp_path)]) == 2
    assert "--custom-title-bar goes with --window" in capsys.readouterr().err


@pytest.mark.parametrize("app_py", ["# an app of my own\n", f"# half of it\n{cli.IMPORT_MARKER}\n"])
def test_without_markers_add_screen_prints_the_lines(tmp_path, capsys, app_py):
    (tmp_path / "app.py").write_text(app_py)
    assert cli.main(["add", "screen", "Settings", "--dir", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "add these lines to it" in out and 'app.open_view(HERE / "Settings_View.yaml")' in out and "app.bind(SettingsViewModel)" in out
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
    """`--window` makes a `widget: Window` view whose screens are routed calls of views, served by one ViewModel."""
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
    assert '{widget: UserProfile, name: user_profile, route: "user-profile"' in out and "Window_View.yaml" in out and "items:" in out
    assert (project / "Views" / "UserProfile_View.yaml").is_file()
    assert not (project / "ViewModels" / "UserProfile_ViewModel.py").exists()  # a screen of the window reads Window_ViewModel's names


@pytest.mark.parametrize("flags", [[], ["--window"], ["--window", "--custom-title-bar"]])
def test_a_new_project_is_in_the_current_view_language_and_checks_clean(tmp_path, flags):
    """#270: the templates write `widget:` views and ViewModels that serve a named view; `app.check()` and the migration tool find nothing to say."""
    import re

    assert cli.main(["new", "fresh", *flags, "--no-venv", "--dir", str(tmp_path)]) == 0
    project = tmp_path / "fresh"
    for path in [*project.glob("Views/*.yaml"), *project.glob("ViewModels/*.py"), project / "app.py"]:
        text = path.read_text()
        assert not re.search(r"^\s*-?\s*(kind|component|include|view|id):", text, re.M), path.name
        assert "app.load(" not in text and "load_shell" not in text
    out = subprocess.run([sys.executable, "-c", textwrap.dedent("""
        import runpy, sys
        from pathlib import Path
        import tesserae
        project = Path(sys.argv[1]); sys.path.insert(0, str(project)); sys.argv = ["app.py"]
        seen = {}
        tesserae.App.run = lambda app, *a, **k: seen.setdefault("problems", app.check())
        runpy.run_path(str(project / "app.py"), run_name="__main__")
        print("PROBLEMS", seen["problems"])
    """), str(project)], capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, out.stderr[-1500:]
    assert "PROBLEMS []" in out.stdout
    assert cli.main(["migrate-yaml", str(project)]) == 0


def test_a_screen_added_to_a_window_project_works_once_its_node_is_in_the_window(tmp_path, capsys):
    assert cli.main(["new", "studio", "--window", "--no-venv", "--dir", str(tmp_path)]) == 0
    project = tmp_path / "studio"
    cli.main(["add", "screen", "UserProfile", "--dir", str(project)])
    node = next(line for line in capsys.readouterr().out.splitlines() if line.strip().startswith("- {widget: UserProfile"))
    window = project / "Views" / "Window_View.yaml"
    window.write_text(window.read_text().rstrip("\n") + "\n      " + node.strip() + "\n")
    assert _run(project, "user-profile")["start"] == "UserProfile"
    report = _run(project)
    assert report["routes"] == ["", "settings", "user-profile"]
    assert ["UserProfile", "Main"] in report["back_from"]
