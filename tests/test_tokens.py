"""M37 Phase 1: Tesserae's MD3 tokens (`tesserae.tokens`) match `tre`'s,
checked against `tre` 0.3.4 while it still has them (0.3.5 removes them,
`tre` D7)."""

import struct

import pytest
import tre

from tesserae import tokens

SEEDS = [(0x67, 0x50, 0xA4), (0xB3, 0x26, 0x1E), (0x00, 0x6A, 0x60), (0xFF, 0xB0, 0x00),
         (0x21, 0x96, 0xF3), (0x00, 0x00, 0x00), (0xFF, 0xFF, 0xFF), (0x7D, 0x52, 0x60)]


def _tre_roles(seed, dark, custom=None):
    window = tre.Window(width=10, height=10)
    window.set_theme((*seed, 0xFF), dark=dark, custom_theme_spec=custom)
    return {role: window.theme.role(role) for role in tokens.ROLES}


@pytest.mark.parametrize("dark", [False, True], ids=["light", "dark"])
@pytest.mark.parametrize("seed", SEEDS, ids=[bytes(s).hex() for s in SEEDS])
def test_every_role_matches_tre(seed, dark):
    assert tokens.color_scheme((*seed, 0xFF), dark) == _tre_roles(seed, dark)


def test_colors_overrides_match_tre():
    custom = {"colors": {"primary": "#00FF00", "surface": "rgb(10, 20, 30)"}}
    ours = tokens.resolve_scheme((0x67, 0x50, 0xA4, 0xFF), False, None, custom)
    assert ours == _tre_roles((0x67, 0x50, 0xA4), False, custom)


def test_seed_precedence_matches_tre_views():
    """`theme_seed`, else the custom theme's `seed:`, else the default
    theme's -- `tre`'s `View` rule."""
    red, blue = {"seed": "#FF0000"}, {"seed": "#0000FF"}
    purple = (0x67, 0x50, 0xA4, 0xFF)
    assert tokens.resolve_scheme(purple, False, blue, red) == tokens.color_scheme(purple)
    assert tokens.resolve_scheme(None, False, blue, red) == tokens.color_scheme((255, 0, 0, 255))
    assert tokens.resolve_scheme(None, False, blue, None) == tokens.color_scheme((0, 0, 255, 255))
    assert tokens.resolve_scheme(None, False, None, None) is None
    # and a View built with each resolves `primary` to the same colour
    for kwargs, ours in [
        ({"theme_seed": purple, "custom_theme_spec": red}, tokens.color_scheme(purple)),
        ({"custom_theme_spec": red, "default_theme_spec": blue}, tokens.color_scheme((255, 0, 0, 255))),
    ]:
        view = tre.View(spec={"id": "r", "kind": "Rect", "style": {"width": 1, "height": 1, "background": "primary"}}, **kwargs)
        tre.Window.from_view(view, width=10, height=10, title="t")
        assert view.node("r").get("fill") == ours["primary"]


def test_an_unknown_role_in_colors_is_an_error():
    with pytest.raises(ValueError, match="unknown color role 'primry'"):
        tokens.resolve_scheme((0, 0, 0, 255), False, None, {"colors": {"primry": "#000000"}})


@pytest.mark.parametrize("name", sorted(tokens.SHAPES))
def test_shape_tokens_match_tre(name):
    view = tre.View(spec={"id": "r", "kind": "Rect", "style": {"width": 1, "height": 1, "background": "#000000", "corner_radius": name}})
    assert view.node("r").get("corner_radius") == tokens.shape(name)


@pytest.mark.parametrize("name", sorted(tokens.ELEVATION_LEVELS))
def test_elevation_levels_match_tre(name):
    view = tre.View(spec={"id": "r", "kind": "Rect", "style": {"width": 1, "height": 1, "background": "#000000", "elevation": name}})
    assert view.node("r").get("elevation") == tokens.elevation(name)


def test_unknown_tokens_are_none_as_in_tre():
    assert tokens.shape("full") is None and tokens.elevation("level_6") is None and tokens.type_style("huge") is None


@pytest.mark.parametrize("role", sorted(tokens.TYPE_SCALE))
def test_type_roles_match_tre(role):
    window = tre.Window(width=10, height=10)
    window.set_theme((0x67, 0x50, 0xA4, 0xFF))
    style = tokens.type_style(role)
    f32 = lambda x: struct.unpack("f", struct.pack("f", x))[0]  # tre stores these as f32
    assert window.theme.typography(role) == (style.font_family, style.font_weight, style.font_size, f32(style.line_height))


def test_elevation_shadows_reproduce_tres_geometry():
    """`tre`'s own docs give level 1 as exactly this pair; the others
    follow `engine-render`'s key/ambient formulas."""
    assert tokens.elevation_shadows(0) == []
    assert tokens.elevation_shadows(1) == [((0, 0, 0, 77), 0.0, 1.0, 2.0, 0.0), ((0, 0, 0, 38), 0.0, 1.0, 3.0, 1.0)]
    assert tokens.elevation_shadows(3) == [((0, 0, 0, 77), 0.0, 1.0, 3.0, 0.0), ((0, 0, 0, 38), 0.0, 4.0, 8.0, 3.0)]
    assert tokens.elevation_shadows(5) == [((0, 0, 0, 77), 0.0, 4.0, 4.0, 0.0), ((0, 0, 0, 38), 0.0, 8.0, 12.0, 6.0)]


def test_elevation_shadows_are_accepted_by_tre():
    window = tre.Window(width=10, height=10)
    box = window.create("box", width=10, height=10, shadows=tokens.elevation_shadows(2))
    assert box.get("shadows") == tokens.elevation_shadows(2)


COLORS = ["#6750A4", "#6750a4", "#abc", "#abcd", "#6750A480", "rebeccapurple", "white", "Red", "transparent",
          "rgb(1,2,3)", "rgba(1,2,3,0.5)", "rgb(1 2 3)", "rgb(1 2 3 / 50%)", "hsl(120, 50%, 50%)",
          "hsla(120,50%,50%,0.5)", "hsl(200deg 40% 30%)", "rgb(10%, 50%, 100%)", "rgb(300,-5,0)",
          "rgba(1,2,3,0.25)", " #6750A4 "]


@pytest.mark.parametrize("raw", COLORS)
def test_colour_strings_parse_as_tre_parses_them(raw):
    view = tre.View(spec={"id": "r", "kind": "Rect", "style": {"width": 1, "height": 1, "background": raw}})
    tre.Window.from_view(view, width=10, height=10, title="t")
    assert tokens.parse_color(raw) == view.node("r").get("fill")


@pytest.mark.parametrize("raw", ["#12345", "notacolor", "rgb(1,2)", "rgb(a,b,c)"])
def test_invalid_colours_raise(raw):
    with pytest.raises(ValueError, match="invalid color"):
        tokens.parse_color(raw)


def test_wide_gamut_colours_say_they_arent_supported_yet():
    with pytest.raises(ValueError, match=r"oklch\(\) colours aren't supported by Tesserae yet"):
        tokens.parse_color("oklch(0.5 0.1 200)")
