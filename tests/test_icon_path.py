"""#216: an `Icon` from SVG path data, with its own view box, beside the named ones."""

import pytest

from tesserae import View
from tesserae.icons import ICON_VIEW_BOX, icon_path
from tesserae.spec.build import SpecBuildError

SEED = (103, 80, 164, 255)
SQUARE = "M2 2H22V22H2Z"


def engine_data(view, data):
    """What tre reads back for `data` (it rewrites path data into its own form)."""
    return view.window.create("path", data=data, view_box=ICON_VIEW_BOX, fill=(0, 0, 0, 255)).get("data")


def icon_view(icon, style=None):
    node = {"id": "i", "kind": "Icon", "icon": icon, "style": {"width": 24, "height": 24, "foreground": "#112233", **(style or {})}}
    return View({"id": "root", "kind": "Container", "style": {"width": 100, "height": 100}, "children": [node]}, theme_seed=SEED)


def test_a_path_is_drawn_in_its_view_box():
    view = icon_view({"path": SQUARE, "view_box": [0, 0, 24, 24]})
    node = view.node("i")
    assert node.get("data") == engine_data(view, SQUARE) != engine_data(view, "M0 0H1V1Z") and tuple(node.get("view_box")) == (0.0, 0.0, 24.0, 24.0)
    assert node.get("fill") == (0x11, 0x22, 0x33, 255)


def test_a_path_without_a_view_box_uses_material_symbols():
    assert tuple(icon_view({"path": SQUARE}).node("i").get("view_box")) == ICON_VIEW_BOX


def test_a_named_icon_is_unchanged():
    view = icon_view({"name": "home"})
    node = view.node("i")
    assert node.get("data") == engine_data(view, icon_path("home")) and tuple(node.get("view_box")) == ICON_VIEW_BOX


@pytest.mark.parametrize("icon, message", [
    ({}, "Icon takes icon .* or path"), ({"name": "home", "path": SQUARE}, "Icon takes icon .* or path"),
    ({"path": ""}, "icon path is SVG path data"), ({"path": 3}, "icon path is SVG path data"),
    ({"path": SQUARE, "view_box": [0, 0, 24]}, "icon view_box is"), ({"path": SQUARE, "view_box": [0, 0, 24, 24, 24]}, "icon view_box is"), ({"path": SQUARE, "view_box": [0, 0, 0, 24]}, "icon view_box is"),
    ({"path": SQUARE, "view_box": [0, 0, 24, True]}, "icon view_box is"), ({"path": SQUARE, "view_box": "0 0 24 24"}, "icon view_box is"),
    ({"name": "nope"}, 'unknown icon "nope"'),
])
def test_a_wrong_icon_names_the_widget(icon, message):
    with pytest.raises(SpecBuildError, match=f'widget "i": {message}'):
        icon_view(icon)


def test_a_bad_path_is_the_engines_message_naming_the_widget():
    with pytest.raises(SpecBuildError, match='widget "i"'):
        icon_view({"path": "not a path", "view_box": [0, 0, 24, 24]})
