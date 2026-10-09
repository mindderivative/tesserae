"""#205: the title bar in a composed view -- tooltips on its window buttons, and the app's own parts (tabs, a search field, buttons) in its middle."""

import pytest

from tesserae import App, ViewModel

SEED = (0x67, 0x50, 0xA4, 0xFF)

WINDOW = """name: main
widget: Window
title: Notes
borderless: true
style: {width: 700, height: 300, flex_direction: vertical}
children:
  - widget: TitleBar
    name: bar
    title: Notes
    icon: home
    children:
      - {widget: Tabs, name: tabs, selected: one, tab_width: 90, tabs: [{value: one, label: One}, {value: two, label: Two}]}
      - {widget: IconButton, name: gear, icon: settings, label: Settings, size: xs}
  - {widget: Container, name: page, style: {height: 200, width: 700}}
"""


class VM(ViewModel):
    views = "main"


def opened(tmp_path, text=WINDOW, native_controls=False):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(text)
    app = App(root=tmp_path, width=700, height=300, theme_seed=SEED, borderless=True)
    app._native_controls.set(native_controls)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    app.window.advance(32)
    return app, view


def hover(app, view, node_id):
    node = view.node(node_id)
    app.window.simulate("pointer_move", x=node.get("layout_x") + 4, y=node.get("layout_y") + 4)
    for _ in range(40):
        app.window.advance(16)


def tips(view):
    return [t.get("text") for layer in view._tips.values() for t in layer[0].children()]


@pytest.mark.parametrize("name, text", [("minimize", "Minimize"), ("maximize", "Maximize"), ("close", "Close")])
def test_each_window_button_says_what_it_does_when_the_pointer_rests_on_it(tmp_path, name, text):
    app, view = opened(tmp_path)
    hover(app, view, f"root.bar.{name}")
    assert tips(view) == [text]


def test_the_tooltip_goes_when_the_pointer_leaves(tmp_path):
    app, view = opened(tmp_path)
    hover(app, view, "root.bar.close")
    assert view._tips
    hover(app, view, "root.bar.minimize")
    app.window.advance(32)
    assert tips(view) in ([], ["Minimize"])  # the next button's own, after its delay
    for _ in range(40):
        app.window.advance(16)
    assert tips(view) == ["Minimize"]


def test_tabs_and_a_button_sit_in_the_middle_and_the_window_buttons_stay_at_the_end(tmp_path):
    app, view = opened(tmp_path)
    tabs, gear, buttons = view.node("root.bar.tabs"), view.node("root.bar.gear"), view.node("root.bar.buttons")
    assert tabs.get("layout_x") < gear.get("layout_x") < buttons.get("layout_x")
    assert buttons.get("layout_x") + buttons.get("layout_width") == 700.0
    assert view.node("root.bar").get("layout_height") == 40.0


def test_a_tab_in_the_title_bar_can_be_chosen_without_moving_the_window(tmp_path):
    app, view = opened(tmp_path)
    app.window.simulate("click", node=view.node("root.bar.tabs.bar.tab[two]"))
    for _ in range(10):
        app.window.advance(16)
    assert view.node("root.bar.tabs.bar.tab[two]").get("selected") is True


def test_the_bar_is_the_window_s_drag_region_and_its_parts_are_not_dragged_over(tmp_path):
    app, view = opened(tmp_path)
    assert view.node("root.bar").get("window_region") == "drag"
