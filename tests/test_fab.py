"""#133 to #140: the Material 3 floating action button and its extended form -- four colours, three sizes, a label, collapsing, lifting."""

import pytest

from tesserae import App, Signal, ViewModel, tokens
from tesserae.shipped import shipped_views


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.small = Signal(False)
        self.clicks = Signal(0)

    def bump(self):
        self.clicks.set(self.clicks.get() + 1)


def opened(tmp_path, props="", icon="home"):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(f"""name: main
widget: Container
style: {{flex_direction: vertical, align_content: top_left, width: 500, height: 400}}
children:
  - {{widget: Fab, name: f, icon: '{icon}', handlers: {{on_click: bump}}{', ' + props if props else ''}}}
""")
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    for _ in range(4):
        view.window.advance(16)
    return view, app.bindings.viewmodel_for("main")


def role(view, name):
    return (view._scheme or tokens.BASELINE)[name]


def f(view):
    return view.node("root.f")


def settle(view, n=40):
    for _ in range(n):
        view.window.advance(16)


def test_it_is_shipped():
    assert "Fab" in shipped_views()


def test_a_fab_is_a_56_pixel_square_with_16_pixel_corners_at_level_three(tmp_path):
    view, _ = opened(tmp_path)
    assert (f(view).get("layout_width"), f(view).get("layout_height")) == (56.0, 56.0) and f(view).get("corner_radius") == 16.0
    assert f(view).get("shadows") and f(view).get("fill") == role(view, "primary_container")
    assert view.node("root.f.icon").get("fill") == role(view, "on_primary_container") and view.node("root.f.icon").get("layout_width") == 24.0


@pytest.mark.parametrize("variant, container, content", [
    ("primary", "primary_container", "on_primary_container"), ("secondary", "secondary_container", "on_secondary_container"),
    ("tertiary", "tertiary_container", "on_tertiary_container"), ("surface", "surface_container_high", "primary"),
])
def test_the_four_colours(tmp_path, variant, container, content):
    view, _ = opened(tmp_path, f"variant: {variant}, label: Add")
    assert f(view).get("fill") == role(view, container)
    assert view.node("root.f.icon").get("fill") == role(view, content) and view.node("root.f.label").get("fill") == role(view, content)


@pytest.mark.parametrize("size, side, radius, glyph", [("small", 40, 12, 24), ("medium", 56, 16, 24), ("large", 96, 28, 36)])
def test_the_three_sizes(tmp_path, size, side, radius, glyph):
    view, _ = opened(tmp_path, f"size: {size}")
    assert (f(view).get("layout_width"), f(view).get("layout_height")) == (float(side), float(side))
    assert f(view).get("corner_radius") == float(radius) and view.node("root.f.icon").get("layout_width") == float(glyph)


def test_a_label_makes_it_extended_with_16_before_the_icon_and_20_after_the_text(tmp_path):
    view, _ = opened(tmp_path, "label: Compose")
    text = view.node("root.f.label")
    assert f(view).get("layout_height") == 56.0
    assert f(view).get("layout_width") == 16 + 24 + 8 + text.get("layout_width") + 20
    assert text.get("font_size") == 14.0 and "root.f.icon" in view._built.specs


def test_an_extended_fab_without_an_icon_has_just_its_label(tmp_path):
    view, _ = opened(tmp_path, "label: Compose", icon="")
    assert "root.f.icon" not in view._built.specs and f(view).get("layout_width") > 56


def test_collapsing_leaves_the_icon_in_a_square(tmp_path):
    view, _ = opened(tmp_path, "label: Compose, collapsed: true")
    assert "root.f.label" not in view._built.specs
    assert (f(view).get("layout_width"), f(view).get("layout_height")) == (56.0, 56.0)


def test_it_collapses_and_extends_with_a_signal(tmp_path):
    view, vm = opened(tmp_path, 'label: Compose, collapsed: "{{ small }}"')
    wide = f(view).get("layout_width")
    vm.small.set(True)
    settle(view)
    assert f(view).get("layout_width") == 56.0 and wide > 56.0
    vm.small.set(False)
    settle(view)
    assert f(view).get("layout_width") == wide


def test_the_label_is_the_name_and_a_collapsed_one_shows_it_as_a_tooltip(tmp_path):
    view, _ = opened(tmp_path, "label: Compose, collapsed: true")
    assert f(view).get("role") == "button" and f(view).get("label") == "Compose"
    view.window.simulate("key_down", key="tab")
    view.window.advance(16)
    assert [t.get("text") for layer in view._tips.values() for t in layer[0].children()] == ["Compose"]


def test_an_extended_one_has_no_tooltip_since_its_label_shows(tmp_path):
    view, _ = opened(tmp_path, "label: Compose")
    view.window.simulate("key_down", key="tab")
    view.window.advance(16)
    assert not view._tips


def test_hovering_lifts_it_from_level_three_to_four_and_a_press_lowers_it_again(tmp_path):
    view, _ = opened(tmp_path)
    rest = f(view).get("shadows")
    view.window.simulate("pointer_enter", node=f(view))
    settle(view)
    hovered = f(view).get("shadows")
    assert hovered != rest
    view.window.simulate("pointer_down", node=f(view))
    settle(view)
    assert f(view).get("shadows") == rest
    view.window.simulate("pointer_up", node=f(view))


def test_a_press_runs_the_calls_handler_unless_disabled(tmp_path):
    view, vm = opened(tmp_path)
    view.window.simulate("click", node=f(view))
    assert vm.clicks.get() == 1
    (tmp_path / "x").mkdir()
    view2, vm2 = opened(tmp_path / "x", "disabled: true")
    view2.window.simulate("click", node=f(view2))
    assert vm2.clicks.get() == 0 and f(view2).get("disabled") is True and f(view2).get("opacity") < 0.5
