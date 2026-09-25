"""Real coverage for the Overlays component fragments: `Dialog`,
`Snackbar`, `SideSheetModal`/`SideSheetStandard`, `MenuItem`,
`Tooltip`. `menu` (the dynamic list of `MenuItem`s `build_menu` wraps)
has no fragment -- a real, variable-length list, the same structural
limit already named for `tabs`/`navigation_rail`/etc.
"""

import pytest

from helpers import elevation, view_from
from tre import Window

from tesserae.spec import expand_components
from tesserae.widgets import dialog, menu_item, side_sheet, snackbar, tooltip

THEME_SEED = (0x67, 0x50, 0xA4, 0xFF)


def _themed_window(width=400, height=300):
    window = Window(width=width, height=height)
    window.set_theme(THEME_SEED)
    return window


def test_dialog_matches_the_imperative_catalog():
    yaml_text = """
id: root
kind: Container
style: {width: 400, height: 300}
children:
  - id: d
    component: Dialog
    with: {headline: 'Delete?', text: 'Cannot be undone.', width: 300, height: 150, scrim_width: 400, scrim_height: 300}
"""
    expanded = expand_components(yaml_text)
    view = view_from(expanded, theme_seed=THEME_SEED)
    scrim = view.node("d")
    panel = view.node("d.panel")
    assert view.node("d.headline") is not None
    assert view.node("d.body") is not None

    imperative = dialog(_themed_window(), "Delete?", "Cannot be undone.", 300, 150)

    assert scrim.get("corner_radius") == imperative.get("corner_radius")
    assert panel.get("corner_radius") == 28.0
    assert elevation(panel) == 3.0
    _assert_scrim_matches(scrim, panel, imperative)


def _assert_scrim_matches(scrim, panel, imperative_scrim):
    """M33 (`tre` 0.3.4): `opacity` is group opacity, so the scrim's 32%
    lives in its color and nothing in the overlay sets `opacity` -- an
    `opacity: 0.32` scrim would fade its child panel too. Matches
    `tre`'s own scrim exactly, `(0, 0, 0, 82)`."""
    assert scrim.get("fill") == imperative_scrim.get("fill") == (0, 0, 0, 82)
    assert scrim.get("opacity") == imperative_scrim.get("opacity") == 1.0
    assert panel.get("opacity") == 1.0


def test_snackbar_matches_the_imperative_catalog():
    yaml_text = """
id: root
kind: Container
style: {width: 300, height: 100}
children:
  - id: sb
    component: Snackbar
    with: {text: Saved, width: 250}
"""
    expanded = expand_components(yaml_text)
    view = view_from(expanded, theme_seed=THEME_SEED)
    declarative = view.node("sb")

    imperative, imp_action, imp_close = snackbar(_themed_window(), "Saved", 250)

    assert declarative.get("corner_radius") == imperative.get("corner_radius")
    assert elevation(declarative) == elevation(imperative)


def test_side_sheet_modal_and_standard_construct_with_correct_elevation():
    # Real, stated limitation (see the fragments' own header comments):
    # `add_side_sheet`'s own base `corner_radius` is a literal 0.0 (the
    # real visual rounding comes from a per-corner override `Node.get`
    # never reads back), so `corner_radius` is not a meaningful
    # cross-check here, unlike every other fragment in this catalog.
    #
    # Real bug caught while writing this test, not in the fragment
    # itself: `side_sheet(modal=True)` returns the outer *scrim* node
    # (confirmed live), not the inner panel -- its own `elevation`
    # reads 0.0, matching the declarative scrim's root, not the
    # panel's real `elevation: level_1`. The panel's own elevation has
    # no separately-gettable imperative counterpart at all in the
    # modal case, so only the non-modal (`side_sheet(modal=False)`
    # returns the panel directly) case cross-checks `elevation`.
    yaml_text = """
id: root
kind: Container
style: {width: 400, height: 300}
children:
  - id: modal
    component: SideSheetModal
    with: {width: 360, height: 300, scrim_width: 400, scrim_height: 300}
  - id: standard
    component: SideSheetStandard
    with: {width: 360, height: 300}
"""
    expanded = expand_components(yaml_text)
    view = view_from(expanded, theme_seed=THEME_SEED)
    modal_scrim = view.node("modal")
    modal_panel = view.node("modal.panel")
    standard = view.node("standard")

    imperative_modal = side_sheet(_themed_window(), width=360, height=300, modal=True)
    imperative_standard = side_sheet(_themed_window(), width=360, height=300, modal=False)

    _assert_scrim_matches(modal_scrim, modal_panel, imperative_modal)
    assert elevation(modal_panel) == 1.0
    assert elevation(standard) == elevation(imperative_standard) == 0.0


def test_menu_item_matches_the_imperative_catalog():
    yaml_text = """
id: root
kind: Container
style: {width: 300, height: 100}
children:
  - id: mi
    component: MenuItem
    with: {label: Settings, width: 200}
"""
    expanded = expand_components(yaml_text)
    view = view_from(expanded, theme_seed=THEME_SEED)
    declarative = view.node("mi")

    imperative = menu_item(_themed_window(), "Settings", width=200)

    assert declarative.get("corner_radius") == imperative.get("corner_radius")


def test_tooltip_matches_the_imperative_catalog():
    yaml_text = """
id: root
kind: Container
style: {width: 300, height: 100}
children:
  - id: tt
    component: Tooltip
    with: {text: Hint, width: 100}
"""
    expanded = expand_components(yaml_text)
    view = view_from(expanded, theme_seed=THEME_SEED)
    declarative = view.node("tt")

    imperative = tooltip(_themed_window(), "Hint", 100)

    assert declarative.get("corner_radius") == imperative.get("corner_radius")
