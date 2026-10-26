"""#288: a stylesheet rule's `part:` that names no node of the widget is an error naming the nearest part (it matched nothing and said nothing)."""

import pytest

from tesserae import App
from tesserae.shipped import ViewLibrary, shipped_rules
from tesserae.spec.nodes import LoadError, load_marked
from tesserae.spec.rules import RuleSheet, load_rule_sheet
from tesserae.spec import widgets as W

LIBRARY = ViewLibrary()


def sheet(text, parts_of=LIBRARY.parts_of):
    return RuleSheet.of(load_marked(text, "S_Stylesheet.yaml"), "S_Stylesheet.yaml", text, parts_of=parts_of)


def rule(widget, part):
    return f"styles:\n  - widget: {widget}\n    part: {part}\n    style: {{opacity: 1}}\n"


def test_the_parts_of_a_view_are_the_named_nodes_in_its_yaml():
    assert {"headline", "subhead", "body", "text", "picture", "actions"} <= LIBRARY.parts_of("Card")


def test_a_view_nobody_has_has_unknown_parts_so_its_rules_are_not_checked():
    assert LIBRARY.parts_of("NoSuchView") is None
    sheet(rule("NoSuchView", "whatever"))


def test_a_part_the_view_has_loads():
    sheet(rule("Card", "headline"))


def test_a_part_that_is_a_typo_is_an_error_at_the_part_naming_the_nearest():
    with pytest.raises(LoadError) as caught:
        sheet(rule("Card", "heading"))
    error = caught.value
    assert "Card has no part 'heading'" in str(error) and "did you mean 'headline'" in str(error) and "parts:" in str(error)
    assert (error.file, error.line) == ("S_Stylesheet.yaml", 3)  # the line of `part:`


def test_a_part_far_from_any_name_lists_the_parts_without_a_guess():
    with pytest.raises(LoadError) as caught:
        sheet(rule("Card", "zzzzzzzz"))
    assert "did you mean" not in str(caught.value) and "parts: " in str(caught.value)


def test_a_part_of_a_view_that_the_view_only_calls_is_not_its_part():
    """`Button`'s `label` is a part of Button; the node a Card calls it with is the Card's own business: only Card's own nodes count."""
    assert "label" not in LIBRARY.parts_of("Card")


def test_without_a_library_nothing_is_known_of_a_view_and_the_rule_is_not_checked():
    sheet(rule("Card", "heading"), parts_of=None)


def test_a_built_in_widget_has_no_parts_and_a_rule_for_one_is_an_error():
    name = next(n for n in W.names() if not W.lookup(n).view and not W.lookup(n).parts)
    with pytest.raises(LoadError, match=f"{name} has no parts"):
        sheet(rule(name, "label"))


@pytest.mark.parametrize("path", sorted(p for p in __import__("pathlib").Path(__file__).resolve().parent.parent.glob("src/tesserae/views/*_Stylesheet.yaml")),
                         ids=lambda p: p.name)
def test_every_shipped_stylesheet_still_loads_against_the_shipped_views(path):
    load_rule_sheet(path, parts_of=LIBRARY.parts_of)


def test_there_are_shipped_stylesheets_to_check():
    assert len(shipped_rules()) > 20


def open_main(tmp_path, **kw):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        "name: Main\nwidget: Container\nstyle: {width: 300, height: 200}\nchildren:\n  - {widget: Card, name: c, headline: Hi}\n")
    app = App(root=tmp_path, width=300, height=200, **kw)
    return app.open_view("Main")


def test_the_apps_own_stylesheet_is_checked_against_the_views_it_uses(tmp_path):
    with pytest.raises(LoadError, match="Card has no part 'heading'.*did you mean 'headline'"):
        open_main(tmp_path, stylesheet_spec={"styles": [{"widget": "Card", "part": "heading", "style": {"opacity": 1}}]})


def test_the_apps_own_stylesheet_with_a_real_part_opens(tmp_path):
    open_main(tmp_path, stylesheet_spec={"styles": [{"widget": "Card", "part": "headline", "style": {"opacity": 1}}]})


def test_a_projects_stylesheet_for_its_own_view_is_checked_with_its_file_and_line(tmp_path):
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Tile_View.yaml").write_text(
        "name: Tile\nwidget: Container\nparams: {title: {type: str, default: x}}\nchildren:\n  - {widget: Text, name: caption, text: hi}\n")
    (tmp_path / "Views" / "Tile_Stylesheet.yaml").write_text("styles:\n  - widget: Tile\n    part: captoin\n    style: {opacity: 1}\n")
    (tmp_path / "Views" / "Main_View.yaml").write_text("name: Main\nwidget: Container\nstyle: {width: 300, height: 200}\nchildren:\n  - {widget: Tile, name: t}\n")
    app = App(root=tmp_path, width=300, height=200)
    with pytest.raises(LoadError) as caught:
        app.open_view("Main")
    message = str(caught.value)
    assert "Tile has no part 'captoin'" in message and "did you mean 'caption'" in message and "Tile_Stylesheet.yaml:3" in message
