"""M38 Phase 1: `tesserae.Theme` answers what `tre`'s `Window.theme` does
-- checked against it while 0.3.4 still has it -- plus MD3 motion."""

import struct

import pytest
import tre

from tesserae import Theme, tokens
from tesserae.spec.build import shipped_default_theme

SEED = (0x67, 0x50, 0xA4, 0xFF)
CUSTOM = {
    "components": {
        "card": {"corner_radius": "large"},            # replaces the default's card entry
        "card.outlined": {"elevation": "level_2"},
        "dialog": {"corner_radius": 20, "elevation": 5},
        "fab.small": {"corner_radius": "extra_small"},
    },
    "typography": {"body_large": {"font_size": 18, "font_family": "Inter"}, "title_small": {"font_weight": 700}},
}


def _tre_theme(custom=None, default=None):
    window = tre.Window(width=10, height=10)
    window.set_theme(SEED, custom_theme_spec=custom, default_theme_spec=default)
    return window.theme


def _keys(*specs):
    keys = set()
    for spec in specs:
        keys |= set((spec or {}).get("components") or {})
    return sorted(keys)


LOOKUPS = [(k.split(".")[0], k.split(".")[1] if "." in k else None) for k in _keys(shipped_default_theme(), CUSTOM)]
LOOKUPS += [("card", "elevated"), ("card", "nope"), ("nothing", None), ("fab", "large"), ("fab", None)]


@pytest.mark.parametrize("custom", [None, CUSTOM], ids=["shipped default", "with a custom theme"])
@pytest.mark.parametrize("component, variant", LOOKUPS, ids=[f"{c}.{v}" for c, v in LOOKUPS])
def test_shape_and_elevation_match_tre(custom, component, variant):
    ours, theirs = Theme.resolve(SEED, custom_theme_spec=custom), _tre_theme(custom)
    assert ours.shape(component, variant) == theirs.shape(component, variant)
    assert ours.elevation(component, variant) == theirs.elevation(component, variant)


def _f32(x):
    return struct.unpack("f", struct.pack("f", x))[0]


@pytest.mark.parametrize("custom", [None, CUSTOM], ids=["shipped default", "with a custom theme"])
@pytest.mark.parametrize("role", sorted(tokens.TYPE_SCALE) + ["nope"])
def test_typography_matches_tre(custom, role):
    ours, theirs = Theme.resolve(SEED, custom_theme_spec=custom).typography(role), _tre_theme(custom).typography(role)
    if theirs is None:
        assert ours is None
    else:
        assert (ours.font_family, ours.font_weight, ours.font_size, _f32(ours.line_height)) == theirs


def test_a_custom_theme_entry_replaces_the_defaults_for_the_same_key():
    default = {"components": {"chip": {"corner_radius": 3, "elevation": 1}}, "typography": {"label_large": {"font_size": 20, "font_weight": 300}}}
    custom = {"components": {"chip": {"corner_radius": 9}}, "typography": {"label_large": {"font_size": 15}}}
    ours, theirs = Theme.resolve(SEED, default_theme_spec=default, custom_theme_spec=custom), _tre_theme(custom, default)
    assert ours.elevation("chip") == theirs.elevation("chip") is None  # the whole entry was replaced
    assert ours.typography("label_large").font_weight == theirs.typography("label_large")[1] == 500.0


def test_roles_and_is_set():
    assert Theme.resolve(SEED).role("primary") == _tre_theme().role("primary")
    unthemed = Theme.resolve()
    assert unthemed.is_set is False and unthemed.role("primary") is None
    assert Theme.resolve(SEED).role("not_a_role") is None


def test_an_unknown_component_token_is_an_error_worded_as_tres():
    bad = {"components": {"card": {"corner_radius": "huge"}}}
    with pytest.raises(ValueError, match=r"components: .card. has an unknown corner_radius token"):
        Theme.resolve(SEED, custom_theme_spec=bad)
    with pytest.raises(ValueError, match=r"components: .card. has an unknown corner_radius token"):
        _tre_theme(bad)


def test_malformed_sections_are_errors():
    for bad in ({"components": {"card": {"radius": 3}}}, {"typography": {"body_large": {"size": 3}}}, {"colours": {}}):
        with pytest.raises(ValueError):
            Theme.resolve(SEED, custom_theme_spec=bad)


def test_motion_tokens():
    assert Theme.easing("standard") == (0.2, 0.0, 0.0, 1.0)
    assert Theme.easing("emphasized_decelerate") == (0.05, 0.7, 0.1, 1.0)
    assert Theme.easing("emphasized") == (0.2, 0.0, 0.0, 1.0)  # MD3's single-bezier form (M38 Q4)
    assert (Theme.duration("short1"), Theme.duration("medium2"), Theme.duration("long4"), Theme.duration("extra_long4")) == (50, 300, 600, 1000)
    with pytest.raises(ValueError, match="unknown easing"):
        Theme.easing("bouncy")
    window = tre.Window(width=10, height=10)
    box = window.create("box", width=10, height=10)
    for name in ("standard", "emphasized", "standard_accelerate"):
        box.animate("opacity", 0.5, Theme.duration("short2"), easing=Theme.easing(name))  # tre takes every one


def test_views_and_apps_expose_their_resolved_theme(tmp_path):
    from tesserae import App, View

    custom = {"components": {"card": {"corner_radius": 7}}}
    view = View({"id": "r", "kind": "Container"}, theme_seed=SEED, custom_theme_spec=custom)
    app = App(theme_seed=SEED, dark=True, custom_theme_spec=custom)
    assert view.theme.shape("card") == app.theme.shape("card") == 7.0
    assert app.theme.dark is True and app.theme.role("primary") == tokens.color_scheme(SEED, True)["primary"]
