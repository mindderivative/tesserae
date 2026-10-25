"""`tools/ci_plan.py` decides what CI runs: docs, partial or full. The rules are tested here, and that the workflow reads what the script writes."""

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent


def load():
    spec = importlib.util.spec_from_file_location("ci_plan", ROOT / "tools" / "ci_plan.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


plan = load()


@pytest.mark.parametrize("path, doc", [
    ("docs/guide/layout.md", True), ("docs/schema/tesserae-yaml-schema.json", True), ("design/yaml-language.md", True), ("LOG.md", True),
    ("README.md", True), ("mkdocs.yml", True), ("AGENTS.md", True), (".agents/skills/live-check/SKILL.md", True),
    ("src/tesserae/composed.py", False), ("tests/test_app.py", False), ("tools/check.py", False), ("pyproject.toml", False),
    ("src/tesserae/views/Button_View.yaml", False), (".github/workflows/ci.yml", False), ("LICENSE", False), ("src/README.md", False),
])
def test_what_counts_as_documentation(path, doc):
    assert plan.is_doc(path) is doc


def test_the_release_series_is_the_first_three_parts():
    assert plan.series("0.5.1.2") == "0.5.1" == plan.series("0.5.1")
    assert plan.series("0.5.2") != plan.series("0.5.1.9")


def mode(files, **kw):
    return plan.decide(files, **kw)[0]


def test_only_documentation_is_a_docs_run():
    assert mode(["docs/index.md", "LOG.md"]) == "docs"


def test_documentation_with_code_is_a_partial_run():
    assert mode(["docs/index.md", "src/tesserae/composed.py"]) == "partial"


def test_a_change_with_no_files_is_not_called_documentation():
    assert mode([]) == "partial"


@pytest.mark.parametrize("trigger", [
    {"dispatch": "full"}, {"labels": ["bug", "full-test"]}, {"message": "fix a thing [full-ci]"}, {"message": "Fix [Full CI]"},
    {"base_version": "0.5.1.9", "head_version": "0.5.2"}, {"base_version": "0.5.0.31", "head_version": "0.5.1"},
])
def test_a_full_run_is_called_for_or_comes_with_a_new_release_series(trigger):
    assert mode(["docs/index.md"], **trigger) == "full"  # even for documentation alone


def test_a_point_release_in_the_same_series_is_not_a_full_run():
    assert mode(["src/tesserae/composed.py"], base_version="0.5.1.1", head_version="0.5.1.2") == "partial"


def test_other_labels_and_an_auto_dispatch_change_nothing():
    assert mode(["src/tesserae/composed.py"], labels=["bug"], dispatch="auto") == "partial"


@pytest.mark.parametrize("asked", ["docs", "partial"])
def test_a_manual_run_may_ask_for_a_mode(asked):
    assert mode(["src/tesserae/composed.py"], dispatch=asked) == asked


def test_partial_picks_the_tests_that_cover_the_change():
    tests, fallback = plan.partial_tests(["src/tesserae/widgets/buttons.py"])
    assert "tests/test_button.py" in tests and not fallback


def test_partial_includes_the_tests_that_import_a_core_module():
    tests, _ = plan.partial_tests(["src/tesserae/__init__.py"])
    assert len(tests) > 100  # nearly everything imports `tesserae`


def test_partial_with_nothing_picked_runs_the_smoke_tests():
    tests, fallback = plan.partial_tests(["LICENSE"])
    assert fallback and tests == list(plan.SMOKE)


def test_the_smoke_tests_exist_and_include_the_run_of_every_example():
    assert all((ROOT / t).exists() for t in plan.SMOKE)
    assert "tests/test_examples_run.py" in plan.SMOKE


def test_the_workflow_has_no_separate_steps_for_the_examples():
    """`tests/test_examples_run.py` runs them; a second run per platform is the same apps again."""
    text = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "examples/" not in text.replace("`tests/test_examples_run.py`", "")


def test_the_doc_tests_exist_and_are_found():
    found = plan.doc_tests()
    assert "tests/test_api_docs.py" in found and "tests/test_tutorials_current.py" in found and "tests/test_yaml_schema.py" in found
    assert all((ROOT / t).exists() for t in found)


def repo(tmp_path, monkeypatch):
    def git(*args):
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=tmp_path, check=True, capture_output=True)
    git("init", "-q", "-b", "main")
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "0.5.1.1"\ndependencies = ["a"]\n')
    git("add", "."); git("commit", "-qm", "one")
    monkeypatch.setattr(plan, "ROOT", tmp_path)
    return git


def test_a_version_bump_alone_is_not_a_packaging_change(tmp_path, monkeypatch):
    git = repo(tmp_path, monkeypatch)
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "0.5.1.2"\ndependencies = ["a"]\n')
    git("commit", "-qam", "bump")
    assert plan.packaging_changed(["pyproject.toml"], "HEAD~1", "HEAD") is False
    assert plan.version_at("HEAD~1") == "0.5.1.1" and plan.version_at("HEAD") == "0.5.1.2"


def test_a_dependency_change_in_pyproject_is_a_packaging_change(tmp_path, monkeypatch):
    git = repo(tmp_path, monkeypatch)
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "0.5.1.2"\ndependencies = ["a", "b"]\n')
    git("commit", "-qam", "dep")
    assert plan.packaging_changed(["pyproject.toml"], "HEAD~1", "HEAD") is True


def test_a_packaging_file_is_a_packaging_change():
    assert plan.packaging_changed(["src/tesserae/cli.py"], "HEAD", "HEAD") is True
    assert plan.packaging_changed(["src/tesserae/composed.py"], "HEAD", "HEAD") is False


def test_a_new_branch_is_compared_with_the_trunk(tmp_path, monkeypatch):
    git = repo(tmp_path, monkeypatch)
    git("update-ref", "refs/remotes/origin/main", "HEAD")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("x")
    git("add", "."); git("commit", "-qm", "docs")
    files, base = plan.changed("0" * 40, "HEAD")
    assert files == ["docs/a.md"]


def test_the_workflow_reads_exactly_what_the_script_writes():
    workflow = yaml.safe_load((ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))
    declared = set(workflow["jobs"]["plan"]["outputs"])
    assert declared == set(plan.OUTPUTS)
    used = set()
    for name, job in workflow["jobs"].items():
        used |= set(__import__("re").findall(r"needs\.plan\.outputs\.(\w+)", json.dumps(job)))
    assert used <= declared, f"the workflow reads outputs the plan job does not declare: {used - declared}"


def test_the_output_file_gets_the_values(tmp_path, monkeypatch):
    out = tmp_path / "out"
    monkeypatch.setenv("GITHUB_OUTPUT", str(out))
    plan.emit({key: "x" for key in plan.OUTPUTS})
    assert set(line.split("=")[0] for line in out.read_text().splitlines()) == set(plan.OUTPUTS)


@pytest.mark.parametrize("tool", ["docs_audit", "check"])
def test_the_checks_use_the_running_python_when_the_checkout_has_no_venv(tool, tmp_path):
    """CI installs into the runner's Python and has no `.venv`: a hard-coded `.venv/bin/python` failed the first docs job (#289 push)."""
    import sys

    spec = importlib.util.spec_from_file_location(tool, ROOT / "tools" / f"{tool}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.venv_python(tmp_path) == sys.executable
    (tmp_path / ".venv" / "bin").mkdir(parents=True)
    (tmp_path / ".venv" / "bin" / "python").write_text("")
    assert module.venv_python(tmp_path) == str(tmp_path / ".venv" / "bin" / "python")
