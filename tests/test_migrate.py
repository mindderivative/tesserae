"""#209 phase 7: `tesserae migrate-yaml` -- what it rewrites, what it leaves, what it refuses, and that a migrated view draws what the old one did."""

import shutil
from pathlib import Path

import pytest
import yaml
from loguru import logger

from tesserae import Signal, View, ViewModel
from tesserae import cli
from tesserae.composed import open_composed
from tesserae.migrate import migrate_project
from tesserae.spec.nodes import parse_view
from tesserae.spec.rules import RuleSheet, is_rule_sheet
from tesserae.viewmodel import Bindings

ROOT = Path(__file__).resolve().parent.parent
SEED = (103, 80, 164, 255)

OLD_VIEW = """# The counter screen.
# Edit while the app runs.
id: root
kind: Container
style: {width: 100, height: 40}
children:
  - id: label
    kind: Text
    text: {content: "Count: 0", font_family: Roboto, font_size: 20}  # a comment inside
    style: {width: 80, height: 20, foreground: "#FFFFFF"}
    bindings: {text: "{{ label.get() }}"}
  - id: go
    component: Pill
    with: {caption: Go}
"""
OLD_COMPONENT = """# A pill.
params: [caption]
id: root
kind: Rect
style: {width: 40, height: 20, background: "#112233"}
children:
  - id: text
    kind: Text
    text: {content: "{{ caption }}", font_family: Roboto, font_size: 12}
    style: {width: 30, height: 10, foreground: "#FFFFFF"}
"""
OLD_COMPONENT_SHEET = """# Pill's look.
styles:
  - id: root
    style: {background: primary}
  - id: text
    style: {foreground: on_primary}
"""
OLD_APP_SHEET = """styles:
  - kind: Rect
    style: {corner_radius: 4}
  - id: go
    style: {opacity: 0.5}
  - classes: [big]
    style: {width: 9}
"""
VIEWMODEL = """from tesserae import Signal, ViewModel


class CounterViewModel(ViewModel):
    def __init__(self, view):
        self.label = Signal("x")
        super().__init__(view)
"""


def project(tmp_path):
    (tmp_path / "Views").mkdir()
    (tmp_path / "Components").mkdir()
    (tmp_path / "Styles").mkdir()
    (tmp_path / "ViewModels").mkdir()
    (tmp_path / "Views" / "Counter_View.yaml").write_text(OLD_VIEW)
    (tmp_path / "ViewModels" / "Counter_ViewModel.py").write_text(VIEWMODEL)
    (tmp_path / "Components" / "Pill_Component.yaml").write_text(OLD_COMPONENT)
    (tmp_path / "Components" / "Pill_Stylesheet.yaml").write_text(OLD_COMPONENT_SHEET)
    (tmp_path / "Styles" / "App_Stylesheet.yaml").write_text(OLD_APP_SHEET)
    (tmp_path / "Themes").mkdir()
    (tmp_path / "Themes" / "Brand_Theme.yaml").write_text("seed: [1, 2, 3, 255]\nstyles:\n  - kind: Rect\n    style: {opacity: 1}\n")
    return tmp_path


def snapshot(root):
    return {str(p.relative_to(root)): p.read_text() for p in sorted(root.rglob("*")) if p.is_file()}


def test_a_dry_run_reports_and_writes_nothing(tmp_path):
    root = project(tmp_path)
    before = snapshot(root)
    report = migrate_project(root)
    assert snapshot(root) == before and not report.written
    statuses = {r.path.name: r.status for r in report.results}
    assert statuses == {"Counter_View.yaml": "migrated", "Pill_Component.yaml": "migrated", "Pill_Stylesheet.yaml": "migrated", "App_Stylesheet.yaml": "migrated"}
    assert "nothing written" in report.render(root)


