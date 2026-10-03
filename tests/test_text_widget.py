"""M64 (#11): `tesserae.widgets.text`, plain text in a type role and a
colour of the theme, from the `Text` fragment. `.content` is a `Signal`
that re-measures the text; a re-theme keeps its content and follows the
theme's type scale, which every widget now gets (`Widget` hands its
theme's `typography:` to its view, as it does `components:`).
"""

import math
import pytest
import tre
import yaml

from tesserae import App, Theme, View, tokens
from tesserae.spec import expand_components_to_spec
from tesserae.spec.build import SpecBuildError
from tesserae.widgets import link, text

SEED = (0x67, 0x50, 0xA4, 0xFF)
BASE = tokens.baseline_scheme()
BIG = {"typography": {"body_medium": {"font_size": 20}, "body_large": {"font_size": 30}}}


def _window():
    return tre.Window(width=400, height=200)


def _measure(window, node, content):
    """The size a Text is given: its measured size, rounded up to whole pixels (the engine rounds a width down,
    which wrapped text that fit)."""
    width, height = window.measure_text(content, font_family=node.get("font_family"), font_size=node.get("font_size"),
                                        font_weight=node.get("font_weight"), line_height=node.get("line_height"))
    return float(math.ceil(width)), float(math.ceil(height))


def test_text_is_body_medium_on_surface_and_its_own_size():
    window = _window()
    t = text(window, "Hello", x=10, y=5)
    style = tokens.type_style("body_medium")
    node = t.node
    assert (node.get("text"), node.get("font_size"), node.get("font_weight")) == (
        "Hello", style.font_size, style.font_weight)
    assert node.get("font_family") == style.font_family and node.get("fill") == BASE["on_surface"]
    assert (node.get("width"), node.get("height")) == _measure(window, node, "Hello")
    assert (node.get("position"), node.get("x"), node.get("y")) == ("absolute", 10.0, 5.0)
    assert node.parent() == window.root


def test_a_type_role_and_a_colour_role_or_string():
    window = _window()
    title = text(window, "Title", typography_role="title_large", color="primary")
    assert title.node.get("font_size") == tokens.type_style("title_large").font_size
    assert title.node.get("fill") == BASE["primary"]
    red = text(window, "Alert", color="#FF0000")
    assert red.node.get("fill") == (255, 0, 0, 255)


def test_setting_content_re_measures_it():
    window = _window()
    t = text(window, "Hi")
    t.content.set("A longer line of text")
    assert t.node.get("text") == "A longer line of text"
    assert (t.node.get("width"), t.node.get("height")) == _measure(window, t.node, "A longer line of text")


def test_a_given_width_is_kept():
    window = _window()
    t = text(window, "Hi", width=150)
    assert t.node.get("width") == 150.0
    t.content.set("A much longer line than before")
    assert t.node.get("width") == 150.0 and t.node.get("height") == _measure(window, t.node, "x")[1]
    t.content.set("Three\nlines\nnow")  # the height follows the content, the width stays
    assert t.node.get("width") == 150.0 and t.node.get("height") == _measure(window, t.node, "Three\nlines\nnow")[1]
    assert t.node.get("height") > 2 * _measure(window, t.node, "x")[1]


def test_a_re_theme_keeps_the_content_and_takes_the_themes_type_scale():
    window = _window()
    t = text(window, "Hello")
    t.content.set("Changed")
    theme = Theme.resolve(theme_seed=SEED, dark=True, custom_theme_spec=BIG)
    t.set_theme(theme)
    assert t.node.get("text") == "Changed" and t.node.get("font_size") == 20.0
    assert (t.node.get("width"), t.node.get("height")) == _measure(window, t.node, "Changed")
    assert t.node.get("fill") == theme.role("on_surface")
    t.content.set("Again")  # and later content keeps the theme's font
    assert t.node.get("font_size") == 20.0 and t.node.get("width") == _measure(window, t.node, "Again")[0]


def test_every_widget_takes_its_themes_type_scale():
    window = _window()
    theme = Theme.resolve(theme_seed=SEED, custom_theme_spec=BIG)
    assert text(window, "Hi", theme=theme).node.get("font_size") == 20.0
    go = link(window, "Go", 100)
    assert [c.get("font_size") for c in go.node.children()] == [tokens.type_style("body_large").font_size]
    go.set_theme(theme)
    assert [c.get("font_size") for c in go.node.children()] == [30.0]


def test_it_follows_the_apps_theme():
    app = App(width=400, height=200, theme_seed=SEED, dark=False)
    t = text(app.window, "Hello")
    t.content.set("Kept")
    assert t.node.get("fill") == app.theme.role("on_surface")
    app.set_dark(True)
    assert t.node.get("fill") == Theme.resolve(theme_seed=SEED, dark=True).role("on_surface")
    assert t.node.get("text") == "Kept"


def test_destroyed_it_stops_listening():
    window = _window()
    t = text(window, "Hello")
    t.destroy()
    t.content.set("After")  # its effect is gone: nothing touches the destroyed node


def test_an_unknown_type_role_is_named():
    with pytest.raises(SpecBuildError, match='unknown text.typography_role "huge"'):
        text(_window(), "Hi", typography_role="huge")


def test_the_fragment_works_in_a_view():
    spec = expand_components_to_spec(yaml.safe_dump({"id": "title", "component": "Text",
                                                     "with": {"text": "Notes", "typography_role": "headline_small"}}))
    assert spec["kind"] == "Text" and spec["style"]["foreground"] == "on_surface"
    view = View({"id": "root", "kind": "Container", "children": [spec]}, theme_seed=SEED)
    node = view.node("title")
    assert node.get("text") == "Notes" and node.get("font_size") == tokens.type_style("headline_small").font_size
    assert node.get("width") > 0
    plain = expand_components_to_spec(yaml.safe_dump({"id": "p", "component": "Text", "with": {"text": "Body"}}))
    assert plain["text"]["typography_role"] == "body_medium" and plain["style"]["foreground"] == "on_surface"
