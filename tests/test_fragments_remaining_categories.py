"""Real coverage for the last 4 widget categories' component fragments:
`SearchBar`/`SearchView` (Search), `Image` (Media & Graphics -- the
only buildable one; `video`/`node_graph`/`graph_node` all confirmed
blocked, no declarative kind), `DatePickerDay` (4 real states)/
`PeriodSelectorAM`/`PeriodSelectorPM` (Date & Time). Progress & Status
has zero fragments -- `CircularProgress`/`LinearProgress`/
`LoadingIndicator` all confirmed blocked, no declarative `NodeKindSpec`
equivalent for any of the 3 (verified directly, matching `tre`'s own
M74 scope note).
"""

from pathlib import Path

import pytest
from tre import View, Window

from tesserae.spec import expand_components
from tesserae.widgets import date_picker_day, period_selector, search_bar, search_view

FIXTURES_VIEW_PATH = str(Path(__file__).parent / "View.yaml")

THEME_SEED = (0x67, 0x50, 0xA4, 0xFF)


def _themed_window(width=400, height=300):
    window = Window(width=width, height=height)
    window.set_theme(THEME_SEED)
    return window


def test_search_bar_matches_the_imperative_catalog():
    yaml_text = """
id: root
kind: Container
style: {width: 400, height: 300}
children:
  - id: sb
    component: SearchBar
    with: {placeholder: "Search...", width: 360, corner_radius: 28}
"""
    expanded = expand_components(yaml_text)
    view = View("T.yaml", source=expanded, theme_seed=THEME_SEED)
    declarative = view.node("sb")
    assert view.node("sb.field") is not None

    imperative, imp_field, imp_leading, imp_trailing = search_bar(
        _themed_window(), "Search...", 360
    )

    assert declarative.get("corner_radius") == imperative.get("corner_radius")
    assert declarative.get("elevation") == imperative.get("elevation")


def test_search_view_matches_the_imperative_catalog():
    yaml_text = """
id: root
kind: Container
style: {width: 400, height: 300}
children:
  - id: sv
    component: SearchView
    with: {width: 360, height: 200}
"""
    expanded = expand_components(yaml_text)
    view = View("T.yaml", source=expanded, theme_seed=THEME_SEED)
    declarative = view.node("sv")

    imperative = search_view(_themed_window(), 360, 200)

    assert declarative.get("corner_radius") == imperative.get("corner_radius")
    assert declarative.get("elevation") == imperative.get("elevation")


def test_image_constructs_from_a_real_file():
    # `src:` resolves relative to the calling view's own directory (a
    # real finding documented in Image_Component.yaml's own header),
    # so `path=` is pointed at this tests/ directory -- where the real
    # `fixtures/pixel.png` fixture already lives -- while `source=`
    # supplies the already-expanded YAML text directly.
    yaml_text = """
id: root
kind: Container
style: {width: 200, height: 200}
children:
  - id: img
    component: Image
    with: {src: fixtures/pixel.png, width: 100, height: 100, fit: Cover}
"""
    expanded = expand_components(yaml_text)
    view = View(FIXTURES_VIEW_PATH, source=expanded)
    assert view.node("img") is not None


DATE_PICKER_DAY_CASES = [
    ("DatePickerDaySelected", dict(selected=True, today=False, outside_month=False)),
    ("DatePickerDayToday", dict(selected=False, today=True, outside_month=False)),
    ("DatePickerDayOutsideMonth", dict(selected=False, today=False, outside_month=True)),
    ("DatePickerDay", dict(selected=False, today=False, outside_month=False)),
]


def test_all_date_picker_day_states_match_the_imperative_catalog():
    for component_name, kwargs in DATE_PICKER_DAY_CASES:
        yaml_text = f"""
id: root
kind: Container
style: {{width: 200, height: 200}}
children:
  - id: d
    component: {component_name}
    with: {{day: "15"}}
"""
        expanded = expand_components(yaml_text)
        view = View("T.yaml", source=expanded, theme_seed=THEME_SEED)
        declarative = view.node("d")

        imperative = date_picker_day(_themed_window(), 15, **kwargs)

        assert declarative.get("corner_radius") == imperative.get("corner_radius"), component_name
        assert declarative.get("border_width") == imperative.get("border_width"), component_name


def test_date_picker_day_requires_a_quoted_string_day():
    # Real, confirmed requirement (see the fragments' own header
    # comments): `day` must be a string -- `TextSpec.content` is
    # `String`-typed, and whole-value substitution preserves the
    # supplied Python type verbatim. `expand_components` itself is a
    # pure string-substitution pass with no schema validation -- the
    # real error only surfaces once `tre.View` parses the result.
    yaml_text = """
id: root
kind: Container
children:
  - id: d
    component: DatePickerDaySelected
    with: {day: 15}
"""
    expanded = expand_components(yaml_text)
    with pytest.raises(ValueError, match="expected a string"):
        View("T.yaml", source=expanded)


def test_period_selector_am_and_pm_match_the_imperative_catalog():
    for component_name in ["PeriodSelectorAM", "PeriodSelectorPM"]:
        yaml_text = f"""
id: root
kind: Container
style: {{width: 200, height: 200}}
children:
  - id: ps
    component: {component_name}
"""
        expanded = expand_components(yaml_text)
        view = View("T.yaml", source=expanded, theme_seed=THEME_SEED)
        am = view.node("ps.am")
        pm = view.node("ps.pm")

        imperative_am, imperative_pm = period_selector(_themed_window(), selected="AM")

        assert am.get("corner_radius") == imperative_am.get("corner_radius"), component_name
        assert pm.get("corner_radius") == imperative_pm.get("corner_radius"), component_name
