"""#118 to #122: the Material 3 button -- five variants, five sizes, icons, a toggle, loading and disabled, as a shipped view."""

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


def opened(tmp_path, widget):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        "name: main\nwidget: Container\nstyle: {flex_direction: vertical, align_content: top_left, width: 500, height: 400}\nchildren:\n" + widget)
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    for _ in range(4):
        view.window.advance(16)
    return view, app.bindings.viewmodel_for("main")


def role(view, name):
    return (view._scheme or tokens.BASELINE)[name]


def button(extra="", name="b"):
    return f"  - {{widget: Button, name: {name}, label: Save{', ' + extra if extra else ''}, handlers: {{on_click: bump}}}}\n"


def test_it_is_shipped():
    assert "Button" in shipped_views()


def node(view, part="", name="b"):
    return view.node(f"root.{name}" + (f".{part}" if part else ""))


def click(view, n):
    view.window.simulate("click", node=n)
    for _ in range(40):
        view.window.advance(16)


def settle(view, n=40):
    for _ in range(n):
        view.window.advance(16)


def test_a_filled_button_is_primary_forty_tall_and_as_wide_as_its_label_and_padding(tmp_path):
    view, _ = opened(tmp_path, button())
    b, text = node(view), node(view, "label")
    assert b.get("layout_height") == 40.0 and b.get("fill") == role(view, "primary") and b.get("corner_radius") >= 20
    assert b.get("layout_width") == 24 + text.get("layout_width") + 24
    assert text.get("fill") == role(view, "on_primary") and text.get("font_size") == 14.0


@pytest.mark.parametrize("variant, fill, content", [
    ("filled", "primary", "on_primary"), ("tonal", "secondary_container", "on_secondary_container"),
    ("elevated", "surface_container_low", "primary"), ("text", None, "primary"), ("outlined", None, "primary"),
])
def test_each_variant_has_its_colours(tmp_path, variant, fill, content):
    view, _ = opened(tmp_path, button(f"variant: {variant}"))
    assert node(view, "label").get("fill") == role(view, content)
    if fill:
        assert node(view).get("fill") == role(view, fill)
    else:
        assert node(view).get("fill")[3] == 0


def test_elevated_rests_at_level_one_and_the_outline_is_one_pixel(tmp_path):
    view, _ = opened(tmp_path, button("variant: elevated") + button("variant: outlined", "o") + button("variant: filled", "f"))
    assert node(view).get("shadows") and not node(view, name="f").get("shadows")
    o = node(view, name="o")
    assert o.get("stroke_width") == 1.0 and o.get("stroke_color") == role(view, "outline")


def test_a_text_button_has_twelve_pixels_of_padding(tmp_path):
    view, _ = opened(tmp_path, button("variant: text"))
    assert node(view).get("layout_width") == 12 + node(view, "label").get("layout_width") + 12


@pytest.mark.parametrize("size, height", [("xs", 32), ("s", 40), ("m", 56), ("l", 96), ("xl", 136)])
def test_the_five_sizes(tmp_path, size, height):
    view, _ = opened(tmp_path, button(f"size: {size}"))
    assert node(view).get("layout_height") == float(height)


def test_a_larger_size_has_larger_type_and_padding(tmp_path):
    view, _ = opened(tmp_path, button("size: m") + button("size: xl", "x"))
    assert node(view, "label").get("font_size") == 16.0 and node(view, "label", "x").get("font_size") == 32.0
    assert node(view, name="x").get("layout_width") == 64 + node(view, "label", "x").get("layout_width") + 64


def test_a_square_button_has_rounded_corners_not_a_pill(tmp_path):
    view, _ = opened(tmp_path, button("shape: square"))
    assert node(view).get("corner_radius") == 12.0


def test_icons_take_sixteen_on_their_side_and_the_icon_is_eighteen(tmp_path):
    view, _ = opened(tmp_path, button("icon: home, trailing_icon: search"))
    icon, trailing, text = node(view, "icon"), node(view, "trailing"), node(view, "label")
    assert (icon.get("layout_width"), icon.get("layout_height")) == (18.0, 18.0)
    assert node(view).get("layout_width") == 16 + 18 + 8 + text.get("layout_width") + 8 + 18 + 16
    assert icon.get("fill") == role(view, "on_primary") and trailing.get("fill") == role(view, "on_primary")


