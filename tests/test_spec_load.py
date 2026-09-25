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
    component: ButtonFilled
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


# M29 Phase 1: `load_view` hands `tre` a dict via `spec=`, and resolves
# `include:` itself, since `tre` only splices `include:` on its YAML-text
# path.

import re

from tesserae.spec import ComponentError, expand_components_to_spec

RECT = 'id: {id}\nkind: Rect\nstyle: {{width: 10, height: 10, background: "#112233"}}\n'


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def test_load_view_resolves_include_relative_to_the_view_file(tmp_path: Path):
    _write(tmp_path / "parts" / "header.yaml", RECT.format(id="header"))
    view_path = _write(
        tmp_path / "Main_View.yaml",
        "id: root\nkind: Container\nchildren:\n  - include: parts/header.yaml\n",
    )
    view = load_view(view_path)
    assert view.node("header") is not None


def test_nested_include_resolves_against_the_including_files_own_directory(tmp_path: Path):
    # `parts/header.yaml` says `include: inner.yaml` -- that's
    # `parts/inner.yaml`, not `<view dir>/inner.yaml`, exactly as in tre.
    _write(tmp_path / "parts" / "inner.yaml", RECT.format(id="inner"))
    _write(
        tmp_path / "parts" / "header.yaml",
        "id: header\nkind: Container\nchildren:\n  - include: inner.yaml\n",
    )
    view_path = _write(
        tmp_path / "Main_View.yaml",
        "id: root\nkind: Container\nchildren:\n  - include: parts/header.yaml\n",
    )
    view = load_view(view_path)
    assert view.node("inner") is not None


def test_an_included_file_can_use_component(tmp_path: Path):
    # New capability: includes resolve *before* component expansion, so
    # an included file's own `component:` usage expands too. Under tre's
    # own text-path include, it reached tre unexpanded and failed.
    _write(tmp_path / "parts" / "actions.yaml", BUTTON_VIEW_YAML)
    view_path = _write(
        tmp_path / "Main_View.yaml",
        "id: page\nkind: Container\nchildren:\n  - include: parts/actions.yaml\n",
    )
    view = load_view(view_path, theme_seed=(0x67, 0x50, 0xA4, 0xFF))
    assert view.node("save_button.label") is not None


def test_include_cycle_is_rejected(tmp_path: Path):
    _write(tmp_path / "a.yaml", "id: a\nkind: Container\nchildren:\n  - include: b.yaml\n")
    _write(tmp_path / "b.yaml", "id: b\nkind: Container\nchildren:\n  - include: a.yaml\n")
    view_path = _write(tmp_path / "Main_View.yaml", "include: a.yaml\n")
    with pytest.raises(ComponentError, match="cycle"):
        load_view(view_path)


def test_include_deeper_than_the_limit_is_rejected(tmp_path: Path):
    for i in range(10):
        _write(tmp_path / f"f{i}.yaml", f"include: f{i + 1}.yaml\n")
    _write(tmp_path / "f10.yaml", RECT.format(id="leaf"))
    view_path = _write(tmp_path / "Main_View.yaml", "include: f0.yaml\n")
    with pytest.raises(ComponentError, match="nested more than 8 deep"):
        load_view(view_path)


def test_include_escaping_the_base_directory_is_rejected(tmp_path: Path):
    _write(tmp_path / "outside.yaml", RECT.format(id="outside"))
    view_path = _write(
        tmp_path / "app" / "Main_View.yaml",
        "id: root\nkind: Container\nchildren:\n  - include: ../outside.yaml\n",
    )
    with pytest.raises(ComponentError, match="escapes its base directory"):
        load_view(view_path)


def test_absolute_include_is_rejected(tmp_path: Path):
    target = _write(tmp_path / "abs.yaml", RECT.format(id="abs"))
    view_path = _write(
        tmp_path / "Main_View.yaml",
        f"id: root\nkind: Container\nchildren:\n  - include: {target}\n",
    )
    with pytest.raises(ComponentError, match="must be a relative path"):
        load_view(view_path)


def test_include_must_be_the_nodes_only_key(tmp_path: Path):
    _write(tmp_path / "part.yaml", RECT.format(id="part"))
    view_path = _write(
        tmp_path / "Main_View.yaml",
        "id: root\nkind: Container\nchildren:\n  - {include: part.yaml, id: extra}\n",
    )
    with pytest.raises(ComponentError, match=r"only key; also got \['id'\]"):
        load_view(view_path)


def test_include_with_no_base_directory_is_rejected():
    with pytest.raises(ComponentError, match="no base directory"):
        expand_components_to_spec("include: part.yaml\n")


def test_include_inside_a_component_fragment_is_rejected(tmp_path: Path):
    frags = tmp_path / "frags"
    _write(frags / "Boxed_Component.yaml", "id: root\nkind: Container\nchildren:\n  - include: x.yaml\n")
    view_path = _write(
        tmp_path / "Main_View.yaml",
        "id: root\nkind: Container\nchildren:\n  - {id: box, component: Boxed}\n",
    )
    with pytest.raises(ComponentError, match="not supported inside a component fragment"):
        load_view(view_path, component_dirs=[frags])


def test_an_unquoted_date_still_loads_as_its_string(tmp_path: Path):
    # PyYAML reads an unquoted 2026-09-24 as a `datetime.date`, which
    # `spec=` can't put in a string field. The old text round-trip turned
    # it back into "2026-09-24"; the dict path must do the same.
    view_path = _write(
        tmp_path / "Date_View.yaml",
        "id: root\nkind: Text\nstyle: {width: 100, height: 20, background: \"#000000\"}\n"
        "text: {content: 2026-09-24, font_family: Roboto, font_size: 16}\n",
    )
    view = load_view(view_path)
    assert view.node("root").get_text() == "2026-09-24"


def test_load_view_names_the_source_file_when_tre_rejects_the_spec(tmp_path: Path):
    view_path = _write(tmp_path / "Bad_View.yaml", "id: root\nkind: NotARealKind\n")
    with pytest.raises(ValueError, match=rf"^{re.escape(str(view_path))}: .*NotARealKind"):
        load_view(view_path)


def test_expand_components_to_spec_returns_the_same_tree_as_the_text_form():
    from tesserae.spec import expand_components
    import yaml

    spec = expand_components_to_spec(BUTTON_VIEW_YAML)
    assert isinstance(spec, dict)
    assert spec == yaml.safe_load(expand_components(BUTTON_VIEW_YAML))
    assert spec["children"][0]["id"] == "save_button"
