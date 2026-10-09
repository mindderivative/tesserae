"""#211: `max_lines`, `letter_spacing` and `selectable` on text, in both syntaxes."""

import pytest

from tesserae import View
from tesserae.composed import open_composed
from tesserae.spec.build import SpecBuildError
from tesserae.spec.nodes import LoadError, parse_view
from tesserae.viewmodel import Bindings

SEED = (103, 80, 164, 255)
LONG = "one two three four five six seven eight nine ten eleven twelve"


def spec(kind="Text", text=None, style=None):
    node = {"id": "t", "kind": kind, "text": {"content": "Hello world", "font_family": "Roboto", "font_size": 16, **(text or {})},
            "style": {"foreground": "#000000", **(style or {})}}
    return {"id": "root", "kind": "Container", "style": {"width": 300, "height": 300}, "children": [node]}


def laid_out(source):
    view = View(source, theme_seed=SEED)
    view.window.advance(16)
    return view, view.node("t")


def test_letter_spacing_widens_the_text_and_the_natural_size_follows():
    _, plain = laid_out(spec())
    _, spaced = laid_out(spec(text={"letter_spacing": 3}))
    assert spaced.get("letter_spacing") == 3.0 and plain.get("letter_spacing") == 0.0
    assert spaced.get("layout_width") > plain.get("layout_width") + 20  # 11 letters, 3 px each, measured into the node's size
    assert laid_out(spec(text={"letter_spacing": -0.5}))[1].get("letter_spacing") == -0.5


def test_max_lines_cuts_a_long_text_to_that_many_lines():
    wrapped = spec(text={"content": LONG}, style={"width": 80})
    _, free = laid_out(wrapped)
    _, two = laid_out(spec(text={"content": LONG, "max_lines": 2, "overflow": "ellipsis"}, style={"width": 80}))
    assert two.get("max_lines") == 2 and free.get("max_lines") is None
    assert free.get("layout_height") > 3 * two.get("layout_height") / 2 and two.get("layout_height") > 0


@pytest.mark.parametrize("text, message", [
    ({"letter_spacing": "wide"}, "text.letter_spacing is a number of pixels"), ({"letter_spacing": True}, "text.letter_spacing is a number of pixels"),
    ({"max_lines": 0}, "text.max_lines is a whole number from 1"), ({"max_lines": 1.5}, "text.max_lines is a whole number from 1"),
    ({"max_lines": True}, "text.max_lines is a whole number from 1"),
])
def test_a_wrong_value_names_the_widget_and_the_key(text, message):
    with pytest.raises(SpecBuildError, match=f'widget "t": {message}'):
        View(spec(text=text), theme_seed=SEED)


def test_a_link_takes_them_and_a_text_field_does_not():
    view, _ = laid_out(spec("Link", text={"max_lines": 1, "letter_spacing": 1}))
    assert view._built.nodes["t"].get("max_lines") == 1  # the Link's text; `node` is its box
    field = {"id": "t", "kind": "TextField", "text": {"content": "", "font_family": "Roboto", "font_size": 16, "max_lines": 2},
             "style": {"width": 100, "height": 30, "background": "#FFFFFF"}}
    with pytest.raises(SpecBuildError, match='a TextField has no text.max_lines'):
        View({"id": "root", "kind": "Container", "children": [field]}, theme_seed=SEED)
    field["text"] = {"content": "", "font_family": "Roboto", "font_size": 16, "letter_spacing": 1}
    with pytest.raises(SpecBuildError, match='a TextField has no text.letter_spacing'):
        View({"id": "root", "kind": "Container", "children": [field]}, theme_seed=SEED)


def test_a_dropped_key_goes_back_to_the_default_when_the_view_reloads():
    view, node = laid_out(spec(text={"max_lines": 2, "letter_spacing": 2}))
    view.reconcile(spec())
    assert (node.get("max_lines"), node.get("letter_spacing")) == (None, 0.0)


def view_of(source):
    return open_composed(parse_view(source, "T_View.yaml"), Bindings(), theme_seed=SEED)


def test_the_new_syntax_takes_them_as_properties_of_text_and_link():
    node = view_of("widget: Text\ntext: " + LONG + "\ntypography_role: body_large\nmax_lines: 2\nletter_spacing: 0.5\nselectable: true\n"
                   "style: {foreground: '#000000', width: 120}\n").node("root")
    assert (node.get("max_lines"), node.get("letter_spacing"), node.get("selectable")) == (2, 0.5, True)
    link = view_of("widget: Link\ntext: Go\ntypography_role: body_large\nmax_lines: 1\nstyle: {foreground: '#000000'}\n")
    assert link._built.nodes["root"].get("max_lines") == 1


def test_a_link_cannot_be_selectable_and_a_bad_value_is_an_error():
    with pytest.raises(LoadError, match="Link: no property 'selectable'"):
        parse_view("widget: Link\ntext: x\nselectable: true\n", "T_View.yaml")
    with pytest.raises(LoadError, match="Text: 'max_lines' takes a whole number"):
        parse_view("widget: Text\nmax_lines: 1.5\n", "T_View.yaml")
    with pytest.raises(SpecBuildError, match="text.max_lines is a whole number from 1"):
        view_of("widget: Text\ntext: x\ntypography_role: body_large\nmax_lines: 0\nstyle: {foreground: '#000000'}\n")
