"""#129 to #132: the Material 3 icon button -- standard, filled, tonal, outlined; sizes, widths, shapes, a toggle that swaps its icon."""

import pytest

from tesserae import App, Signal, ViewModel, tokens
from tesserae.shipped import shipped_views


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.on = Signal(False)
        self.clicks = Signal(0)

    def bump(self):
        self.clicks.set(self.clicks.get() + 1)


def opened(tmp_path, props="", label="Home"):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(f"""name: main
widget: Container
style: {{flex_direction: vertical, align_content: top_left, width: 400, height: 400}}
children:
  - {{widget: IconButton, name: b, icon: home, label: '{label}', handlers: {{on_click: bump}}{', ' + props if props else ''}}}
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


def b(view):
    return view.node("root.b")


def icon(view):
    return view.node("root.b.icon")


def settle(view, n=40):
    for _ in range(n):
        view.window.advance(16)


def click(view):
    view.window.simulate("click", node=b(view))
    settle(view)


def test_it_is_shipped():
    assert "IconButton" in shipped_views()


def test_a_standard_icon_button_has_no_container_and_a_24_pixel_icon_in_a_40_pixel_circle(tmp_path):
    view, _ = opened(tmp_path)
    assert (b(view).get("layout_width"), b(view).get("layout_height")) == (40.0, 40.0) and b(view).get("corner_radius") >= 20
    assert b(view).get("fill")[3] == 0
    assert icon(view).get("fill") == role(view, "on_surface_variant") and icon(view).get("layout_width") == 24.0


@pytest.mark.parametrize("variant, fill, content", [
    ("filled", "primary", "on_primary"), ("tonal", "secondary_container", "on_secondary_container"),
])
def test_filled_and_tonal_have_their_containers(tmp_path, variant, fill, content):
    view, _ = opened(tmp_path, f"variant: {variant}")
    assert b(view).get("fill") == role(view, fill) and icon(view).get("fill") == role(view, content)


def test_outlined_has_a_one_pixel_outline(tmp_path):
    view, _ = opened(tmp_path, "variant: outlined")
    assert b(view).get("stroke_width") == 1.0 and b(view).get("stroke_color") == role(view, "outline") and b(view).get("fill")[3] == 0


@pytest.mark.parametrize("size, height, glyph", [("xs", 32, 20), ("s", 40, 24), ("m", 56, 24), ("l", 96, 32), ("xl", 136, 40)])
def test_the_five_sizes(tmp_path, size, height, glyph):
    view, _ = opened(tmp_path, f"size: {size}")
    assert b(view).get("layout_height") == float(height) and b(view).get("layout_width") == float(height)
    assert icon(view).get("layout_width") == float(glyph)


@pytest.mark.parametrize("kind, width", [("narrow", 32), ("default", 40), ("wide", 52)])
def test_the_three_widths(tmp_path, kind, width):
    view, _ = opened(tmp_path, f"width_kind: {kind}")
    assert b(view).get("layout_width") == float(width) and b(view).get("layout_height") == 40.0


def test_a_square_one_has_rounded_corners(tmp_path):
    view, _ = opened(tmp_path, "shape: square")
    assert b(view).get("corner_radius") == 12.0


def test_it_is_a_button_named_by_its_label_and_the_label_is_its_tooltip(tmp_path):
    view, _ = opened(tmp_path)
    assert b(view).get("role") == "button" and b(view).get("label") == "Home" and b(view).get("focusable")
    view.window.simulate("key_down", key="tab")
    view.window.advance(16)
    assert [t.get("text") for layer in view._tips.values() for t in layer[0].children()] == ["Home"]


def test_without_a_label_there_is_no_tooltip(tmp_path):
    view, _ = opened(tmp_path, label="")
    view.window.simulate("key_down", key="tab")
    view.window.advance(16)
    assert not view._tips


def test_a_press_runs_the_calls_handler_unless_disabled(tmp_path):
    view, vm = opened(tmp_path)
    click(view)
    assert vm.clicks.get() == 1
    view2, vm2 = opened(tmp_path / "x" if (tmp_path / "x").mkdir() is None else tmp_path, "disabled: true")
    click(view2)
    assert vm2.clicks.get() == 0 and b(view2).get("disabled") is True and b(view2).get("opacity") < 0.5


def test_a_toggle_flips_swaps_its_icon_and_its_colours_and_shape(tmp_path):
    view, _ = opened(tmp_path, "variant: filled, toggle: true, selected_icon: search")
    assert b(view).get("pressed") is False and b(view).get("fill") == role(view, "surface_container_highest")
    assert icon(view).get("fill") == role(view, "on_surface_variant") and b(view).get("corner_radius") >= 20
    assert view._built.specs["root.b.icon"]["icon"] == {"name": "home"}
    click(view)
    assert b(view).get("pressed") is True and b(view).get("fill") == role(view, "primary")
    assert icon(view).get("fill") == role(view, "on_primary") and b(view).get("corner_radius") == 12.0
    assert view._built.specs["root.b.icon"]["icon"] == {"name": "search"}


def test_a_standard_toggle_turns_its_icon_primary_when_on(tmp_path):
    view, _ = opened(tmp_path, "toggle: true")
    click(view)
    assert icon(view).get("fill") == role(view, "primary")


def test_a_toggle_bound_to_a_signal_writes_it(tmp_path):
    view, vm = opened(tmp_path, 'toggle: true, selected: "{{ on }}"')
    click(view)
    assert vm.on.get() is True
    click(view)
    assert vm.on.get() is False


def test_a_pressed_circle_squares_off(tmp_path):
    view, _ = opened(tmp_path)
    view.window.simulate("pointer_down", node=b(view))
    settle(view)
    assert b(view).get("corner_radius") == 12.0
    view.window.simulate("pointer_up", node=b(view))
    settle(view)
    assert b(view).get("corner_radius") >= 20


def test_a_toggle_flips_even_when_the_call_has_its_own_click_handler(tmp_path):
    view, vm = opened(tmp_path, "toggle: true")  # the call's `on_click: bump` runs after the view's own flip
    click(view)
    assert vm.clicks.get() == 1 and b(view).get("pressed") is True