def test_write_moves_the_project_to_the_current_syntax(tmp_path):
    root = project(tmp_path)
    report = migrate_project(root, write=True)
    assert report.written and not report.failed
    assert not (root / "Components" / "Pill_Component.yaml").exists() and (root / "Components" / "Pill_View.yaml").exists()
    view = (root / "Views" / "Counter_View.yaml").read_text()
    assert view.startswith("# The counter screen.\n# Edit while the app runs.\n")  # header comments are kept
    data = yaml.safe_load(view)
    assert data["name"] == "Counter" and data["widget"] == "Container" and "id" not in data and data["children"][0]["name"] == "label"
    assert data["children"][0]["text"] == "{{ label.get() }}" and data["children"][1] == {"widget": "Pill", "name": "go", "caption": "Go"}
    assert yaml.safe_load((root / "Components" / "Pill_View.yaml").read_text())["params"] == ["caption"]
    parse_view(view, "Counter_View.yaml", resolver={"Pill": __import__("tesserae.spec.widgets", fromlist=["x"]).decl_from_params("Pill", ["caption"])}.get)
    assert (root / "Themes" / "Brand_Theme.yaml").read_text() == snapshot_theme()  # themes are not touched


def snapshot_theme():
    return "seed: [1, 2, 3, 255]\nstyles:\n  - kind: Rect\n    style: {opacity: 1}\n"


def test_stylesheets_become_rules_a_components_by_part_and_an_apps_by_widget_and_name(tmp_path):
    root = project(tmp_path)
    migrate_project(root, write=True)
    component = yaml.safe_load((root / "Components" / "Pill_Stylesheet.yaml").read_text())
    assert component["styles"] == [{"widget": "Pill", "style": {"background": "primary"}}, {"widget": "Pill", "part": "text", "style": {"foreground": "on_primary"}}]
    app = yaml.safe_load((root / "Styles" / "App_Stylesheet.yaml").read_text())
    assert app["styles"] == [{"widget": "Rect", "style": {"corner_radius": 4}}, {"name": "go", "style": {"opacity": 0.5}},
                             {"classes": ["big"], "style": {"width": 9}}]
    assert (root / "Components" / "Pill_Stylesheet.yaml").read_text().startswith("# Pill's look.\n")
    assert is_rule_sheet(component) and is_rule_sheet(app)
    RuleSheet.of(component)
    RuleSheet.of(app)


def test_the_report_says_what_to_change_in_the_viewmodel_and_what_comments_were_lost(tmp_path):
    root = project(tmp_path)
    text = migrate_project(root).render(root)
    assert "ViewModels/Counter_ViewModel.py: add `views = \"Counter\"` to the class; let `__init__` take no `view` and call `super().__init__()`" in text
    assert "app.open_view(\"Counter\")" in text and "comments inside the file were not kept" in text
    assert "Pill_Component.yaml -> Components/Pill_View.yaml" in text


def test_a_fragment_is_never_named_after_a_viewmodel(tmp_path):
    root = project(tmp_path)
    (root / "ViewModels" / "Pill_ViewModel.py").write_text("")
    migrate_project(root, write=True)
    assert "name" not in yaml.safe_load((root / "Components" / "Pill_View.yaml").read_text())


def test_a_view_with_no_viewmodel_is_not_given_a_name(tmp_path):
    root = project(tmp_path)
    (root / "ViewModels" / "Counter_ViewModel.py").unlink()
    migrate_project(root, write=True)
    assert "name" not in yaml.safe_load((root / "Views" / "Counter_View.yaml").read_text())


def test_nothing_is_written_when_any_file_would_not_load_unless_forced(tmp_path):
    root = project(tmp_path)
    (root / "Components" / "Dyn_Component.yaml").write_text("params: [which]\nid: root\nkind: Container\nchildren:\n  - id: x\n    component: \"{{ which }}\"\n")
    before = snapshot(root)
    report = migrate_project(root, write=True)
    assert not report.written and snapshot(root) == before
    failed = report.failed
    assert [r.path.name for r in failed] == ["Dyn_Component.yaml"] and "no widget named '{{ which }}'" in failed[0].error
    assert "fix the failed files, or use --force" in report.render(root)
    forced = migrate_project(root, write=True, force=True)
    assert forced.written and (root / "Components" / "Pill_View.yaml").exists() and (root / "Components" / "Dyn_Component.yaml").exists()


