"""Real coverage for `tesserae.spec.load_view` -- the integration point
between `expand_components` and a real `tre.View`, reading from an
actual file on disk (not just a YAML string in memory, unlike
`test_spec_expand.py`).
"""

from pathlib import Path

import pytest

from tesserae.spec import load_view

BUTTON_VIEW_YAML = """
id: root
kind: Container
style: {width: 300, height: 200}
children:
  - id: save_button
    component: Button
    with: {label: Save, width: 120, height: 40, corner_radius: 20}
"""

PLAIN_VIEW_YAML = """
id: root
kind: Rect
style: {width: 100, height: 50, background: "#6750A4"}
"""


def test_load_view_expands_component_usage_from_a_real_file(tmp_path: Path):
    view_path = tmp_path / "Save_View.yaml"
    view_path.write_text(BUTTON_VIEW_YAML)

    view = load_view(view_path, theme_seed=(0x67, 0x50, 0xA4, 0xFF))
    node = view.node("save_button")
    assert node.get("corner_radius") == 20.0

    label = view.node("save_button.label")
    assert label is not None


def test_load_view_is_a_true_no_op_passthrough_with_zero_component_usage(tmp_path: Path):
    view_path = tmp_path / "Plain_View.yaml"
    view_path.write_text(PLAIN_VIEW_YAML)

    view = load_view(view_path)
    node = view.node("root")
    assert node is not None


def test_load_view_forwards_theme_kwargs_to_tre_view(tmp_path: Path):
    view_path = tmp_path / "Save_View.yaml"
    view_path.write_text(BUTTON_VIEW_YAML)

    # No theme_seed given -- style: {background: primary} should fail to
    # resolve, proving the kwarg genuinely reaches tre.View rather than
    # being silently dropped.
    with pytest.raises(ValueError, match="unknown color identifier"):
        load_view(view_path)
