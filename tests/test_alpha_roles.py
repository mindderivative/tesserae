"""#212: a colour may end in `@N%` to scale its alpha (`primary@12%`, `#6750A4@50%`), and `corner_radius: full` is a pill."""

import pytest

from tesserae import Signal, View, ViewModel, tokens
from tesserae.composed import open_composed
from tesserae.spec.build import SpecBuildError
from tesserae.spec.nodes import parse_view
from tesserae.spec.rules import RuleSheet
from tesserae.spec.widgets import Property, PropertyError
from tesserae.viewmodel import Bindings

SEED = (103, 80, 164, 255)


def box(style):
    return View({"id": "root", "kind": "Container", "style": {"width": 200, "height": 100}, "children": [
        {"id": "b", "kind": "Rect", "style": {"width": 100, "height": 40, **style}}]}, theme_seed=SEED)


def test_resolve_color_scales_a_roles_alpha_and_a_colours():
    roles = {"primary": (103, 80, 164, 255), "scrim": (0, 0, 0, 200)}
    assert tokens.resolve_color("primary", roles) == (103, 80, 164, 255)
    assert tokens.resolve_color("primary@12%", roles) == (103, 80, 164, 31)
    assert tokens.resolve_color("primary @ 38 %", roles) == (103, 80, 164, 97)
    assert tokens.resolve_color("primary@100%", roles) == (103, 80, 164, 255) and tokens.resolve_color("primary@0%", roles) == (103, 80, 164, 0)
    assert tokens.resolve_color("scrim@50%", roles) == (0, 0, 0, 100)  # a colour that has alpha keeps that fraction of it
    assert tokens.resolve_color("#FF000080@50%", None) == (255, 0, 0, 64)
    assert tokens.resolve_color("red@25.5%", None) == (255, 0, 0, 65)
    assert tokens.resolve_color("rgb(0 128 0)@50%", None) == (0, 128, 0, 128)
    assert tokens.resolve_color("#112233") == (17, 34, 51, 255)


@pytest.mark.parametrize("raw, message", [("primary@101%", "over 100%"), ("nope@12%", "unknown color identifier"), ("primary@12", "invalid color"),
                                          ("primary@%", "invalid color"), ("primary@-5%", "invalid color")])
def test_a_bad_alpha_or_base_is_an_error(raw, message):
    with pytest.raises(ValueError, match=message):
        tokens.resolve_color(raw, {"primary": (1, 2, 3, 255)})


def test_the_builder_takes_it_wherever_a_style_takes_a_colour():
    view = box({"background": "primary@12%", "border_color": "on_surface@38%", "border_width": 2})
    node = view.node("b")
    scheme = view._scheme
    assert node.get("fill") == (*scheme["primary"][:3], 31)
    assert node.get("stroke_color") == (*scheme["on_surface"][:3], 97)
    gradient = box({"background": {"gradient": "linear", "stops": ["primary@0%", "primary"], "angle": 90}}).node("b").get("fill")
    assert gradient is not None


def test_a_bad_style_colour_names_the_widget_and_the_field():
    with pytest.raises(SpecBuildError, match='widget "b": invalid style.background "primary@200%": the alpha'):
        box({"background": "primary@200%"})
    with pytest.raises(SpecBuildError, match='invalid style.background "prymary@12%"'):
        box({"background": "prymary@12%"})


def test_a_bound_colour_may_carry_an_alpha():
    class VM(ViewModel):
        def __init__(self, view):
            self.tint = Signal("primary@12%")
            super().__init__(view)

    view = View({"id": "root", "kind": "Container", "children": [
        {"id": "b", "kind": "Rect", "style": {"width": 50, "height": 20, "background": "surface"}, "bindings": {"background": "{{ tint.get() }}"}}]},
        theme_seed=SEED)
    vm = VM(view)
    assert view.node("b").get("fill")[3] == 31
    vm.tint.set("primary@50%")
    assert view.node("b").get("fill")[3] == 128


def test_the_new_syntax_takes_it_in_a_node_in_a_rule_and_as_a_colour_property():
    view = open_composed(parse_view("widget: Rect\nstyle: {width: 50, height: 20, background: 'primary@12%'}\n", "T_View.yaml"), Bindings(), theme_seed=SEED)
    assert view.node("root").get("fill")[3] == 31
    RuleSheet.of({"styles": [{"widget": "Rect", "style": {"background": "on_surface@38%"}}]})
    prop = Property("color")
    prop.name = "tint"
    assert prop.coerce("primary@12%") == "primary@12%" and prop.coerce("#112233@50%") == "#112233@50%"
    with pytest.raises(PropertyError, match="optionally ending in @N%"):
        prop.coerce("12%")


def test_full_is_a_pill_and_a_circle():
    assert tokens.shape("full") == tokens.FULL_RADIUS and tokens.shape("large") == 16.0 and tokens.shape("nope") is None
    assert "full" not in tokens.SHAPES  # the MD3 scale is unchanged; `full` is the one token that depends on the node's size

    def corners(style, size):
        view = View({"id": "root", "kind": "Container", "style": {"width": 200, "height": 100}, "children": [
            {"id": "b", "kind": "Rect", "style": {"width": size[0], "height": size[1], "background": "#FF0000", **style}}]}, theme_seed=SEED)
        view.window.advance(16)
        rgba, width, _ = view.window.snapshot(200, 100)
        pixel = lambda x, y: tuple(rgba[(y * width + x) * 4:(y * width + x) * 4 + 4])  # noqa: E731
        return view.node("b").get("corner_radius"), pixel(1, 1), pixel(0, size[1] // 2), pixel(size[0] // 2, 0)

    radius, corner, side, top = corners({"corner_radius": "full"}, (100, 40))
    assert radius == tokens.FULL_RADIUS and corner[3] == 0 and side[3] > 200 and top[3] == 255  # round ends, flat enough middle
    assert corners({"corner_radius": "full"}, (40, 40))[1][3] == 0  # a circle
    assert corners({"corner_radius": "none"}, (100, 40))[1][3] == 255


def test_full_works_in_a_themes_components_and_the_schema_lists_it():
    from tesserae.theme import Theme

    theme = Theme.resolve(theme_seed=SEED, dark=False, default_theme_spec=None, custom_theme_spec={"components": {"chip": {"corner_radius": "full"}}})
    assert theme.shape("chip") == tokens.FULL_RADIUS
