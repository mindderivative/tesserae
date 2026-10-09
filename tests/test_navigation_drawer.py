"""#163, #164: the Material 3 navigation drawer and its items -- standard (beside the content), modal (over a scrim), and one for the app's screens."""

import pytest

from tesserae import App, Signal, ViewModel, tokens
from tesserae.shipped import shipped_views

ITEMS = """[{value: inbox, label: Inbox, icon: home, badge: 24}, {value: sent, label: Sent, icon: send}, {divider: true}, {heading: Labels},
          {value: work, label: Work, icon: tag}, {value: off, label: Archive, icon: folder, disabled: true}]"""


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.open = Signal(True)
        self.page = Signal("sent")


def opened(tmp_path, props="", children="", widget="NavigationDrawer", items=ITEMS, open_=True):
    (tmp_path / "Views").mkdir(exist_ok=True)
    lines = "\n    ".join(props.split(", ")) if props else ""
    kids = f"\n    children:\n{children}" if children else ""
    (tmp_path / "Views" / "Main_View.yaml").write_text(f"""name: main
widget: Container
style: {{flex_direction: horizontal, align_content: top_left, width: 800, height: 500}}
children:
  - widget: {widget}
    name: d
    open: "{{{{ open }}}}"
    items: {items}
    selected: "{{{{ page }}}}"
    {lines}{kids}
  - {{widget: Container, name: main, style: {{flex: fill, height: 100%, background: surface_container}}}}
""")
    app = App(root=tmp_path, width=800, height=500)
    app.bind(VM)
    view = app.open_view("Main")
    vm = app.bindings.viewmodel_for("main")
    app.show("main")
    settle(view, 4)
    if not open_:
        vm.open.set(False)
        settle(view, 30)
    return view, vm


def role(view, name):
    return (view._scheme or tokens.BASELINE)[name]


def settle(view, n=30):
    for _ in range(n):
        view.window.advance(16)


def item(view, i, base="root.d.panel.list"):
    return view.node(f"{base}.row[{i}].item")


def test_they_are_shipped():
    assert {"NavigationDrawer", "NavigationDrawerItem", "NavigationDrawerModal", "NavigationDrawerScreens"} <= set(shipped_views())


def test_a_standard_drawer_is_360_wide_beside_the_content_on_a_surface_column(tmp_path):
    view, _ = opened(tmp_path)
    d = view.node("root.d")
    assert (d.get("layout_width"), d.get("layout_height")) == (360.0, 500.0) and d.get("fill") == role(view, "surface")
    assert view.node("root.main").get("layout_x") == 360.0


def test_an_item_is_a_56_tall_pill_12_pixels_in_with_a_24_pixel_icon_and_a_label_large_label(tmp_path):
    view, _ = opened(tmp_path)
    it = item(view, 0)
    assert (it.get("layout_height"), it.get("layout_x"), it.get("corner_radius")) == (56.0, 12.0, 28.0)
    icon, label = view.node("root.d.panel.list.row[0].item.icon"), view.node("root.d.panel.list.row[0].item.label")
    assert (icon.get("layout_width"), icon.get("layout_x")) == (24.0, it.get("layout_x") + 16) and label.get("layout_x") == icon.get("layout_x") + 24 + 12
    assert label.get("font_size") == 14.0


def test_a_badge_sits_at_the_end(tmp_path):
    view, _ = opened(tmp_path)
    badge, it = view.node("root.d.panel.list.row[0].item.badge"), item(view, 0)
    assert badge.get("text") == "24" and badge.get("layout_x") + badge.get("layout_width") == it.get("layout_x") + it.get("layout_width") - 24


def test_the_chosen_destination_is_secondary_container_and_the_rest_plain(tmp_path):
    view, _ = opened(tmp_path)
    assert item(view, 1).get("fill") == role(view, "secondary_container") and item(view, 0).get("fill")[3] == 0
    assert view.node("root.d.panel.list.row[1].item.label").get("fill") == role(view, "on_secondary_container")
    assert view.node("root.d.panel.list.row[0].item.label").get("fill") == role(view, "on_surface_variant")


def test_each_destination_is_a_link_and_the_current_one_is_the_page(tmp_path):
    view, _ = opened(tmp_path)
    assert item(view, 0).get("role") == "link" and item(view, 0).get("label") == "Inbox"
    assert [item(view, i).get("current") for i in (0, 1, 4)] == [False, "page", False]


def test_pressing_a_destination_chooses_it(tmp_path):
    view, vm = opened(tmp_path)
    view.window.simulate("click", node=item(view, 4))
    settle(view, 30)
    assert vm.page.get() == "work" and item(view, 4).get("fill") == role(view, "secondary_container") and item(view, 1).get("fill")[3] == 0


def test_a_disabled_destination_does_not_respond(tmp_path):
    view, vm = opened(tmp_path)
    view.window.simulate("click", node=item(view, 5))
    settle(view, 6)
    assert vm.page.get() == "sent"


def test_a_divider_and_a_heading_are_rows_of_their_own(tmp_path):
    view, _ = opened(tmp_path)
    assert "root.d.panel.list.row[2].divider" in view._built.specs and "root.d.panel.list.row[2].item" not in view._built.specs
    heading = view.node("root.d.panel.list.row[3].heading")
    assert heading.get("text") == "Labels" and heading.get("fill") == role(view, "on_surface_variant") and heading.get("font_size") == 14.0


