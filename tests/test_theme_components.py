"""M57 (#10): a theme's `components:` reach fragments, in views and in
`tesserae.widgets` alike. The expander tags each fragment's root with the
fragment it came from (`component_of`); the cascade gives that root the
corner radius and elevation of its `components:` entry (the variant's,
then the component's), over the fragment's own. A FAB's entry follows its
size (`fab.small`), which its fragments name themselves.
"""

import pytest
import yaml
from helpers import elevation
from tre import Window

from tesserae import Theme, View
from tesserae.spec import expand_components_to_spec
from tesserae.spec.cascade import component_key
from tesserae.widgets import card, fab

SEED = (0x67, 0x50, 0xA4, 0xFF)
CUSTOM = {"components": {"card.elevated": {"corner_radius": 4, "elevation": "level_5"},
                         "dialog": {"corner_radius": "small"},
                         "fab.small": {"corner_radius": 2}}}


@pytest.mark.parametrize("fragment, key", [
    ("CardElevated", ("card", "elevated")), ("CardOutlined", ("card", "outlined")),
    ("ButtonFilledTonal", ("button", "filled_tonal")), ("IconButtonOutlined", ("icon_button", "outlined")),
    ("ChipFilterSelected", ("chip", "filter")), ("ChipAssist", ("chip", "assist")), ("BadgeDot", ("badge", "dot")),
    ("SideSheetModal", ("side_sheet", "modal")), ("SideSheetStandard", ("side_sheet", None)),
    ("ExtendedFabPrimary", ("extended_fab", None)), ("DatePickerDayToday", ("date_picker_day", None)),
    ("ButtonGroup", ("button_group", None)), ("Dialog", ("dialog", None)), ("TopAppBar", ("top_app_bar", None)),
    ("NavigationDrawerItem", ("navigation_drawer_item", None)), ("fab.small", ("fab", "small")),
    ("Card", ("card", None)),  # an app fragment named just the family: no empty variant
])
def test_component_key(fragment, key):
    assert component_key(fragment) == key


def _view(component, with_, **theme):
    spec = expand_components_to_spec(yaml.safe_dump({"id": "w", "component": component, "with": with_}))
    view = View(spec, theme_seed=SEED, **theme)
    view.window.advance(16)
    return view


CARD = ("CardElevated", {"width": 200, "height": 100})


def test_the_expander_tags_a_fragment_root_only():
    spec = expand_components_to_spec(yaml.safe_dump({"id": "w", "component": "Dialog", "with": {
        "headline": "H", "text": "S", "width": 300, "height": 200, "scrim_width": 800, "scrim_height": 600}}))
    assert spec["component_of"] == "Dialog"
    assert all("component_of" not in child for child in spec.get("children") or [])


def test_a_custom_themes_entry_shapes_a_fragment_in_a_view():
    plain, themed = _view(*CARD), _view(*CARD, custom_theme_spec=CUSTOM)
    assert themed.root.get("corner_radius") == 4.0 and elevation(themed.root) == 5
    assert plain.root.get("corner_radius") != 4.0 and elevation(plain.root) != 5  # the default theme's own


def test_the_variant_entry_wins_then_the_component_entry():
    theme = {"components": {"card": {"corner_radius": 20}, "card.elevated": {"corner_radius": 6}}}
    assert _view(*CARD, custom_theme_spec=theme).root.get("corner_radius") == 6.0
    outlined = _view("CardOutlined", {"width": 200, "height": 100}, custom_theme_spec=theme)
    assert outlined.root.get("corner_radius") == 20.0  # no card.outlined entry: card's


def test_a_fab_follows_its_size_entry():
    small = {"icon": "add", "size": 40, "corner_radius": 12, "fab_size": "small"}
    assert _view("FabPrimary", small, custom_theme_spec=CUSTOM).root.get("corner_radius") == 2.0
    default = {"icon": "add", "size": 56, "corner_radius": 16}
    assert _view("FabPrimary", default, custom_theme_spec=CUSTOM).root.get("corner_radius") == 16.0


def test_a_theme_change_reapplies_it():
    view = _view(*CARD)
    view.set_theme(theme_seed=SEED, custom_theme_spec=CUSTOM)
    assert view.root.get("corner_radius") == 4.0 and elevation(view.root) == 5
    view.set_theme(theme_seed=SEED)
    assert view.root.get("corner_radius") != 4.0


def test_a_plain_node_is_untouched():
    view = View({"id": "r", "kind": "Rect", "style": {"width": 10, "height": 10, "corner_radius": 9,
                                                      "background": "#112233"}},
                theme_seed=SEED, custom_theme_spec={"components": {"rect": {"corner_radius": 1}}})
    assert view.root.get("corner_radius") == 9.0


def test_widgets_take_their_themes_entries_and_follow_a_new_theme():
    window = Window(width=400, height=300)
    themed = Theme.resolve(theme_seed=SEED, custom_theme_spec=CUSTOM)
    widget = card(window, 200, 100, variant="elevated", theme=themed)
    assert widget.node.get("corner_radius") == 4.0 and elevation(widget.node) == 5
    widget.set_theme(Theme.resolve(theme_seed=SEED))
    assert widget.node.get("corner_radius") != 4.0
    small = fab(window, "add", size="small", theme=themed)
    assert small.node.get("corner_radius") == 2.0


def test_fab_sizes_keep_md3s_shapes_under_the_default_theme():
    window = Window(width=400, height=300)
    radii = {size: fab(window, "add", size=size).node.get("corner_radius") for size in ("small", "default", "large")}
    assert radii == {"small": 12.0, "default": 16.0, "large": 28.0}