def test_a_name_that_would_be_taken_is_a_failure_not_an_overwrite(tmp_path):
    root = project(tmp_path)
    (root / "Components" / "Pill_View.yaml").write_text("widget: Text\n")
    report = migrate_project(root, write=True)
    assert [r.error for r in report.failed] == ["Pill_View.yaml already exists"] and not report.written
    assert (root / "Components" / "Pill_Component.yaml").exists()


def test_files_already_in_the_new_syntax_and_files_that_are_not_views_are_left_alone(tmp_path):
    root = project(tmp_path)
    migrate_project(root, write=True)
    before = snapshot(root)
    second = migrate_project(root, write=True)
    assert snapshot(root) == before and all(r.status == "current" for r in second.results if r.path.name != "Brand_Theme.yaml")
    (root / "Views" / "Odd_View.yaml").write_text("- just\n- a list\n")
    (root / "Views" / "Bad_View.yaml").write_text("kind: [unclosed\n")
    third = migrate_project(root)
    statuses = {r.path.name: r.status for r in third.results}
    assert statuses["Odd_View.yaml"] == "skipped" and statuses["Bad_View.yaml"] == "failed"


def test_folders_that_are_not_the_projects_are_not_read(tmp_path):
    root = project(tmp_path)
    (root / ".venv").mkdir()
    (root / ".venv" / "Junk_View.yaml").write_text("kind: Rect\n")
    assert all(r.path.name != "Junk_View.yaml" for r in migrate_project(root).results)


def test_the_command_reports_writes_and_returns_the_exit_code(tmp_path, capsys):
    root = project(tmp_path)
    assert cli.main(["migrate-yaml", str(root)]) == 0
    assert "nothing written" in capsys.readouterr().out and (root / "Components" / "Pill_Component.yaml").exists()
    assert cli.main(["migrate-yaml", str(root), "--write"]) == 0
    assert capsys.readouterr().out.rstrip().endswith("written") and (root / "Components" / "Pill_View.yaml").exists()
    (root / "Components" / "Dyn_View.yaml").write_text("kind: Container\nchildren:\n  - id: x\n    component: Nope\n")
    assert cli.main(["migrate-yaml", str(root)]) == 1
    assert "failed" in capsys.readouterr().out
    assert cli.main(["migrate-yaml", str(root / "missing")]) == 2
    assert "is not a folder" in capsys.readouterr().err
    assert cli.main(["migrate-yaml", str(root), "--force"]) == 2
    assert "--force goes with --write" in capsys.readouterr().err


def test_an_old_syntax_view_says_once_per_file_how_to_move_on(tmp_path):
    from tesserae.spec import load

    path = tmp_path / "Old_View.yaml"
    path.write_text("id: root\nkind: Rect\nstyle: {width: 4, height: 4, background: '#112233'}\n")
    seen = []
    handler = logger.add(lambda m: seen.append(str(m)), level="WARNING")
    try:
        load._NOTED.discard(path.resolve())
        View(path, theme_seed=SEED)
        View(path, theme_seed=SEED)
        new = tmp_path / "New_View.yaml"
        new.write_text("widget: Rect\n")
        load._note_old_syntax(new, new.read_text())
        mixed = tmp_path / "Mixed_View.yaml"
        load._note_old_syntax(mixed, "widget: Rect\nkind: left-over\n")
    finally:
        logger.remove(handler)
    assert len(seen) == 1 and "Old_View.yaml is written in the 0.4.x view syntax" in seen[0] and "tesserae migrate-yaml" in seen[0]


# -- the shipped fragments --------------------------------------------------------------------------------------------------