def test_a_press_runs_the_call_s_handler_and_the_button_has_a_role_and_a_label(tmp_path):
    view, vm = opened(tmp_path, button())
    b = node(view)
    assert b.get("role") == "button" and b.get("label") == "Save" and b.get("focusable")
    click(view, b)
    assert vm.clicks.get() == 1


def test_a_disabled_button_does_not_respond_and_is_dimmed_and_skipped(tmp_path):
    view, vm = opened(tmp_path, button("disabled: true"))
    b = node(view)
    click(view, b)
    assert vm.clicks.get() == 0 and b.get("disabled") is True and b.get("opacity") < 0.5


def test_a_loading_button_shows_a_spinner_for_its_icon_and_does_not_respond(tmp_path):
    view, vm = opened(tmp_path, button("icon: home, loading: true"))
    assert "root.b.spinner" in view._built.specs and "root.b.icon" not in view._built.specs
    assert node(view).get("busy") is True
    click(view, node(view))
    assert vm.clicks.get() == 0


def test_a_toggle_button_flips_and_swaps_colours_and_shape(tmp_path):
    view, vm = opened(tmp_path, "  - {widget: Button, name: b, label: Mute, toggle: true, selected: \"{{ on }}\"}\n")
    b = node(view)
    assert b.get("pressed") is False and b.get("fill") == role(view, "surface_container_highest")
    assert node(view, "label").get("fill") == role(view, "on_surface_variant") and b.get("corner_radius") >= 20
    click(view, b)
    assert vm.on.get() is True and b.get("pressed") is True and b.get("fill") == role(view, "primary")
    assert node(view, "label").get("fill") == role(view, "on_primary") and b.get("corner_radius") == 12.0
    click(view, b)
    assert vm.on.get() is False and b.get("corner_radius") >= 20


def test_a_button_that_is_no_toggle_has_no_pressed_state(tmp_path):
    view, _ = opened(tmp_path, button())
    assert node(view).get("pressed") is None


def test_hovering_a_filled_button_lifts_it(tmp_path):
    view, _ = opened(tmp_path, button())
    b = node(view)
    assert not b.get("shadows")
    view.window.simulate("pointer_enter", node=b)
    settle(view)
    assert b.get("shadows")


def test_it_has_a_state_layer_and_the_keyboard_activates_it(tmp_path):
    view, vm = opened(tmp_path, button())
    b = node(view)
    assert view.interaction("root.b") is not None
    b.focus()
    view.window.simulate("key_down", key="enter")
    settle(view, 10)
    assert vm.clicks.get() == 1


def test_an_elevated_button_rises_from_level_one_to_two_when_hovered_and_back_to_one_when_pressed(tmp_path):
    view, _ = opened(tmp_path, button("variant: elevated"))
    b = node(view)
    rest = b.get("shadows")
    view.window.simulate("pointer_enter", node=b)
    settle(view)
    hovered = b.get("shadows")
    assert hovered != rest
    view.window.simulate("pointer_down", node=b)
    settle(view)
    assert b.get("shadows") == rest
    view.window.simulate("pointer_up", node=b)


@pytest.mark.parametrize("size, radius", [("xs", 12.0), ("s", 12.0), ("m", 16.0), ("l", 28.0), ("xl", 28.0)])
def test_a_square_button_s_corners_grow_with_its_size(tmp_path, size, radius):
    view, _ = opened(tmp_path, button(f"shape: square, size: {size}"))
    assert node(view).get("corner_radius") == radius


def test_a_square_toggle_becomes_a_pill_while_on(tmp_path):
    view, vm = opened(tmp_path, "  - {widget: Button, name: b, label: Mute, shape: square, toggle: true, selected: \"{{ on }}\"}\n")
    b = node(view)
    assert b.get("corner_radius") == 12.0
    click(view, b)
    assert b.get("corner_radius") >= 20


def test_a_pressed_pill_squares_off_while_the_button_is_held(tmp_path):
    view, _ = opened(tmp_path, button())
    b = node(view)
    view.window.simulate("pointer_down", node=b)
    settle(view)
    assert b.get("corner_radius") == 12.0
    view.window.simulate("pointer_up", node=b)
    settle(view)
    assert b.get("corner_radius") >= 20
