from helpers import elevation, view_from
"""Real coverage for the Navigation & Shell component fragments that
are fixed-shape (not dynamic lists): `ToolbarDocked`/`ToolbarFloating`,
`TopAppBar`, `StatusBar`. `tabs`/`navigation_rail`/`navigation_drawer`
have no fragment at all -- each takes a genuinely variable-length list
of entries, a real structural limit this macro layer's current design
(no loop/repeat construct) can't express (the same real limitation
already named for `button_group`/`list_`/`menu`).
"""

from tre import Window

from tesserae.spec import expand_components
from tesserae.widgets import status_bar, toolbar, top_app_bar

THEME_SEED = (0x67, 0x50, 0xA4, 0xFF)


def _themed_window(width=300, height=200):
    window = Window(width=width, height=height)
    window.set_theme(THEME_SEED)
    return window


def test_toolbar_docked_matches_the_imperative_catalog():
    yaml_text = """
id: root
kind: Container
style: {width: 300, height: 200}
children:
  - id: t
    component: ToolbarDocked
    with: {background: surface_container, width: 280}
"""
    expanded = expand_components(yaml_text)
    view = view_from(expanded, theme_seed=THEME_SEED)
    declarative = view.node("t")

    imperative = toolbar(_themed_window(), variant="docked", vibrant=False, width=280).node  # a Widget since M41

    assert declarative.get("corner_radius") == imperative.get("corner_radius")
    assert elevation(declarative) == elevation(imperative)


def test_toolbar_floating_matches_the_imperative_catalog():
    yaml_text = """
id: root
kind: Container
style: {width: 300, height: 200}
children:
  - id: t
    component: ToolbarFloating
    with: {background: primary_container, width: 200, corner_radius: 32}
"""
    expanded = expand_components(yaml_text)
    view = view_from(expanded, theme_seed=THEME_SEED)
    declarative = view.node("t")

    imperative = toolbar(
        _themed_window(), variant="floating", vibrant=True, width=200, height=64
    ).node  # a Widget since M41

    assert declarative.get("corner_radius") == imperative.get("corner_radius")
    assert elevation(declarative) == elevation(imperative)


def test_top_app_bar_matches_the_imperative_catalog():
    yaml_text = """
id: root
kind: Container
style: {width: 300, height: 200}
children:
  - id: tab
    component: TopAppBar
    with: {title: Home, width: 300}
"""
    expanded = expand_components(yaml_text)
    view = view_from(expanded, theme_seed=THEME_SEED)
    declarative = view.node("tab")
    assert view.node("tab.title") is not None

    imperative = top_app_bar(_themed_window(), "Home", width=300).node  # a Widget since M41
    assert declarative.get("corner_radius") == imperative.get("corner_radius")


def test_status_bar_matches_the_imperative_catalog():
    yaml_text = """
id: root
kind: Container
style: {width: 300, height: 200}
children:
  - id: sb
    component: StatusBar
    with: {text: Ready, width: 300}
"""
    expanded = expand_components(yaml_text)
    view = view_from(expanded, theme_seed=THEME_SEED)
    declarative = view.node("sb")
    assert view.node("sb.text") is not None

    imperative = status_bar(_themed_window(), "Ready", width=300).node  # a Widget since M41
    assert declarative.get("corner_radius") == imperative.get("corner_radius")
