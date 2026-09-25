from helpers import elevation, view_from
"""Real coverage for the `split_button` component fragment family
(`src/tesserae/spec/components/SplitButton*_Component.yaml`) -- all 5
real MD3 variants, rest-state only (the real hover/press inner-corner
shape-tightening animation has no public Python API, a stated scope
boundary named in each fragment's own header comment).
"""

from tre import Window

from tesserae.spec import expand_components
from tesserae.widgets import split_button

SPLIT_BUTTON_VARIANTS = [
    ("SplitButtonElevated", "elevated"),
    ("SplitButtonFilled", "filled"),
    ("SplitButtonFilledTonal", "filled_tonal"),
    ("SplitButtonOutlined", "outlined"),
    ("SplitButtonText", "text"),
]

THEME_SEED = (0x67, 0x50, 0xA4, 0xFF)


def test_all_split_button_variants_match_the_imperative_catalog():
    for component_name, variant in SPLIT_BUTTON_VARIANTS:
        yaml_text = f"""
id: root
kind: Container
style: {{width: 300, height: 200}}
children:
  - id: b
    component: {component_name}
    with: {{label: Send, width: 100, height: 40, corner_radius: 20}}
"""
        expanded = expand_components(yaml_text)
        view = view_from(expanded, theme_seed=THEME_SEED)
        leading = view.node("b.leading")
        trailing = view.node("b.trailing")

        window = Window(width=300, height=200)
        window.set_theme(THEME_SEED)
        imp_leading, imp_trailing, imp_container = split_button(
            window, "Send", 100, 40, variant=variant
        )

        assert leading.get("corner_radius") == imp_leading.get("corner_radius"), component_name
        assert elevation(leading) == elevation(imp_leading), component_name
        assert leading.get("border_width") == imp_leading.get("border_width"), component_name
        assert trailing.get("corner_radius") == imp_trailing.get("corner_radius"), component_name


def test_split_button_leading_and_trailing_are_separately_addressable_nodes():
    yaml_text = """
id: root
kind: Container
style: {width: 300, height: 200}
children:
  - id: send_split
    component: SplitButtonFilled
    with: {label: Send, width: 100, height: 40, corner_radius: 20}
"""
    expanded = expand_components(yaml_text)
    view = view_from(expanded, theme_seed=THEME_SEED)
    # Real, confirmed behavior: id-namespacing is flat -- every id
    # inside the fragment is prefixed once by the call-site's own id,
    # regardless of nesting depth (matching pyCopper's own real
    # `_namespace_names` precedent) -- not hierarchically nested by
    # each ancestor's own renamed id.
    assert view.node("send_split.leading") is not None
    assert view.node("send_split.trailing") is not None
    assert view.node("send_split.label") is not None
    assert view.node("send_split.chevron") is not None
