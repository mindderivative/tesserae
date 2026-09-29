"""M37 Phase 1: Tesserae's MD3 tokens (`tesserae.tokens`) match `tre`'s,
checked against `tre` 0.3.4's answers, recorded (M43, `tests/reference.py`)
since 0.3.5 removes them (`tre` D7)."""

import struct

import pytest
import tre

import reference
from tesserae import tokens

SEEDS = [(0x67, 0x50, 0xA4), (0xB3, 0x26, 0x1E), (0x00, 0x6A, 0x60), (0xFF, 0xB0, 0x00),
         (0x21, 0x96, 0xF3), (0x00, 0x00, 0x00), (0xFF, 0xFF, 0xFF), (0x7D, 0x52, 0x60)]


def _tre_roles(seed, dark, custom=None):
    def ask():
        window = tre.Window(width=10, height=10)
        window.set_theme((*seed, 0xFF), dark=dark, custom_theme_spec=custom)
        return {role: window.theme.role(role) for role in tokens.ROLES}
    return reference.tre(ask)


def _tre_read(spec, prop, show=False, **kwargs):
    """A `tre` `View` of `spec`'s node `r`'s `prop`, recorded."""
    def ask():
        view = tre.View(spec=spec, **kwargs)
        if show:
            tre.Window.from_view(view, width=10, height=10, title="t")
        return view.node("r").get(prop)
    return reference.tre(ask)


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
        spec = {"id": "r", "kind": "Rect", "style": {"width": 1, "height": 1, "background": "primary"}}
        assert _tre_read(spec, "fill", show=True, **kwargs) == ours["primary"]


def test_an_unknown_role_in_colors_is_an_error():
    with pytest.raises(ValueError, match="unknown color role 'primry'"):
        tokens.resolve_scheme((0, 0, 0, 255), False, None, {"colors": {"primry": "#000000"}})


@pytest.mark.parametrize("name", sorted(tokens.SHAPES))
def test_shape_tokens_match_tre(name):
    spec = {"id": "r", "kind": "Rect", "style": {"width": 1, "height": 1, "background": "#000000", "corner_radius": name}}
    assert _tre_read(spec, "corner_radius") == tokens.shape(name)


@pytest.mark.parametrize("name", sorted(tokens.ELEVATION_LEVELS))
def test_elevation_levels_match_tre(name):
    spec = {"id": "r", "kind": "Rect", "style": {"width": 1, "height": 1, "background": "#000000", "elevation": name}}
    assert _tre_read(spec, "elevation") == tokens.elevation(name)


def test_unknown_tokens_are_none_as_in_tre():
    assert tokens.shape("full") is None and tokens.elevation("level_6") is None and tokens.type_style("huge") is None


@pytest.mark.parametrize("role", sorted(tokens.TYPE_SCALE))
def test_type_roles_match_tre(role):
    def ask():
        window = tre.Window(width=10, height=10)
        window.set_theme((0x67, 0x50, 0xA4, 0xFF))
        return window.theme.typography(role)
    style = tokens.type_style(role)
    f32 = lambda x: struct.unpack("f", struct.pack("f", x))[0]  # tre stores these as f32
    assert reference.tre(ask) == (style.font_family, style.font_weight, style.font_size, f32(style.line_height))


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
    spec = {"id": "r", "kind": "Rect", "style": {"width": 1, "height": 1, "background": raw}}
    assert tokens.parse_color(raw) == _tre_read(spec, "fill", show=True)


@pytest.mark.parametrize("raw, message", [
    ("#12345", "wrong number of hex digits"), ("notacolor", "unknown color identifier"),  # tre's wording
    ("rgb(1,2)", "invalid color"), ("rgb(a,b,c)", "invalid color"),
])
def test_invalid_colours_raise(raw, message):
    with pytest.raises(ValueError, match=message):
        tokens.parse_color(raw)


