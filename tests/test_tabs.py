"""#166, #167: the Material 3 tab bar -- primary and secondary, an indicator that slides, arrows that move and choose, badges and icons."""

import pytest

from tesserae import App, Signal, ViewModel, tokens
from tesserae.shipped import shipped_views

TABS = "[{value: flights, label: Flights, icon: home}, {value: trips, label: Trips, icon: search, badge: 3}, {value: explore, label: Explore, icon: menu}]"
PLAIN = "[{value: a, label: One}, {value: b, label: Two}, {value: c, label: Three}]"


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.tab = Signal("trips")
        self.plain = Signal("a")


def opened(tmp_path, widget, **kwargs):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        "name: main\nwidget: Container\nstyle: {flex_direction: vertical, align_content: top_left, width: 500, height: 300}\nchildren:\n" + widget)
    app = App(root=tmp_path, **kwargs)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    for _ in range(3):
        view.window.advance(16)
    return view, app.bindings.viewmodel_for("main")


ICONS = f'  - {{widget: Tabs, name: t, tabs: {TABS}, selected: "{{{{ tab }}}}"}}\n'
BARE = f'  - {{widget: Tabs, name: t, tabs: {PLAIN}, selected: "{{{{ plain }}}}"}}\n'


def tab(view, value, node="t"):
    return view.node(f"root.{node}.bar.tab[{value}]")


def indicator(view, node="t"):
    return view.node(f"root.{node}.bar.indicator")


def role(view, name):
    return (view._scheme or tokens.BASELINE)[name]


def settle(view):
    for _ in range(40):
        view.window.advance(16)


def click(view, value):
    view.window.simulate("click", node=tab(view, value))
    settle(view)


def test_it_is_shipped():
    assert "Tabs" in shipped_views()


def test_a_bar_of_equal_tabs_over_a_divider(tmp_path):
    view, _ = opened(tmp_path, BARE)
    xs = [tab(view, v).get("layout_x") for v in "abc"]
    assert xs == [xs[0], xs[0] + 120, xs[0] + 240] and tab(view, "a").get("layout_width") == 120.0
    assert view.node("root.t.bar").get("layout_height") == 48.0
    assert view.node("root.t.divider").get("layout_y") == view.node("root.t.bar").get("layout_y") + 48.0
    assert view.node("root.t.bar").get("role") == "tablist"


def test_icons_make_the_bar_sixty_four_tall(tmp_path):
    view, _ = opened(tmp_path, ICONS)
    assert view.node("root.t.bar").get("layout_height") == 64.0


def test_the_selected_tab_is_primary_and_the_rest_on_surface_variant(tmp_path):
    view, _ = opened(tmp_path, BARE)
    assert view.node("root.t.bar.tab[a].label").get("fill") == role(view, "primary")
    assert view.node("root.t.bar.tab[b].label").get("fill") == role(view, "on_surface_variant")
    assert view.node("root.t.bar.tab[a].label").get("font_size") == 14.0


def test_each_tab_is_a_tab_that_knows_if_it_is_selected(tmp_path):
    view, _ = opened(tmp_path, BARE)
    assert [tab(view, v).get("role") for v in "abc"] == ["tab"] * 3
    assert [tab(view, v).get("selected") for v in "abc"] == [True, False, False]
    assert tab(view, "b").get("label") == "Two"


def test_the_primary_indicator_is_three_tall_rounded_on_top_and_under_the_selected_tab(tmp_path):
    view, _ = opened(tmp_path, BARE)
    ind = indicator(view)
    assert ind.get("layout_height") == 3.0 and ind.get("fill") == role(view, "primary")
    assert ind.get("corner_radius") == (3.0, 3.0, 0.0, 0.0)
    assert ind.get("layout_x") == tab(view, "a").get("layout_x") + 12 and ind.get("layout_width") == 96.0
    assert ind.get("layout_y") == view.node("root.t.bar").get("layout_y") + 46


def test_the_secondary_indicator_is_two_tall_across_the_whole_tab(tmp_path):
    view, _ = opened(tmp_path, BARE.replace("}\n", ", variant: secondary}\n"))
    ind = indicator(view)
    assert ind.get("layout_height") == 2.0 and ind.get("layout_width") == 120.0 and ind.get("layout_x") == tab(view, "a").get("layout_x")
    assert ind.get("corner_radius") == 0.0


