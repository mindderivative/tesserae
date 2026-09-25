"""M37 Phase 2: Tesserae's spec compiler (`tesserae.spec.build`) and
cascade (`tesserae.spec.cascade`).

The cascade and the compiler's errors are checked against `tre` 0.3.4's
own builder, a `tre` `View`, on the same spec. Whole-tree comparison of
every fragment and example view is M37 Phase 3's tree differ.
"""

import pytest
import tre

from tesserae import tokens
from tesserae.spec.build import SpecBuildError, build

SEED = (0x67, 0x50, 0xA4, 0xFF)
SCHEME = tokens.color_scheme(SEED)


def _window():
    window = tre.Window(width=400, height=300)
    window.set_theme(SEED)
    return window


def _rect(node_id="r", classes=(), **style):
    return {"id": node_id, "kind": "Rect", "classes": list(classes),
            "style": {"width": 10, "height": 10, "background": "#112233", **style}}


def _both(spec, **sheets):
    """`(tre's View, Tesserae's Built)` for the same spec and sheets."""
    view = tre.View(spec=spec, theme_seed=SEED, **{f"{k}_spec": v for k, v in sheets.items() if v is not None})
    built = build(_window(), spec, scheme=SCHEME, **{k: v for k, v in sheets.items() if v is not None})
    return view, built


def _radius_both(spec, node_id="r", **sheets):
    view, built = _both(spec, **sheets)
    return view.node(node_id).get("corner_radius"), built.nodes[node_id].get("corner_radius")


def _rule(style, **selector):
    return {**selector, "style": style}


CASCADE_CASES = {
    "inline beats every rule": ({"styles": [_rule({"corner_radius": 1}, id="r")]}, {"corner_radius": 9}, ()),
    "id beats classes": ({"styles": [_rule({"corner_radius": 2}, id="r"), _rule({"corner_radius": 3}, classes=["a"])]}, {}, ("a",)),
    "more classes beat fewer": ({"styles": [_rule({"corner_radius": 5}, classes=["a", "b"]), _rule({"corner_radius": 4}, classes=["a"])]}, {}, ("a", "b")),
    "classes beat kind": ({"styles": [_rule({"corner_radius": 6}, classes=["a"]), _rule({"corner_radius": 7}, kind="Rect")]}, {}, ("a",)),
    "kind beats baseline": ({"styles": [_rule({"corner_radius": 8}, kind="Rect"), _rule({"corner_radius": 1})]}, {}, ()),
    "a class rule needs every class": ({"styles": [_rule({"corner_radius": 5}, classes=["a", "b"])]}, {}, ("a",)),
    "same tier: later wins": ({"styles": [_rule({"corner_radius": 2}, kind="Rect"), _rule({"corner_radius": 3}, kind="Rect")]}, {}, ()),
    "a kind rule for another kind": ({"styles": [_rule({"corner_radius": 4}, kind="Container")]}, {}, ()),
    "kind+classes rule applies at the kind tier alone": ({"styles": [_rule({"corner_radius": 4}, kind="Rect", classes=["zz"])]}, {}, ()),
    "id+kind rule applies at the id tier": ({"styles": [_rule({"corner_radius": 5}, kind="Container", id="r")]}, {}, ()),
    "tokens resolve through the cascade": ({"styles": [_rule({"corner_radius": "large"}, kind="Rect")]}, {}, ()),
}


@pytest.mark.parametrize("name", sorted(CASCADE_CASES))
def test_the_cascade_matches_tres(name):
    sheet, inline, classes = CASCADE_CASES[name]
    theirs, ours = _radius_both(_rect(classes=classes, **inline), stylesheet=sheet)
    assert ours == theirs


def test_layers_stack_default_then_custom_then_stylesheet():
    for default, custom, sheet in [
        ({"styles": [_rule({"corner_radius": 1})]}, {"styles": [_rule({"corner_radius": 2})]}, {"styles": [_rule({"corner_radius": 3})]}),
        ({"styles": [_rule({"corner_radius": 1}, id="r")]}, {"styles": [_rule({"corner_radius": 2})]}, None),
        ({"styles": [_rule({"corner_radius": 1}, kind="Rect")]}, None, {"styles": [_rule({"elevation": 2})]}),
    ]:
        theirs, ours = _radius_both(_rect(), default_theme=default, custom_theme=custom, stylesheet=sheet)
        assert ours == theirs


