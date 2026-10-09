"""#153: the Material 3 list item -- one to three lines, leading and trailing content, selectable, with a divider."""

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


def opened(tmp_path, props="headline: Inbox", children=""):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(f"""name: main
widget: Container
style: {{flex_direction: vertical, align_content: top_left, width: 400, height: 400}}
children:
  - {{widget: ListItem, name: li, {props}, handlers: {{on_click: bump}}{', children: [' + children + ']' if children else ''}}}
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


def li(view):
    return view.node("root.li")


def part(view, name):
    return view.node(f"root.li.{name}")


def settle(view, n=40):
    for _ in range(n):
        view.window.advance(16)


def test_it_is_shipped():
    assert "ListItem" in shipped_views()


def test_a_one_line_item_is_56_tall_as_wide_as_its_place_with_16_pixels_each_side(tmp_path):
    view, _ = opened(tmp_path)
    assert (li(view).get("layout_width"), li(view).get("layout_height")) == (400.0, 56.0)
    assert part(view, "text.headline").get("layout_x") == li(view).get("layout_x") + 16
    assert part(view, "text.headline").get("font_size") == 16.0 and part(view, "text.headline").get("fill") == role(view, "on_surface")


@pytest.mark.parametrize("props, height", [
    ("headline: A", 56), ("headline: A, supporting: B", 72), ("headline: A, supporting: B, overline: C", 88),
    ("headline: A, overline: C", 72), ("headline: A, lines: 3", 88), ("headline: A, supporting: B, lines: 1", 56),
])
def test_it_is_as_tall_as_its_lines(tmp_path, props, height):
    view, _ = opened(tmp_path, props)
    assert li(view).get("layout_height") == float(height)


def test_the_supporting_text_is_body_medium_in_on_surface_variant_under_the_headline(tmp_path):
    view, _ = opened(tmp_path, "headline: Inbox, supporting: Unread messages, overline: Mail")
    sup, head, over = part(view, "text.supporting"), part(view, "text.headline"), part(view, "text.overline")
    assert sup.get("font_size") == 14.0 and sup.get("fill") == role(view, "on_surface_variant")
    assert over.get("layout_y") < head.get("layout_y") < sup.get("layout_y") and over.get("font_size") == 11.0


def test_a_leading_icon_and_trailing_text_and_icon(tmp_path):
    view, _ = opened(tmp_path, "headline: A, leading_icon: home, trailing_text: 5m, trailing_icon: search")
    icon, head, text, tail = part(view, "leading_icon"), part(view, "text.headline"), part(view, "trailing_text"), part(view, "trailing_icon")
    assert (icon.get("layout_width"), icon.get("fill")) == (24.0, role(view, "on_surface_variant"))
    assert head.get("layout_x") == icon.get("layout_x") + 24 + 16
    assert text.get("layout_x") > head.get("layout_x") and tail.get("layout_x") + 24 + 16 == li(view).get("layout_x") + 400


def test_an_avatar_is_a_40_pixel_circle_with_letters_in_primary_container(tmp_path):
    view, _ = opened(tmp_path, "headline: A, leading_text: JD")
    av = part(view, "avatar")
    assert (av.get("layout_width"), av.get("layout_height")) == (40.0, 40.0) and av.get("corner_radius") >= 20
    assert av.get("fill") == role(view, "primary_container") and part(view, "avatar.avatar_text").get("fill") == role(view, "on_primary_container")


def test_a_leading_slot_and_a_trailing_slot_hold_your_own_content(tmp_path):
    children = "{widget: Switch, name: sw, slot: trailing, label: ''}, {widget: Checkbox, name: cb, slot: leading, label: ''}"
    view, _ = opened(tmp_path, "headline: Wi-Fi", children)
    assert view.node("root.li.cb").get("layout_x") < part(view, "text.headline").get("layout_x") < view.node("root.li.sw").get("layout_x")


def test_a_press_runs_the_calls_handler_and_it_is_a_list_item_named_by_its_headline(tmp_path):
    view, vm = opened(tmp_path, "headline: Inbox, supporting: Unread")
    assert li(view).get("role") == "listitem" and li(view).get("label") == "Inbox" and li(view).get("focusable")
    view.window.simulate("click", node=li(view))
    assert vm.clicks.get() == 1


def test_a_selectable_item_flips_and_turns_secondary_container(tmp_path):
    view, vm = opened(tmp_path, 'headline: A, selectable: true, selected: "{{ on }}"')
    assert li(view).get("selected") is False and li(view).get("fill")[3] == 0
    view.window.simulate("click", node=li(view))
    settle(view)
    assert vm.on.get() is True and li(view).get("selected") is True and li(view).get("fill") == role(view, "secondary_container")


def test_an_item_that_is_not_selectable_has_no_selected_state(tmp_path):
    view, _ = opened(tmp_path)
    assert li(view).get("selected") is None


def test_a_disabled_item_is_dimmed_and_does_not_respond(tmp_path):
    view, vm = opened(tmp_path, "headline: A, disabled: true")
    view.window.simulate("click", node=li(view))
    assert vm.clicks.get() == 0 and li(view).get("disabled") is True and li(view).get("opacity") < 0.5


def test_a_divider_runs_along_the_bottom_edge(tmp_path):
    view, _ = opened(tmp_path, "headline: A, divider: true")
    line = part(view, "line")
    assert line.get("layout_x") == li(view).get("layout_x") + 16 and abs(line.get("layout_y") - (li(view).get("layout_y") + 56)) <= 1
    (tmp_path / "x").mkdir()
    view2, _ = opened(tmp_path / "x")
    assert "root.li.line" not in view2._built.specs


def test_a_long_headline_is_cut_to_one_line(tmp_path):
    view, _ = opened(tmp_path, "headline: " + "word " * 80)
    assert part(view, "text.headline").get("layout_height") < 30 and part(view, "text.headline").get("overflow") == "ellipsis"