def test_pressing_a_tab_chooses_it_and_the_indicator_slides_there(tmp_path):
    view, vm = opened(tmp_path, BARE)
    start = indicator(view).get("layout_x")
    view.window.simulate("click", node=tab(view, "c"))
    for _ in range(6):
        view.window.advance(16)
    assert vm.plain.get() == "c" and start < indicator(view).get("layout_x") < start + 240  # on its way
    settle(view)
    assert indicator(view).get("layout_x") == start + 240 and view.node("root.t.bar.tab[c].label").get("fill") == role(view, "primary")


def test_the_indicator_follows_a_signal_too(tmp_path):
    view, vm = opened(tmp_path, BARE)
    vm.plain.set("b")
    settle(view)
    assert indicator(view).get("layout_x") == tab(view, "b").get("layout_x") + 12


def test_a_value_that_is_no_tab_puts_the_indicator_on_the_first(tmp_path):
    view, vm = opened(tmp_path, BARE)
    vm.plain.set("nope")
    settle(view)
    assert indicator(view).get("layout_x") == tab(view, "a").get("layout_x") + 12


def test_the_arrows_move_the_focus_along_the_bar_and_choose_the_tab(tmp_path):
    view, vm = opened(tmp_path, BARE)
    assert [tab(view, v).get("tab_index") for v in "abc"] == [0, -1, -1]
    tab(view, "a").focus()
    view.window.simulate("key_down", key="arrow_right")
    settle(view)
    assert vm.plain.get() == "b"
    view.window.simulate("key_down", key="End")
    settle(view)
    assert vm.plain.get() == "c"
    view.window.simulate("key_down", key="Home")
    settle(view)
    assert vm.plain.get() == "a"


def test_an_icon_and_a_badge_sit_in_the_tab(tmp_path):
    view, _ = opened(tmp_path, ICONS)
    assert view.node("root.t.bar.tab[flights].icon").get("fill") == role(view, "on_surface_variant")
    assert view.node("root.t.bar.tab[trips].badged.mark.label").get("text") == "3"
    assert view.node("root.t.bar.tab[trips].badged.badged_icon").get("fill") == role(view, "primary")
    assert "root.t.bar.tab[trips].icon" not in view._built.specs


def test_a_tab_width_sets_every_tab(tmp_path):
    view, _ = opened(tmp_path, BARE.replace("}\n", ", tab_width: 90}\n"))
    assert tab(view, "b").get("layout_width") == 90.0 and indicator(view).get("layout_width") == 66.0


def test_tabs_can_change(tmp_path):
    class Dynamic(ViewModel):
        views = "main"

        def __init__(self):
            super().__init__()
            self.tabs = Signal([{"value": "a", "label": "A"}, {"value": "b", "label": "B"}])

    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        "name: main\nwidget: Container\nstyle: {width: 500, height: 200}\nchildren:\n  - {widget: Tabs, name: t, tabs: \"{{ tabs }}\", selected: b}\n")
    app = App(root=tmp_path)
    app.bind(Dynamic)
    view = app.open_view("Main")
    app.show("main")
    view.window.advance(16)
    app.bindings.viewmodel_for("main").tabs.set([{"value": "a", "label": "A"}, {"value": "b", "label": "B"}, {"value": "c", "label": "C"}])
    settle(view)
    assert tab(view, "c").get("layout_x") == tab(view, "a").get("layout_x") + 240


def test_a_panel_is_the_viewers_to_switch(tmp_path):
    view, vm = opened(tmp_path, BARE + '  - {widget: Container, name: pa, if: "plain == \'a\'", style: {width: 10, height: 10}}\n'
                                       '  - {widget: Container, name: pb, if: "plain == \'b\'", style: {width: 10, height: 10}}\n')
    assert "root.pa" in view._built.specs and "root.pb" not in view._built.specs
    click(view, "b")
    assert "root.pb" in view._built.specs and "root.pa" not in view._built.specs