def test_the_shipped_fragments_and_their_stylesheets_migrate_except_the_known_gaps(tmp_path):
    shutil.copytree(ROOT / "src" / "tesserae" / "spec" / "components", tmp_path / "components")
    report = migrate_project(tmp_path)
    migrated = [r for r in report.results if r.status == "migrated"]
    assert len(migrated) >= 150
    assert {r.path.name for r in report.failed} == {"ButtonGroup_Component.yaml"}  # a widget name from a parameter: the component pass
    assert sum(r.path.name.endswith("_Stylesheet.yaml") for r in migrated) >= 75
    assert sum(r.new_path.name.endswith("_View.yaml") for r in migrated if r.new_path) >= 75


# -- a migrated view draws what the old one did ------------------------------------------------------------------------------

LAYOUT = ("layout_x", "layout_y", "layout_width", "layout_height")
DRAWN = ("fill", "stroke_color", "stroke_width", "corner_radius", "opacity", "text", "font_size", "visible")


def dump(node):
    """Every node under `node`, in order, as the values it was laid out and painted with."""
    out = []

    def go(n):
        row = {}
        for key in (*LAYOUT, *DRAWN):
            try:
                row[key] = n.get(key)
            except ValueError:
                pass
        out.append(row)
        for child in n.children():
            go(child)

    go(node)
    return out


def stub(prefix, names):
    """An old-style and a new-style ViewModel with the same Signals and handlers."""
    def attrs(self):
        for name, value in names.items():
            if value is None:
                setattr(self, name, lambda *a: None)
            else:
                setattr(self, name, Signal(value))

    class Old(ViewModel):
        def __init__(self, view):
            attrs(self)
            super().__init__(view)

    class New(ViewModel):
        views = prefix

        def __init__(self):
            super().__init__()
            attrs(self)

    return Old, New


CASES = [
    ("examples/counter/Counter_View.yaml", "Counter", {"label": "Count: 0", "button_label": "Increment", "increment": None}),
    ("examples/getting_started/declarative/step1/Counter_View.yaml", "Counter", {}),
    ("examples/getting_started/declarative/step2/Counter_View.yaml", "Counter", {}),
    ("examples/getting_started/declarative/step3/Counter_View.yaml", "Counter", {}),
    ("examples/getting_started/declarative/step4/Counter_View.yaml", "Counter", {"label_text": "Count: 0", "increment": None}),
    ("examples/window_dock/Files_View.yaml", "Files", {}),
    ("examples/window_dock/Home_View.yaml", "Home", {}),
    ("examples/window_dock/Outline_View.yaml", "Outline", {}),
    ("examples/window_dock/Properties_View.yaml", "Properties", {}),
    ("examples/window_dock/Console_View.yaml", "Console", {"last": "ready"}),
    ("examples/window_dock/Notes_View.yaml", "Notes", {"note": "hello", "echo": "hello"}),
]


@pytest.mark.parametrize("path, prefix, names", CASES, ids=[c[0].split("examples/")[1] for c in CASES])
def test_a_migrated_view_draws_the_same_tree_as_the_old_one(tmp_path, path, prefix, names):
    source = ROOT / path
    # the old way
    old_vm, new_vm = stub(prefix, names)
    old_view = View(source, theme_seed=SEED)
    old_vm(old_view)
    # the new way: the same file, migrated
    copy = tmp_path / source.name
    copy.write_text(source.read_text())
    (tmp_path / f"{prefix}_ViewModel.py").write_text("")  # a ViewModel beside the view: the migration names the view after it
    migrate_project(tmp_path, write=True)
    doc = parse_view(copy.read_text(), copy.name)
    assert doc.name == prefix
    bindings = Bindings()
    bindings.bind(new_vm)
    new_view = open_composed(doc, bindings, base_dir=source.parent, theme_seed=SEED)
    assert dump(new_view.root) == dump(old_view.root)
