"""#199: the Material 3 carousel -- a row of rounded items that scrolls sideways and settles on one."""

import pytest

from tesserae import App, Signal, ViewModel, tokens
from tesserae.shipped import shipped_views

ITEMS = "[" + ", ".join("{value: i%d, title: 'Item %d'}" % (n, n) for n in range(6)) + "]"


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.chosen = Signal("")


def opened(tmp_path, props="", items=ITEMS):
    (tmp_path / "Views").mkdir(exist_ok=True)
    lines = "\n    ".join(props.split(", ")) if props else ""
    (tmp_path / "Views" / "Main_View.yaml").write_text(f"""name: main
widget: Container
style: {{flex_direction: vertical, align_content: top_left, width: 500, height: 300}}
children:
  - widget: Carousel
    name: c
    items: {items}
    chosen: "{{{{ chosen }}}}"
    {lines}
""")
    app = App(root=tmp_path, width=500, height=300)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    for _ in range(8):
        view.window.advance(16)
    return view, app.bindings.viewmodel_for("main")


def role(view, name):
    return (view._scheme or tokens.BASELINE)[name]


def settle(view, n=40):
    for _ in range(n):
        view.window.advance(16)


def item(view, n):
    return view.node(f"root.c.item[i{n}]")


def strip(view):
    return view._built.outer["root.c"]


def test_it_is_shipped():
    assert "Carousel" in shipped_views()


def test_it_is_a_horizontal_scroll_view_of_the_size_it_is_given_that_settles_on_an_item(tmp_path):
    view, _ = opened(tmp_path)
    s = strip(view)
    assert (s.get("layout_width"), s.get("layout_height")) == (360.0, 200.0) and s.get("orientation") == "horizontal" and s.get("scroll_snap") == "start"
    assert item(view, 0).get("snap_align") == "start"


def test_uncontained_items_are_item_width_wide_28_pixel_rounded_and_8_pixels_apart(tmp_path):
    view, _ = opened(tmp_path, "item_width: 150")
    a, b = item(view, 0), item(view, 1)
    assert (a.get("layout_width"), a.get("layout_height"), a.get("corner_radius")) == (150.0, 200.0, 28.0) and b.get("layout_x") == a.get("layout_x") + 150 + 8
    assert a.get("fill") == role(view, "surface_container_highest")


def test_the_item_has_its_title_on_a_darkened_band_at_the_bottom(tmp_path):
    view, _ = opened(tmp_path)
    cap, title = view.node("root.c.item[i0].caption"), view.node("root.c.item[i0].caption.title")
    assert cap.get("layout_y") + cap.get("layout_height") == item(view, 0).get("layout_y") + 200
    assert title.get("text") == "Item 0" and title.get("fill") == (255, 255, 255, 255) and cap.get("fill")[3] == round(0.32 * 255)


def test_multi_browse_has_a_large_item_a_medium_one_and_then_small_ones(tmp_path):
    view, _ = opened(tmp_path, "variant: multi_browse")
    widths = [item(view, n).get("layout_width") for n in range(4)]
    assert widths[0] > widths[1] > widths[2] and widths[2] == widths[3] == 56.0


def test_hero_items_are_large_with_a_peek_of_the_next(tmp_path):
    view, _ = opened(tmp_path, "variant: hero")
    a, b = item(view, 0), item(view, 1)
    assert a.get("layout_width") == 360 - 56 - 8 and b.get("layout_x") < strip(view).get("layout_x") + 360 and b.get("layout_x") + b.get("layout_width") > strip(view).get("layout_x") + 360


def test_center_hero_items_snap_to_the_centre_with_room_either_side(tmp_path):
    view, _ = opened(tmp_path, "variant: center_hero")
    assert strip(view).get("scroll_snap") == "center" and item(view, 0).get("snap_align") == "center"
    a = item(view, 0)
    assert a.get("layout_width") == 360 - 2 * 56 - 2 * 8 and a.get("layout_x") == strip(view).get("layout_x") + 56 + 8


def test_the_wheel_scrolls_it_sideways_and_it_settles_with_an_item_at_the_start(tmp_path):
    view, _ = opened(tmp_path, "item_width: 150")
    view.window.simulate("wheel", node=strip(view), delta_x=120.0, delta_y=0.0)
    settle(view, 60)
    assert strip(view).get("scroll_offset") == 158.0  # the second item (150 + 8)


def test_a_small_wheel_turn_settles_back_on_the_first_item(tmp_path):
    view, _ = opened(tmp_path, "item_width: 150")
    view.window.simulate("wheel", node=strip(view), delta_x=40.0, delta_y=0.0)
    settle(view, 60)
    assert strip(view).get("scroll_offset") == 0.0


def test_pressing_an_item_chooses_it(tmp_path):
    view, vm = opened(tmp_path)
    view.window.simulate("click", node=item(view, 1))
    assert vm.chosen.get() == "i1"


def test_the_items_are_focusable_list_items_named_by_their_titles_and_the_arrows_move_between_them(tmp_path):
    view, _ = opened(tmp_path)
    assert item(view, 2).get("role") == "listitem" and item(view, 2).get("label") == "Item 2" and item(view, 0).get("focusable")
    item(view, 0).focus()
    settle(view, 2)
    view.window.simulate("key_down", key="arrow_right")
    settle(view, 4)
    assert item(view, 1).get("focused") is True
    assert strip(view).get("role") == "group" and strip(view).get("label") == "Carousel"


def test_a_picture_fills_the_item(tmp_path):
    from PIL import Image
    (tmp_path / "Views").mkdir()
    Image.new("RGBA", (40, 20), (200, 0, 0, 255)).save(tmp_path / "Views" / "pic.png")
    view, _ = opened(tmp_path, items="[{value: a, title: A, image: pic.png}]")
    pic = view.node("root.c.item[a].picture")
    assert (pic.get("layout_width"), pic.get("layout_height")) == (200.0, 200.0)
