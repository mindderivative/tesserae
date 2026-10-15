"""#273: `style: row_Style.yaml` in a view of the 0.5.0 language was accepted and ignored (the node laid out at 0 by 0). It is refused where it is written, and
`tesserae migrate-yaml` writes the file's fields into the node."""

import pytest
import yaml

from tesserae import App, ViewModel, cli
from tesserae.spec.nodes import LoadError

OLD = "id: root\nkind: Container\nchildren:\n  - {id: a, kind: Rect, style: row_Style.yaml}\n"


class VM(ViewModel):
    views = "style"


def _project(tmp_path, view, style="style: {width: 77, height: 5, background: error}\n"):
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Style_View.yaml").write_text(view)
    (tmp_path / "Views" / "row_Style.yaml").write_text(style)
    return tmp_path


def test_a_view_that_names_a_style_file_is_refused_where_it_says_so(tmp_path):
    _project(tmp_path, "name: style\nwidget: Container\nchildren:\n  - {widget: Container, name: a, style: row_Style.yaml}\n")
    app = App(root=tmp_path)
    app.bind(VM)
    with pytest.raises(LoadError) as caught:
        app.open_view("Style")
    text = str(caught.value)
    assert "Style_View.yaml:4" in text and "style file" in text and "migrate-yaml" in text


def test_the_migration_writes_the_files_fields_into_the_node(tmp_path, capsys):
    _project(tmp_path, OLD.replace("id: root\n", "id: root\n"))
    assert cli.main(["migrate-yaml", str(tmp_path), "--write"]) == 0
    migrated = yaml.safe_load((tmp_path / "Views" / "Style_View.yaml").read_text())
    node = migrated["children"][0]
    assert node["style"] == {"width": 77, "height": 5, "background": "error"}
    assert "style: row_Style.yaml was written in" in capsys.readouterr().out


def test_a_migrated_view_lays_out_as_the_old_one_did(tmp_path):
    from tesserae import App as A

    _project(tmp_path, "id: root\nkind: Container\nstyle: {width: 200, height: 100}\nchildren:\n  - {id: a, kind: Rect, style: row_Style.yaml}\n")
    old = A(root=tmp_path, width=200, height=100)
    view = old.build_view(tmp_path / "Views" / "Style_View.yaml")  # the older loader expands the style file
    old.window.advance(16)
    before = [view.node("a").get(k) for k in ("layout_width", "layout_height")]
    assert before == [77.0, 5.0]
    assert cli.main(["migrate-yaml", str(tmp_path), "--write"]) == 0
    new = A(root=tmp_path, width=200, height=100)
    new.bind(VM)
    migrated = new.open_view("Style")
    new.window.advance(16)
    assert [migrated.node("root.a").get(k) for k in ("layout_width", "layout_height")] == before


def test_a_file_holding_the_fields_themselves_is_written_in_too(tmp_path):
    _project(tmp_path, OLD, style="{width: 12, height: 3}\n")
    assert cli.main(["migrate-yaml", str(tmp_path), "--write"]) == 0
    assert yaml.safe_load((tmp_path / "Views" / "Style_View.yaml").read_text())["children"][0]["style"] == {"width": 12, "height": 3}


def test_a_style_file_that_is_missing_is_reported_and_nothing_is_written(tmp_path, capsys):
    _project(tmp_path, OLD.replace("row_Style.yaml", "gone_Style.yaml"))
    assert cli.main(["migrate-yaml", str(tmp_path), "--write"]) == 1
    out = capsys.readouterr().out
    assert "could not be read" in out and "nothing written" in out
    assert "kind: Container" in (tmp_path / "Views" / "Style_View.yaml").read_text()  # still the old file


def test_two_style_files_of_one_name_elsewhere_are_not_guessed_between(tmp_path, capsys):
    """Beside the view it is that one; found only under the project, the name must be unique."""
    _project(tmp_path, OLD.replace("row_Style.yaml", "shared_Style.yaml"))
    for folder in ("a", "b"):
        (tmp_path / folder).mkdir()
        (tmp_path / folder / "shared_Style.yaml").write_text("{width: 1}\n")
    assert cli.main(["migrate-yaml", str(tmp_path), "--write"]) == 1
    assert "could not be read" in capsys.readouterr().out