def test_one_tab_stop_and_the_arrows_move_and_choose(tmp_path):
    view, vm = opened(tmp_path)
    assert [item(view, i).get("tab_index") for i in (0, 1, 4)].count(0) == 1 and item(view, 1).get("tab_index") == 0
    item(view, 1).focus()
    settle(view, 2)
    view.window.simulate("key_down", key="arrow_down")
    settle(view, 6)
    assert vm.page.get() == "work"


def test_header_and_footer_hold_your_own_content(tmp_path):
    children = "      - {widget: Container, name: brand, slot: header, style: {width: 100, height: 40, background: primary}}\n      - {widget: Container, name: foot, slot: footer, style: {width: 100, height: 30, background: secondary}}\n"
    view, _ = opened(tmp_path, children=children)
    assert view.node("root.d.brand").get("layout_y") < item(view, 0).get("layout_y") < view.node("root.d.foot").get("layout_y")


def test_closing_a_standard_drawer_gives_the_content_its_room_back_and_the_width_eases(tmp_path):
    view, vm = opened(tmp_path)
    vm.open.set(False)
    for _ in range(6):
        view.window.advance(16)
    assert 0.0 < view.node("root.d").get("layout_width") < 360.0
    settle(view, 30)
    assert view.node("root.d").get("layout_width") == 0.0 and view.node("root.main").get("layout_width") == 800.0
    vm.open.set(True)
    settle(view, 30)
    assert view.node("root.d").get("layout_width") == 360.0


def test_the_width_is_held_between_256_and_360(tmp_path):
    view, _ = opened(tmp_path, "width: 900")
    assert view.node("root.d").get("layout_width") == 360.0
    (tmp_path / "n").mkdir()
    narrow, _ = opened(tmp_path / "n", "width: 100")
    assert narrow.node("root.d").get("layout_width") == 256.0


def test_a_long_list_scrolls(tmp_path):
    many = "[" + ", ".join("{value: v%d, label: Item %d, icon: home}" % (i, i) for i in range(20)) + "]"
    view, _ = opened(tmp_path, items=many)
    scroller = view._built.outer["root.d.panel.list"]
    assert scroller.get("layout_height") == 500.0 - 24
    view.window.simulate("wheel", node=scroller, delta_x=0.0, delta_y=120.0)
    settle(view, 4)
    assert scroller.get("scroll_offset") > 0


# -- the modal drawer ---------------------------------------------------------------------------------------------------------


def modal(tmp_path, props="", **kw):
    view, vm = opened(tmp_path, props, widget="NavigationDrawerModal", **kw)
    vm.open.set(False)
    settle(view, 4)
    vm.open.set(True)
    settle(view, 8)
    return view, vm


def test_the_modal_drawer_is_over_the_content_on_a_scrim_from_the_start_edge(tmp_path):
    view, _ = modal(tmp_path)
    sheet = view.node("root.d.sheet")
    assert view.node("root.main").get("layout_width") == 440.0 or view.node("root.main").get("layout_width") == 800.0
    assert (sheet.get("layout_x"), sheet.get("layout_width")) == (0.0, 360.0) and view._built.nodes["root.d"].get("fill")[3] == round(0.32 * 255)
    assert sheet.get("fill") == role(view, "surface_container_low") and sheet.get("corner_radius") == (0.0, 16.0, 16.0, 0.0) and sheet.get("shadows")
    assert sheet.get("role") == "dialog"


def test_pressing_a_destination_in_the_modal_drawer_chooses_it_and_closes_it(tmp_path):
    view, vm = modal(tmp_path)
    view.window.simulate("click", node=item(view, 4, "root.d.sheet.panel.list"))
    settle(view, 6)
    assert vm.page.get() == "work" and vm.open.get() is False and not view._shown_layers


def test_escape_and_the_scrim_close_the_modal_drawer_without_choosing(tmp_path):
    view, vm = modal(tmp_path)
    view.window.simulate("key_down", key="escape")
    settle(view, 6)
    assert vm.open.get() is False and vm.page.get() == "sent"
    vm.open.set(True)
    settle(view, 8)
    view.window.simulate("pointer_down", x=700, y=250)
    settle(view, 6)
    assert vm.open.get() is False and vm.page.get() == "sent"


# -- the screens drawer (#164 and the app's screens) --------------------------------------------------------------------------


class A(ViewModel):
    views = "a"


class B(ViewModel):
    views = "b"


def test_the_screens_drawer_selects_the_screen_showing_and_navigates_when_pressed(tmp_path):
    (tmp_path / "Views").mkdir()
    for name in ("a", "b"):
        (tmp_path / "Views" / f"{name.upper()}_View.yaml").write_text(f"""name: {name}
widget: Container
style: {{flex_direction: horizontal, width: 600, height: 400}}
children:
  - widget: NavigationDrawerScreens
    name: d
    items: [{{screen: a, label: Home, icon: home}}, {{divider: true}}, {{heading: More}}, {{screen: b, label: Settings, icon: search, badge: 3}}]
""")
    app = App(root=tmp_path, width=600, height=400)
    app.bind(A)
    app.bind(B)
    a, b = app.open_view("A"), app.open_view("B")
    app.show("a")
    for _ in range(24):
        app.window.advance(16)
    assert a.node("root.d.row[0].item").get("current") == "page" and a.node("root.d.row[3].item").get("current") is False
    assert a.node("root.d.row[0].item").get("fill") == role(a, "secondary_container")
    a.window.simulate("click", node=a.node("root.d.row[3].item"))
    for _ in range(24):
        app.window.advance(16)
    assert app.current_screen.get() == "b" and b.node("root.d.row[3].item").get("current") == "page"