def test_the_shipped_default_theme_applies_when_none_is_given():
    """`tre`'s default theme gives a Checkbox corner radius 2 -- Tesserae's
    copy of it does too."""
    spec = {"id": "c", "kind": "Container", "children": [_rect()]}
    view, built = _both(spec)
    assert built.nodes["r"].get("corner_radius") == view.node("r").get("corner_radius") == 0.0


def test_fills_resolve_theme_roles_and_colours_as_tre_does():
    spec = {"id": "c", "kind": "Container", "style": {"background": "surface"}, "children": [
        _rect("a", background="primary"), _rect("b", background="#80FF0000"),
        {"id": "t", "kind": "Text", "text": {"content": "x", "font_family": "Roboto", "font_size": 14},
         "style": {"foreground": "on_surface", "width": 10, "height": 10}},
    ]}
    view, built = _both(spec)
    tre.Window.from_view(view, width=10, height=10, title="t")
    for node_id in ("c", "a", "b", "t"):
        assert built.nodes[node_id].get("fill") == view.node(node_id).get("fill"), node_id


def test_elevation_becomes_shadows_and_opacity_carries_over():
    built = build(_window(), _rect(elevation="level_3", opacity=0.5), scheme=SCHEME)
    assert built.nodes["r"].get("shadows") == tokens.elevation_shadows(3)
    assert built.nodes["r"].get("opacity") == 0.5


def test_text_takes_its_type_role_and_explicit_fields_win():
    spec = {"id": "t", "kind": "Text", "text": {"content": "Hi", "typography_role": "title_medium", "font_size": 20},
            "style": {"foreground": "#000000"}}
    node = build(_window(), spec, scheme=SCHEME).nodes["t"]
    assert (node.get("text"), node.get("font_family"), node.get("font_weight"), node.get("font_size")) == ("Hi", "Roboto", 500.0, 20.0)


def test_icons_are_paths_from_tesseraes_icon_set():
    from tesserae.icons import ICON_VIEW_BOX, icon_path

    spec = {"id": "i", "kind": "Icon", "icon": {"name": "check"}, "style": {"width": 24, "height": 24, "foreground": "primary"}}
    window = _window()
    node = build(window, spec, scheme=SCHEME).nodes["i"]
    # tre reads path data back normalised (absolute commands), so compare with its own reading
    assert node.get("data") == window.create("path", data=icon_path("check")).get("data")
    assert node.get("view_box") == ICON_VIEW_BOX and node.get("fill") == SCHEME["primary"]


def test_a_text_field_is_a_box_around_a_text_input():
    spec = {"id": "f", "kind": "TextField", "text": {"content": "bob", "font_family": "Roboto", "font_size": 14},
            "style": {"width": 200, "height": 40, "background": "surface"}}
    built = build(_window(), spec, scheme=SCHEME)
    assert built.nodes["f"].get("text") == "bob" and built.nodes["f"].get("role") == "textbox"
    assert built.outer["f"].get("fill") == SCHEME["surface"] and built.nodes["f"].parent() is not None


def test_images_take_decoded_pixels_and_fit():
    spec = {"id": "img", "kind": "Image", "image": {"fit": "contain"}, "style": {"width": 20, "height": 10}}
    rgba = bytes([255, 0, 0, 255] * 4)
    node = build(_window(), spec, scheme=SCHEME, frames={"img": (rgba, 2, 2)}).nodes["img"]
    assert (node.get("pixel_width"), node.get("pixel_height"), node.get("fit")) == (2, 2, "contain")


@pytest.mark.parametrize("kind, fields", [
    ("Checkbox", {"checked": True, "style": {"width": 18, "height": 18, "background": "primary"}}),
    ("Switch", {"selected": True, "style": {"width": 52, "height": 32}}),
    ("RadioButton", {"selected": True, "style": {"width": 20, "height": 20}}),
    ("Slider", {"value": 0.3, "style": {"width": 200, "height": 40, "background": "primary"}}),
    ("CircularProgress", {"value": 0.5, "style": {"width": 48, "height": 48}}),
    ("LinearProgress", {"value": 0.5, "style": {"width": 200, "height": 4}}),
    ("LoadingIndicator", {"style": {"width": 48, "height": 48, "foreground": "primary"}}),
    ("TimePickerDial", {"hour": 3, "minute": 30, "style": {"width": 256, "height": 256}}),
])
def test_the_md3_kinds_build_with_their_state_until_m40(kind, fields):
    spec = {"id": "root", "kind": "Container", "children": [{"id": "w", "kind": kind, **fields}]}
    window = _window()
    built = build(window, spec, scheme=SCHEME)
    node = built.nodes["w"]
    assert node.parent() is not None  # moved into the tree, off the window's root
    window.root.add_child(built.root)
    window.advance(16)
    assert node.get("layout_width") == fields["style"]["width"]
    if kind == "Checkbox":
        assert node.get_checked() is True
    elif kind in ("Switch", "RadioButton"):
        assert node.get_selected() is True
    elif kind in ("Slider", "CircularProgress", "LinearProgress"):
        assert node.get("value") == pytest.approx(fields["value"])


