"""#159, #160: the Material 3 navigation rail and its items -- selected pill, badges, expanded, header and footer, arrows choose."""

import pytest

from tesserae import App, Signal, ViewModel, tokens
from tesserae.shipped import shipped_views

ITEMS = "[{value: home, label: Home, icon: home}, {value: search, label: Search, icon: search, badge: 3}, {value: menu, label: Menu, icon: menu}]"


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.page = Signal("search")


def opened(tmp_path, props="", children=""):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(f"""name: main
widget: Container
style: {{flex_direction: horizontal, align_content: top_left, width: 500, height: 600}}
children:
  - {{widget: NavigationRail, name: r, items: {ITEMS}, selected: "{{{{ page }}}}"{', ' + props if props else ''}{', children: [' + children + ']' if children else ''}}}
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


def item(view, value):
    return view.node(f"root.r.destinations.item[{value}]")


def part(view, value, name):
    return view.node(f"root.r.destinations.item[{value}].{name}")


def settle(view, n=40):
    for _ in range(n):
        view.window.advance(16)


def test_they_are_shipped():
    assert {"NavigationRail", "NavigationRailItem"} <= set(shipped_views())


class A(ViewModel):
    views = "a"


class B(ViewModel):
    views = "b"


def screens_app(tmp_path, props=""):
    (tmp_path / "Views").mkdir(exist_ok=True)
    for name in ("a", "b"):
        (tmp_path / "Views" / f"{name.upper()}_View.yaml").write_text(f"""name: {name}
widget: Container
style: {{flex_direction: horizontal, align_content: top_left, width: 500, height: 600}}
children:
  - widget: NavigationRailScreens
    name: r
    {props}
    items: [{{screen: a, label: Home, icon: home}}, {{screen: b, label: Settings, icon: search, badge: 2}}]
""")
    app = App(root=tmp_path, width=500, height=600)
    app.bind(A)
    app.bind(B)
    view_a, view_b = app.open_view("A"), app.open_view("B")
    app.show("a")
    for _ in range(4):
        app.window.advance(16)
    return app, view_a, view_b


# -- the rail -----------------------------------------------------------------------------------------------------------------


def test_the_rail_is_80_pixels_wide_and_a_surface_column(tmp_path):
    view, _ = opened(tmp_path)
    rail = view.node("root.r")
    assert (rail.get("layout_width"), rail.get("layout_height")) == (80.0, 600.0) and rail.get("fill") == role(view, "surface")
    assert view.node("root.r").get("role") == "group" and view.node("root.r").get("label") == "Navigation"


def test_the_destinations_start_44_pixels_down_and_are_12_apart(tmp_path):
    view, _ = opened(tmp_path)
    home, search = item(view, "home"), item(view, "search")
    assert home.get("layout_y") == view.node("root.r").get("layout_y") + 44
    assert search.get("layout_y") == home.get("layout_y") + home.get("layout_height") + 12
    assert home.get("layout_x") + home.get("layout_width") / 2 == 40  # centred on the rail


def test_an_item_is_a_56_by_32_pill_over_a_label_medium_label(tmp_path):
    view, _ = opened(tmp_path)
    pill, label = part(view, "home", "pill"), part(view, "home", "label")
    assert (pill.get("layout_width"), pill.get("layout_height")) == (56.0, 32.0) and pill.get("corner_radius") == 16.0
    assert label.get("font_size") == 12.0 and label.get("layout_y") > pill.get("layout_y") + 32
    assert part(view, "home", "pill.icon").get("layout_width") == 24.0


def test_the_selected_destination_has_the_pill_and_the_other_colours(tmp_path):
    view, _ = opened(tmp_path)
    assert part(view, "search", "pill").get("fill") == role(view, "secondary_container")
    assert part(view, "home", "pill").get("fill")[3] == 0
    assert part(view, "search", "pill.badged.badged_icon").get("fill") == role(view, "on_secondary_container")
    assert part(view, "home", "pill.icon").get("fill") == role(view, "on_surface_variant")
    assert part(view, "search", "label").get("fill") == role(view, "on_surface") and part(view, "home", "label").get("fill") == role(view, "on_surface_variant")


def test_each_destination_is_a_link_named_by_its_label_and_the_current_one_is_the_page(tmp_path):
    view, _ = opened(tmp_path)
    assert [item(view, v).get("role") for v in ("home", "search", "menu")] == ["link"] * 3
    assert item(view, "home").get("label") == "Home"
    assert [item(view, v).get("current") for v in ("home", "search", "menu")] == [False, "page", False]


def test_a_badge_sits_on_the_icon(tmp_path):
    view, _ = opened(tmp_path)
    assert part(view, "search", "pill.badged.mark.label").get("text") == "3"
    assert "root.r.destinations.item[home].pill.badged" not in view._built.specs


def test_pressing_a_destination_chooses_it(tmp_path):
    view, vm = opened(tmp_path)
    view.window.simulate("click", node=item(view, "menu"))
    settle(view)
    assert vm.page.get() == "menu" and part(view, "menu", "pill").get("fill") == role(view, "secondary_container")
    assert part(view, "search", "pill").get("fill")[3] == 0


def test_one_tab_stop_and_the_arrows_move_and_choose(tmp_path):
    view, vm = opened(tmp_path)
    assert [item(view, v).get("tab_index") for v in ("home", "search", "menu")] == [-1, 0, -1]
    item(view, "search").focus()
    view.window.simulate("key_down", key="arrow_down")
    settle(view, 10)
    assert vm.page.get() == "menu"
    view.window.simulate("key_down", key="Home")
    settle(view, 10)
    assert vm.page.get() == "home"


def test_expanded_it_is_220_wide_with_the_label_beside_the_icon(tmp_path):
    view, _ = opened(tmp_path, "expanded: true")
    assert view.node("root.r").get("layout_width") == 220.0
    pill = part(view, "home", "pill")
    assert pill.get("layout_height") == 56.0 and "root.r.destinations.item[home].label" not in view._built.specs
    inline = part(view, "home", "pill.inline_label")
    assert inline.get("layout_x") > part(view, "home", "pill.icon").get("layout_x") + 24 and inline.get("font_size") == 14.0
    assert part(view, "search", "pill").get("fill") == role(view, "secondary_container")


def test_a_header_and_a_footer_hold_your_own_content(tmp_path):
    children = "{widget: Container, name: fab, slot: header, style: {width: 56, height: 56, background: primary}}, {widget: Container, name: help, slot: footer, style: {width: 40, height: 40, background: secondary}}"
    view, _ = opened(tmp_path, children=children)
    fab, help_ = view.node("root.r.fab"), view.node("root.r.help")
    assert fab.get("layout_y") < item(view, "home").get("layout_y") < help_.get("layout_y")
    assert help_.get("layout_y") + 40 <= 600


def test_the_destinations_can_be_grouped_at_the_centre_or_bottom(tmp_path):
    top, _ = opened(tmp_path)
    (tmp_path / "c").mkdir()
    centre, _ = opened(tmp_path / "c", "alignment: center")
    (tmp_path / "d").mkdir()
    bottom, _ = opened(tmp_path / "d", "alignment: bottom")
    y = [item(v, "home").get("layout_y") for v in (top, centre, bottom)]
    assert y[0] < y[1] < y[2]


def test_a_disabled_destination_does_not_respond(tmp_path):
    items = "[{value: home, label: Home, icon: home, disabled: true}, {value: search, label: Search, icon: search}]"
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text(f"""name: main
widget: Container
style: {{flex_direction: horizontal, width: 500, height: 600}}
children:
  - {{widget: NavigationRail, name: r, items: {items}, selected: "{{{{ page }}}}"}}
""")
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    settle(view, 4)
    view.window.simulate("click", node=item(view, "home"))
    settle(view, 4)
    assert app.bindings.viewmodel_for("main").page.get() == "search"


# -- the screens variants (#161, #162) ---------------------------------------------------------------------------------------


def test_the_screens_rail_selects_the_screen_showing_and_navigates_when_pressed(tmp_path):
    app, a, b = screens_app(tmp_path)
    for _ in range(20):
        app.window.advance(16)
    assert app.current_screen.get() == "a"
    assert [a.node(f"root.r.item[{s}]").get("current") for s in "ab"] == ["page", False]
    assert a.node("root.r.item[a].pill").get("fill") == (a._scheme or tokens.BASELINE)["secondary_container"]
    a.window.simulate("click", node=a.node("root.r.item[b]"))
    for _ in range(6):
        app.window.advance(16)
    assert app.current_screen.get() == "b"
    assert [b.node(f"root.r.item[{s}]").get("current") for s in "ab"] == [False, "page"]


def test_a_screens_rail_is_the_same_look_and_has_a_badge(tmp_path):
    app, a, _ = screens_app(tmp_path)
    assert a.node("root.r").get("layout_width") == 80.0 and a.node("root.r.item[b].pill.badged.mark.label").get("text") == "2"


def test_an_expanded_screens_rail(tmp_path):
    app, a, _ = screens_app(tmp_path, "expanded: true")
    assert a.node("root.r").get("layout_width") == 220.0 and a.node("root.r.item[a].pill").get("layout_height") == 56.0


def test_one_screen_item_on_its_own(tmp_path):
    (tmp_path / "Views").mkdir()
    for name in ("a", "b"):
        (tmp_path / "Views" / f"{name.upper()}_View.yaml").write_text(
            f"name: {name}\nwidget: Container\nstyle: {{width: 200, height: 200}}\nchildren:\n  - {{widget: NavigationRailScreen, name: n, screen: b, label: Go, icon: home}}\n")
    app = App(root=tmp_path, width=200, height=200)
    app.bind(A)
    app.bind(B)
    a, b = app.open_view("A"), app.open_view("B")
    app.show("a")
    a.window.advance(16)
    assert a.node("root.n").get("current") is False
    a.window.simulate("click", node=a.node("root.n"))
    for _ in range(6):
        app.window.advance(16)
    assert app.current_screen.get() == "b" and b.node("root.n").get("current") == "page"


def test_an_expanded_rail_has_20_pixels_of_padding_and_44_above_the_first_destination(tmp_path):
    view, _ = opened(tmp_path, "expanded: true")
    home = item(view, "home")
    assert home.get("layout_x") == view.node("root.r").get("layout_x") + 20 and home.get("layout_y") == view.node("root.r").get("layout_y") + 44
