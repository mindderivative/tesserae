"""#209 phase 5: lowering instances to the builder's spec -- each widget's properties in the shape `tesserae.spec.build` reads."""

import pytest

from tesserae import Signal
from tesserae.spec.compose import Composer
from tesserae.spec.lower import lower
from tesserae.spec.nodes import parse_view


class VM:
    def __init__(self):
        self.label = Signal("hi")
        self.on = Signal(True)


def spec(source, vm=None):
    return lower(Composer({}, vm or VM()).compose(parse_view(source, "T_View.yaml")).root)


def test_text_icon_image_and_svg_take_the_builders_nested_shapes():
    assert spec("widget: Text\ntext: '{{ label }}'\ntypography_role: body_large\nwrap: none\nfont_size: 14") == {
        "id": "root", "kind": "Text", "text": {"content": "hi", "typography_role": "body_large", "wrap": "none", "font_size": 14.0}}
    assert spec("widget: Link\ntext: go\nfont_family: Roboto")["text"] == {"content": "go", "font_family": "Roboto"}
    assert spec("widget: TextInput\ntext: typed\ntypography_role: body_large\nplaceholder: Name\nobscured: true")["text"] == {"content": "typed", "typography_role": "body_large", "placeholder": "Name", "obscured": True}
    assert spec("widget: Icon\nicon: home")["icon"] == {"name": "home"}
    assert spec("widget: Image\nsrc: a.png\nfit: contain")["image"] == {"src": "a.png", "fit": "contain"}
    assert spec("widget: Svg\ncontent: '<svg/>'")["svg"] == {"content": "<svg/>"}
    assert spec("widget: Text")["text"] == {"content": ""}


def test_controls_and_windows_keep_their_properties_flat():
    assert spec("widget: Checkbox\nchecked: '{{ on }}'\ndisabled: true") == {"id": "root", "kind": "Checkbox", "checked": True, "disabled": True}
    assert spec("widget: Slider\nvalue: 0.25")["value"] == 0.25
    node = spec("widget: Window\ntitle: App\nborderless: true\nmin_width: 400\ntitle_bar: {title: App, buttons: [close]}")
    assert node["kind"] == "Window" and node["title"] == "App" and node["borderless"] is True and node["title_bar"] == {"title": "App", "buttons": ["close"]}
    assert spec("widget: DockPanel\ntitle: Files")["title"] == "Files"


def test_the_universal_keys_are_carried_at_their_current_values():
    node = spec("widget: Rect\nstyle: {width: 10, background: '{{ \"#112233\" if on else \"#445566\" }}'}\nclasses: [a, b]\n"
                "a11y: {label: '{{ label }}', role: button}\ninteraction: on_primary\nwindow_region: drag")
    assert node["style"] == {"width": 10, "background": "#112233"} and node["classes"] == ["a", "b"]
    assert node["a11y"] == {"label": "hi", "role": "button"}
    assert node["interaction"] == {"color": "on_primary"} and node["window_region"] == "drag"
    assert spec("widget: Rect\ninteraction: true")["interaction"] is True
    assert "style" not in spec("widget: Rect") and "children" not in spec("widget: Rect")


def test_children_are_lowered_in_order_with_their_ids():
    node = spec("widget: Container\nchildren:\n  - {widget: Text, name: a}\n  - widget: Rect\n  - {widget: Icon, icon: home, name: c}")
    assert [(c["id"], c["kind"]) for c in node["children"]] == [("root.a", "Text"), ("root.children[1]", "Rect"), ("root.c", "Icon")]


def test_values_are_read_at_lowering_so_a_new_lowering_sees_the_change():
    vm = VM()
    comp = Composer({}, vm).compose(parse_view("widget: Text\ntext: '{{ label }}'", "T_View.yaml"))
    assert lower(comp.root)["text"]["content"] == "hi"
    vm.label.set("bye")
    assert lower(comp.root)["text"]["content"] == "bye"


@pytest.mark.parametrize("source, what", [("widget: Image\nframe: x", "a video frame")])
def test_a_property_the_renderer_cannot_draw_is_an_error_naming_it(source, what):
    with pytest.raises(ValueError, match=what):
        spec(source)


def test_flat_properties_of_a_widget_with_a_nested_shape_are_kept():
    assert spec("widget: TextInput\ntext: x\ndisabled: true")["disabled"] is True
    assert spec("widget: Icon\nicon: home") == {"id": "root", "kind": "Icon", "icon": {"name": "home"}}  # a folded property is not repeated flat
