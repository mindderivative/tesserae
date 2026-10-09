"""#148, #149, #150: the Material 3 card -- elevated, filled, outlined; media, headline, text, actions; actionable and selectable."""

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


def opened(tmp_path, props="headline: Trip", children=""):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(f"""name: main
widget: Container
style: {{flex_direction: vertical, align_content: top_left, width: 400, height: 500}}
children:
  - {{widget: Card, name: c, {props}, style: {{width: 240}}{', children: [' + children + ']' if children else ''}}}
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


def card(view):
    return view.node("root.c")


def settle(view, n=40):
    for _ in range(n):
        view.window.advance(16)


def test_it_is_shipped():
    assert "Card" in shipped_views()


def test_an_elevated_card_is_surface_container_low_with_12_pixel_corners_at_level_one(tmp_path):
    view, _ = opened(tmp_path)
    assert card(view).get("fill") == role(view, "surface_container_low") and card(view).get("corner_radius") == 12.0 and card(view).get("shadows")


def test_a_filled_card_is_a_higher_surface_with_no_shadow(tmp_path):
    view, _ = opened(tmp_path, "variant: filled, headline: Trip")
    assert card(view).get("fill") == role(view, "surface_container_highest") and not card(view).get("shadows")


def test_an_outlined_card_is_a_surface_with_a_one_pixel_outline_variant_border(tmp_path):
    view, _ = opened(tmp_path, "variant: outlined, headline: Trip")
    c = card(view)
    assert c.get("fill") == role(view, "surface") and c.get("stroke_width") == 1.0 and c.get("stroke_color") == role(view, "outline_variant") and not c.get("shadows")


def test_the_text_has_16_pixels_around_it_and_the_three_styles(tmp_path):
    view, _ = opened(tmp_path, "headline: Trip, subhead: Paris, text: Three days")
    head, sub, text = (view.node(f"root.c.body.{n}") for n in ("headline", "subhead", "text"))
    assert head.get("layout_x") == card(view).get("layout_x") + 16 and head.get("layout_y") == card(view).get("layout_y") + 16
    assert (head.get("font_size"), sub.get("font_size"), text.get("font_size")) == (22.0, 14.0, 14.0)
    assert head.get("fill") == role(view, "on_surface") and sub.get("fill") == role(view, "on_surface_variant")
    assert head.get("layout_y") < sub.get("layout_y") < text.get("layout_y")


def test_a_picture_runs_across_the_top_and_is_clipped_to_the_corners(tmp_path):
    from PIL import Image
    (tmp_path / "Views").mkdir()
    Image.new("RGBA", (40, 20), (200, 0, 0, 255)).save(tmp_path / "Views" / "pic.png")
    view, _ = opened(tmp_path, "headline: Trip, media: pic.png, media_height: 100")
    pic = view.node("root.c.picture")
    assert (pic.get("layout_width"), pic.get("layout_height")) == (240.0, 100.0) and pic.get("layout_y") == card(view).get("layout_y")
    assert view.node("root.c.body.headline").get("layout_y") == card(view).get("layout_y") + 100 + 16


def test_your_content_follows_the_text_and_actions_sit_at_the_end(tmp_path):
    children = "{widget: Container, name: extra, style: {width: 50, height: 20}}, {widget: Button, name: ok, slot: actions, label: OK, variant: text}"
    view, _ = opened(tmp_path, "headline: Trip, text: Hi", children)
    assert view.node("root.c.body.text").get("layout_y") < view.node("root.c.extra").get("layout_y") < view.node("root.c.ok").get("layout_y")
    ok = view.node("root.c.ok")
    assert ok.get("layout_x") + ok.get("layout_width") == card(view).get("layout_x") + 240 - 16


def test_a_plain_card_is_a_group_that_is_not_pressable(tmp_path):
    view, vm = opened(tmp_path)
    assert card(view).get("role") == "group" and card(view).get("label") == "Trip" and not card(view).get("focusable")


def test_an_actionable_card_is_one_button_that_runs_the_calls_handler(tmp_path):
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text("""name: main
widget: Container
style: {flex_direction: vertical, align_content: top_left, width: 400, height: 500}
children:
  - {widget: Card, name: c, headline: Trip, actionable: true, style: {width: 240}, handlers: {on_click: bump}}
""")
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    settle(view, 4)
    assert card(view).get("role") == "button" and card(view).get("focusable") and view.interaction("root.c") is not None
    view.window.simulate("click", node=card(view))
    assert app.bindings.viewmodel_for("main").clicks.get() == 1


def test_a_plain_card_has_no_state_layer(tmp_path):
    view, _ = opened(tmp_path)
    assert view.interaction("root.c") is None


def test_an_actionable_elevated_card_lifts_when_hovered_and_a_plain_one_does_not(tmp_path):
    view, _ = opened(tmp_path, "actionable: true, headline: Trip")
    rest = card(view).get("shadows")
    view.window.simulate("pointer_enter", node=card(view))
    settle(view)
    assert card(view).get("shadows") != rest
    (tmp_path / "x").mkdir()
    plain, _ = opened(tmp_path / "x")
    rest2 = card(plain).get("shadows")
    plain.window.simulate("pointer_enter", node=card(plain))
    settle(plain)
    assert card(plain).get("shadows") == rest2


def test_selected_changes_the_colours_and_is_reported(tmp_path):
    view, _ = opened(tmp_path, "headline: Trip, selected: true")
    assert card(view).get("fill") == role(view, "secondary_container") and card(view).get("selected") is True
    (tmp_path / "o").mkdir()
    out, _ = opened(tmp_path / "o", "variant: outlined, headline: Trip, selected: true")
    assert card(out).get("stroke_color") == role(out, "outline")


def test_a_disabled_card_is_dimmed(tmp_path):
    view, _ = opened(tmp_path, "headline: Trip, disabled: true")
    assert card(view).get("disabled") is True and card(view).get("opacity") < 0.5


def test_interaction_may_be_worked_out_from_params_but_not_from_a_signal(tmp_path):
    from tesserae.spec.nodes import LoadError
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text("""name: main
widget: Container
style: {width: 100, height: 100}
children:
  - {widget: Container, name: c, interaction: "{{ on }}", style: {width: 50, height: 50, background: primary}, handlers: {on_click: bump}}
""")
    app = App(root=tmp_path)
    app.bind(VM)
    with pytest.raises((LoadError, ValueError), match="interaction cannot change"):
        app.open_view("Main")
