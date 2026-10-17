"""#265: a `Text` has `runs` in the current language: styled pieces of one text (tre 0.5.4's `spans`), bound to data like any property, with a `link` run
calling `on_link`. They had been left behind when the older `text: {runs: ...}` was the only way to write them."""

import pytest

from tesserae import App, Signal, ViewModel
from tesserae.spec.nodes import LoadError
from tesserae.spec.build import SpecBuildError


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.was = Signal("$12")
        self.heard = []

    def opened(self, event):
        self.heard.append(event.href)


HEAD = "name: main\nwidget: Container\nstyle: {width: 400, height: 160, background: surface, padding: 16}\nchildren:\n"
BASE = "  - widget: Text\n    name: msg\n    typography_role: body_large\n    style: {foreground: on_surface, width: 360}\n"


def opened(tmp_path, body, vm=VM):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(HEAD + body)
    app = App(root=tmp_path, width=400, height=160)
    app.bind(vm)
    view = app.open_view("Main")
    app.show("main")
    view.window.advance(50)
    return app, view, view.node("root.msg"), app.bindings.viewmodel_for("main")


RUNS = BASE + '''    runs:
      - "Sale: "
      - {text: "{{ was }}", strikethrough: true, color: on_surface_variant}
      - {text: " $9", weight: 700, color: error}
      - " ends Friday. "
      - {text: "Read the terms", link: terms}
    handlers: {on_link: "opened(event)"}
'''


def test_runs_make_one_text_with_styled_ranges(tmp_path):
    app, view, node, vm = opened(tmp_path, RUNS)
    assert node.get("text") == "Sale: $12 $9 ends Friday. Read the terms"
    spans = node.get("spans")
    assert len(spans) == 3 and spans[0][:2] == (6, 9) and spans[1][2]["weight"] == 700.0 and spans[2][2]["link"] == "terms"


def test_a_run_that_reads_a_name_follows_it(tmp_path):
    app, view, node, vm = opened(tmp_path, RUNS)
    vm.was.set("$15")
    view.window.advance(50)
    assert node.get("text").startswith("Sale: $15 $9")
    assert node.get("spans")[0][:2] == (6, 9)  # the range follows the new text


def test_a_link_run_calls_on_link_with_its_href(tmp_path):
    app, view, node, vm = opened(tmp_path, RUNS)
    app.window.simulate("link", node, href="terms")
    assert vm.heard == ["terms"]


def test_the_offsets_are_utf8_bytes_not_characters(tmp_path):
    app, view, node, vm = opened(tmp_path, BASE + '    runs: ["é", {text: "ab", weight: 700}]\n')
    assert node.get("spans")[0][:2] == (2, 4)


def test_a_text_with_runs_can_be_selectable(tmp_path):
    app, view, node, vm = opened(tmp_path, BASE + '    selectable: true\n    runs: ["a ", {text: "b", weight: 700}]\n')
    assert node.get("selectable") is True


def test_a_run_may_be_a_whole_expression_that_gives_a_mapping(tmp_path):
    app, view, node, vm = opened(tmp_path, BASE + '    runs: ["Total ", "{{ {\'text\': was, \'weight\': 700} }}"]\n')
    assert node.get("text") == "Total $12" and node.get("spans")[0][2]["weight"] == 700.0


@pytest.mark.parametrize("runs, message", [
    ('[]', "list of pieces"),
    ('[{weight: 700}]', "string, or a mapping with `text:`"),
    ('[{text: a, bogus: 1}]', "unknown key"),
    ('[{text: a, link: ""}]', "link must be a non-empty string"),
    ('[{text: a, weight: heavy}]', "weight"),
    ('"just text"', "list"),
])
def test_bad_runs_are_refused_naming_the_text(tmp_path, runs, message):
    with pytest.raises((SpecBuildError, LoadError, ValueError)) as caught:
        opened(tmp_path, BASE + f"    runs: {runs}\n")
    assert message in str(caught.value) or "runs" in str(caught.value)


def test_runs_and_text_together_are_refused_where_they_are_written(tmp_path):
    with pytest.raises(LoadError) as caught:
        opened(tmp_path, BASE + "    text: hello\n    runs: [a]\n")
    assert "`runs:` is the text" in str(caught.value) and "Main_View.yaml" in str(caught.value)
    with pytest.raises(LoadError, match="runs"):
        opened(tmp_path, BASE + "    runs: [a]\n    text: hello\n")


@pytest.mark.parametrize("widget", ["Link", "TextInput", "Button"])
def test_runs_are_for_a_text_only(tmp_path, widget):
    with pytest.raises(LoadError, match="runs"):
        opened(tmp_path, f"  - {{widget: {widget}, name: msg, runs: [a]}}\n")


def test_a_mistake_in_a_run_expression_is_found_at_load_with_its_position(tmp_path):
    with pytest.raises(LoadError) as caught:
        opened(tmp_path, BASE + '    runs: ["{{ was + }}"]\n')
    assert "Main_View.yaml" in str(caught.value)


def test_a_name_a_run_reads_that_nothing_defines_is_named_when_the_view_opens(tmp_path):
    with pytest.raises(Exception, match="nothing_here"):
        opened(tmp_path, BASE + '    runs: ["{{ nothing_here }}"]\n')


def test_the_contract_check_reads_the_names_in_runs(tmp_path):
    """`check_view` lists names the ViewModel lacks, run strings included."""
    from tesserae.spec.nodes import parse_view
    from tesserae.viewmodel import check_view

    doc = parse_view(HEAD + BASE + '    runs: ["{{ nothing_here }}"]\n', "Main_View.yaml")
    assert any("nothing_here" in p for p in check_view(doc, VM()))


def test_a_file_in_the_older_syntax_with_text_runs_migrates_and_loads(tmp_path):
    """`tesserae migrate-yaml` failed on `text: {runs: ...}` (`Text: no property 'runs'`); it carries them over now."""
    import yaml

    from tesserae import cli

    (tmp_path / "Old_View.yaml").write_text(
        "id: root\nkind: Container\nchildren:\n  - id: msg\n    kind: Text\n    text:\n      typography_role: body_large\n      runs: ['Sale: ', {text: '$9', weight: 700, color: error}, {text: terms, link: terms}]\n"
        "    style: {foreground: on_surface}\n")
    assert cli.main(["migrate-yaml", str(tmp_path), "--write"]) == 0
    node = yaml.safe_load((tmp_path / "Old_View.yaml").read_text())["children"][0]
    assert node["widget"] == "Text" and node["runs"][1] == {"text": "$9", "weight": 700, "color": "error"} and "text" not in node
