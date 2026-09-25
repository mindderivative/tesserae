from helpers import elevation, view_from
"""Real coverage for the `icon_button`/`fab`/`extended_fab` component
fragment families (`src/tesserae/spec/components/`). Same cross-check
strategy as `test_spec_expand.py`'s own `Button` test: expand a real
`component:` usage, construct via `tre.View(source=...)`, and compare
against `tesserae.widgets`'s own imperative output for the identical
widget/variant.
"""

from tre import Window

from tesserae.spec import expand_components
from tesserae.widgets import extended_fab, fab, icon_button

ICON_BUTTON_VARIANTS = [
    ("IconButtonFilled", "filled"),
    ("IconButtonFilledTonal", "filled_tonal"),
    ("IconButtonOutlined", "outlined"),
    ("IconButtonStandard", "standard"),
]

FAB_VARIANTS = [
    ("FabSurface", "surface"),
    ("FabPrimary", "primary"),
    ("FabSecondary", "secondary"),
    ("FabTertiary", "tertiary"),
]

EXTENDED_FAB_VARIANTS = [
    ("ExtendedFabSurface", "surface"),
    ("ExtendedFabPrimary", "primary"),
    ("ExtendedFabSecondary", "secondary"),
    ("ExtendedFabTertiary", "tertiary"),
]

THEME_SEED = (0x67, 0x50, 0xA4, 0xFF)


def _themed_window(width=300, height=300):
    window = Window(width=width, height=height)
    window.set_theme(THEME_SEED)
    return window


def test_all_icon_button_variants_match_the_imperative_catalog():
    for component_name, variant in ICON_BUTTON_VARIANTS:
        yaml_text = f"""
id: root
kind: Container
style: {{width: 200, height: 200}}
children:
  - id: b
    component: {component_name}
    with: {{icon: settings, size: 40, corner_radius: 20}}
"""
        expanded = expand_components(yaml_text)
        view = view_from(expanded, theme_seed=THEME_SEED)
        declarative = view.node("b")

        window = _themed_window(200, 200)
        imperative = icon_button(window, "settings", size=40, variant=variant)

        assert declarative.get("corner_radius") == imperative.get("corner_radius"), component_name
        assert declarative.get("border_width") == imperative.get("border_width"), component_name


def test_all_fab_variants_match_the_imperative_catalog():
    for component_name, variant in FAB_VARIANTS:
        yaml_text = f"""
id: root
kind: Container
style: {{width: 200, height: 200}}
children:
  - id: b
    component: {component_name}
    with: {{icon: add, size: 56, corner_radius: 16}}
"""
        expanded = expand_components(yaml_text)
        view = view_from(expanded, theme_seed=THEME_SEED)
        declarative = view.node("b")

        window = _themed_window(200, 200)
        imperative = fab(window, "add", size="default", variant=variant)

        assert declarative.get("corner_radius") == imperative.get("corner_radius"), component_name
        assert elevation(declarative) == elevation(imperative), component_name


def test_all_extended_fab_variants_match_the_imperative_catalog():
    for component_name, variant in EXTENDED_FAB_VARIANTS:
        yaml_text = f"""
id: root
kind: Container
style: {{width: 300, height: 100}}
children:
  - id: b
    component: {component_name}
    with: {{label: Compose, icon: add, width: 160}}
"""
        expanded = expand_components(yaml_text)
        view = view_from(expanded, theme_seed=THEME_SEED)
        declarative = view.node("b")

        window = _themed_window(300, 100)
        imperative = extended_fab(window, "Compose", 160, icon="add", variant=variant)

        assert declarative.get("corner_radius") == imperative.get("corner_radius"), component_name
        assert elevation(declarative) == elevation(imperative), component_name
