from helpers import elevation, view_from
"""Real coverage for the Progress & Status component fragments --
`CircularProgress`/`LinearProgress`/`LoadingIndicator`. All 3 were
blocked until `tre`'s own M84 added declarative `NodeKindSpec` support
for them (this repo's own M27) -- see `BUILD_TRACKER.md`.

`Node.get()` only exposes a small numeric whitelist (`engine-py::
node.rs`, confirmed directly) -- `value` is readable for both progress
indicators, but no color/tint field is readable from Python for any of
these 3 at all; `tre`'s own `engine-spec` unit tests already cover
tint resolution directly at the Rust level.
"""

from tre import Node, Window

from tesserae.spec import expand_components
from tesserae.widgets import circular_progress, linear_progress, loading_indicator

THEME_SEED = (0x67, 0x50, 0xA4, 0xFF)


def test_circular_progress_matches_the_imperative_catalog():
    yaml_text = """
id: root
kind: Container
style: {width: 100, height: 100}
children:
  - id: spinner
    component: CircularProgress
    with: {size: 48, value: 0.4}
"""
    expanded = expand_components(yaml_text)
    view = view_from(expanded, theme_seed=THEME_SEED)
    declarative = view.node("spinner")

    window = Window(width=100, height=100)
    window.set_theme(THEME_SEED)
    imperative = circular_progress(window, size=48, value=0.4)

    assert declarative.get("value") == imperative.node.get("value") == 0.4
    assert view.control("spinner").value.get() == imperative.value.get() == 0.4


def test_linear_progress_matches_the_imperative_catalog():
    yaml_text = """
id: root
kind: Container
style: {width: 200, height: 50}
children:
  - id: bar
    component: LinearProgress
    with: {width: 200, height: 4, value: 0.75}
"""
    expanded = expand_components(yaml_text)
    view = view_from(expanded, theme_seed=THEME_SEED)
    declarative = view.node("bar")

    window = Window(width=200, height=50)
    window.set_theme(THEME_SEED)
    imperative = linear_progress(window, width=200, height=4, value=0.75)

    assert declarative.get("value") == imperative.node.get("value") == 0.75
    assert view.control("bar").value.get() == imperative.value.get() == 0.75


def test_loading_indicator_builds_with_a_real_role_name_background():
    yaml_text = """
id: root
kind: Container
style: {width: 100, height: 100}
children:
  - id: spinner
    component: LoadingIndicator
    with: {size: 48, background: primary}
"""
    expanded = expand_components(yaml_text)
    view = view_from(expanded, theme_seed=THEME_SEED)
    node = view.node("spinner")
    assert isinstance(node, Node)


def test_loading_indicator_with_no_theme_still_builds_via_a_literal_color():
    yaml_text = """
id: root
kind: Container
children:
  - id: spinner
    component: LoadingIndicator
    with: {size: 48, background: "#6750A4FF"}
"""
    expanded = expand_components(yaml_text)
    view = view_from(expanded)
    node = view.node("spinner")
    assert isinstance(node, Node)