#: M63: CSS Color 4's wide-gamut functions, every `color()` space, in and out of sRGB's gamut
#: (clipped), with `none`, angle units, percentages, alpha, comments and odd spacing.
WIDE_GAMUT = [
    "oklch(0.5 0.1 200)", "oklch(62.8% 0.2577 29.23)", "oklch(70% 0.4 145)", "oklch(0.7 none 30)",
    "oklch(0.6 0.15 1.2rad)", "oklch(0.6 0.15 0.25turn / 50%)", "OKLCH(0.9 0.05 300grad)",
    "oklab(0.5 0.1 -0.1)", "oklab(40% 25% -50%)", "oklab(1 0 0)", "oklab(0 0 0 / 0.3)",
    "lab(50 20 -30)", "lab(100 0 0)", "lab(0% 0 0)", "lab(29.2345% 39.3825 20.0664)", "lab(60 150 -150)",
    "lch(50 30 270)", "lch(52.2345% 72.2 56.2 / .5)", "lch(80 200 120)", "lch(none 40 none)",
    "hwb(120 10% 20%)", "hwb(0 100% 100%)", "hwb(200deg 0% 0%)", "hwb(-30 20 30 / 25%)", "hwb(90 60% 60%)",
    "color(srgb 0.2 0.4 0.6)", "color(srgb-linear 0.5 0.5 0.5)", "color(display-p3 1 0 0)",
    "color(display-p3 0.3 0.6 0.2 / 0.8)", "color(a98-rgb 0.5 0.2 0.9)", "color(prophoto-rgb 0.4 0.4 0.4)",
    "color(rec2020 0.1 0.8 0.3)", "color(xyz 0.2 0.3 0.4)", "color(xyz-d50 0.3 0.3 0.2)",
    "color(xyz-d65 0.9505 1 1.089)", "color(display-p3 none 0.5 0.5)", "color(srgb 120% -10% 50%)",
    "lab( 50 /* a comment */ 20 -30 )", "oklch(0.5 0.1 200 / none)", " hwb(60 5% 5%) ",
    "color(srgb 5e-1 2.5E-1 1e0)", "lab(5e1 +20 -3e1)", "color(srgb .5 +.25 -0)", "oklch(0.5 0.1 200 / 1.5)",
    "color(xyz none -0.5 -0.1)",  # a missing channel stays 0 in sRGB, though X = 0 would make red 234
    "color(xyz 1e39 1e39 0)",  # infinite, then NaN: a NaN channel is 0
    "oklch(0.6 50% 120)",  # 100% chroma is 0.4
    # near black, where each transfer's linear segment decides a byte
    "color(display-p3 0.03306 0.03306 0.03306)", "color(display-p3 0.00195 0.00195 0.00195)",
    "color(display-p3 0.00981 0.00981 0.00981)", "color(prophoto-rgb 0.00243 0.00243 0.00243)",
]


@pytest.mark.parametrize("raw", WIDE_GAMUT)
def test_wide_gamut_colours_parse_as_tre_parses_them(raw):
    spec = {"id": "r", "kind": "Rect", "style": {"width": 1, "height": 1, "background": raw}}
    assert tokens.parse_color(raw) == _tre_read(spec, "fill", show=True)


@pytest.mark.parametrize("raw, reason", [
    ("color(cmyk 0 0 0)", "unknown color space"), ("color()", "expected color space identifier"),
    ("lab(50 20)", "unknown color component"), ("oklch(0.5 0.1 20px)", "unknown angle dimension"),
    ("hwb(10% 0 0)", "unknown angle"), ("lab(50 20 -30", "expected closing parenthesis"),
    ("oklab(0.5 0 0) x", "expected end of string"), ("lch(50 /* 30 270)", "unclosed comment"),
    ("lab (50 20 -30)", "expected arguments"), ("lab(50, 20, -30)", "unknown color component"),
    ("color(--x 0 0 0)", "expected color space identifier"), ("color(- 0 0 0)", "expected color space identifier"),
])
def test_invalid_wide_gamut_colours_say_why(raw, reason):
    with pytest.raises(ValueError, match=rf"invalid color .*: {reason}$"):
        tokens.parse_color(raw)