ERROR_CASES = {
    "Rect without background": {"id": "x", "kind": "Rect", "style": {"width": 1}},
    "Text without foreground": {"id": "x", "kind": "Text", "text": {"content": "a", "font_family": "Roboto", "font_size": 1}, "style": {}},
    "Text with background": {"id": "x", "kind": "Text", "text": {"content": "a", "font_family": "Roboto", "font_size": 1}, "style": {"background": "#000000", "foreground": "#000000"}},
    "Text without text": {"id": "x", "kind": "Text", "style": {"foreground": "#000000"}},
    "Text without a font": {"id": "x", "kind": "Text", "text": {"content": "a", "font_size": 1}, "style": {"foreground": "#000000"}},
    "Text without a size": {"id": "x", "kind": "Text", "text": {"content": "a", "font_family": "Roboto"}, "style": {"foreground": "#000000"}},
    "unknown typography role": {"id": "x", "kind": "Text", "text": {"content": "a", "typography_role": "huge"}, "style": {"foreground": "#000000"}},
    "unknown shape token": {"id": "x", "kind": "Rect", "style": {"background": "#000000", "corner_radius": "full"}},
    "unknown elevation token": {"id": "x", "kind": "Rect", "style": {"background": "#000000", "elevation": "level_9"}},
    "unknown icon": {"id": "x", "kind": "Icon", "icon": {"name": "nope"}, "style": {"foreground": "#000000"}},
    "Checkbox with selected": {"id": "x", "kind": "Checkbox", "selected": True, "style": {"background": "#000000"}},
    "Switch with checked": {"id": "x", "kind": "Switch", "checked": True, "style": {}},
    "LoadingIndicator without width": {"id": "x", "kind": "LoadingIndicator", "style": {"foreground": "#000000", "height": 4}},
}


@pytest.mark.parametrize("name", sorted(ERROR_CASES))
def test_errors_read_as_tres_do(name):
    spec = ERROR_CASES[name]
    with pytest.raises(ValueError) as theirs:
        tre.View(spec=spec, theme_seed=SEED)
    with pytest.raises(SpecBuildError) as ours:
        build(_window(), spec, scheme=SCHEME)
    assert str(ours.value) == str(theirs.value)


def test_a_bad_colour_names_the_widget_and_field_as_tre_does():
    spec = {"id": "x", "kind": "Rect", "style": {"background": "notacolor"}}
    with pytest.raises(ValueError) as theirs:
        tre.View(spec=spec, theme_seed=SEED)
    with pytest.raises(SpecBuildError) as ours:
        build(_window(), spec, scheme=SCHEME)
    prefix = 'widget "x": invalid style.background "notacolor": '
    assert str(theirs.value).startswith(prefix) and str(ours.value).startswith(prefix)


def test_a_background_from_a_stylesheet_rule_doesnt_break_text():
    """`tre`'s "not a fill" check reads only the node's own inline
    `style:`, so a baseline rule giving every widget a background still
    lets a Text build."""
    spec = {"id": "c", "kind": "Container", "children": [
        {"id": "t", "kind": "Text", "text": {"content": "x", "font_family": "Roboto", "font_size": 14},
         "style": {"foreground": "#000000", "width": 10, "height": 10}}]}
    sheet = {"styles": [_rule({"background": "surface"})]}
    view, built = _both(spec, stylesheet=sheet)
    tre.Window.from_view(view, width=10, height=10, title="t")
    assert built.nodes["t"].get("fill") == view.node("t").get("fill") == (0, 0, 0, 255)


def test_text_content_must_be_a_string_as_in_tre():
    spec = {"id": "x", "kind": "Text", "text": {"content": 5, "font_family": "Roboto", "font_size": 14},
            "style": {"foreground": "#000000"}}
    with pytest.raises(ValueError):
        tre.View(spec=spec, theme_seed=SEED)
    with pytest.raises(SpecBuildError, match="text.content must be a string, got int 5"):
        build(_window(), spec, scheme=SCHEME)
