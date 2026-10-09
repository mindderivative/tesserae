"""#124 to #128: the Material 3 split button -- a main action and a menu button, in five types."""

import pytest

from tesserae import App, Signal, ViewModel, tokens
from tesserae.shipped import shipped_views

ITEMS = "[{value: save, label: Save}, {value: copy, label: Save a copy}]"


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.chosen = Signal("")
        self.log = []

    def go(self):
        self.log.append("go")


def opened(tmp_path, props=""):
    (tmp_path / "Views").mkdir(exist_ok=True)
    lines = "\n    ".join(props.split(", ")) if props else ""
    (tmp_path / "Views" / "Main_View.yaml").write_text(f"""name: main
widget: Container
style: {{width: 500, height: 400, align_content: top_left}}
children:
  - widget: SplitButton
    name: sb
    label: Save
    items: {ITEMS}
    chosen: "{{{{ chosen }}}}"
    on_click: go
    {lines}
""")
    app = App(root=tmp_path, width=500, height=400)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    for _ in range(8):
        view.window.advance(16)
    return view, app.bindings.viewmodel_for("main")


def role(view, name):
    return (view._scheme or tokens.BASELINE)[name]


def settle(view, n=30):
    for _ in range(n):
        view.window.advance(16)


def main(view):
    return view.node("root.sb.main")


def trailing(view):
    return view.node("root.sb.trailing")


def test_it_is_shipped():
    assert "SplitButton" in shipped_views()


def test_the_two_parts_are_side_by_side_two_pixels_apart_and_as_tall_as_a_button(tmp_path):
    view, _ = opened(tmp_path)
    m, t = main(view), trailing(view)
    assert m.get("layout_height") == t.get("layout_height") == 40.0 and t.get("layout_x") == m.get("layout_x") + m.get("layout_width") + 2
    assert m.get("fill") == role(view, "primary") and t.get("fill") == role(view, "primary")


def test_the_inner_corners_are_small_and_the_outer_ones_round(tmp_path):
    view, _ = opened(tmp_path)
    assert main(view).get("corner_radius") == (9999.0, 4.0, 4.0, 9999.0)
    assert trailing(view).get("corner_radius") == (4.0, 9999.0, 9999.0, 4.0)


def test_pressing_the_main_part_runs_on_click_and_opens_no_menu(tmp_path):
    view, vm = opened(tmp_path)
    view.window.simulate("click", node=main(view))
    settle(view, 6)
    assert vm.log == ["go"] and not view._shown_layers


def test_pressing_the_trailing_part_opens_the_menu_under_it_and_flips_the_chevron(tmp_path):
    view, _ = opened(tmp_path)
    assert view._built.specs["root.sb.trailing.icon"]["icon"] == {"name": "chevron_down"} and trailing(view).get("expanded") is False
    view.window.simulate("click", node=trailing(view))
    settle(view, 8)
    assert view._shown_layers and view._built.specs["root.sb.trailing.icon"]["icon"] == {"name": "chevron_up"} and trailing(view).get("expanded") is True
    surface = view.node("root.sb.menu.surface")
    t = trailing(view)
    assert surface.get("layout_y") >= t.get("layout_y") + t.get("layout_height")
    settle(view, 30)
    assert trailing(view).get("corner_radius") == (9999.0,) * 4  # round on every corner while the menu is open


def test_choosing_a_row_sets_chosen_and_closes_the_menu_and_the_chevron_turns_back(tmp_path):
    view, vm = opened(tmp_path)
    view.window.simulate("click", node=trailing(view))
    settle(view, 8)
    view.window.simulate("click", node=view.node("root.sb.menu.surface.row[1].item"))
    settle(view, 8)
    assert vm.chosen.get() == "copy" and not view._shown_layers
    assert view._built.specs["root.sb.trailing.icon"]["icon"] == {"name": "chevron_down"}


def test_escape_closes_the_menu_and_it_can_be_opened_again(tmp_path):
    view, _ = opened(tmp_path)
    view.window.simulate("click", node=trailing(view))
    settle(view, 8)
    view.window.simulate("key_down", key="escape")
    settle(view, 8)
    assert not view._shown_layers
    view.window.simulate("click", node=trailing(view))
    settle(view, 8)
    assert view._shown_layers


@pytest.mark.parametrize("variant, fill", [("tonal", "secondary_container"), ("elevated", "surface_container_low"), ("filled", "primary")])
def test_the_variant_goes_to_both_parts(tmp_path, variant, fill):
    view, _ = opened(tmp_path, f"variant: {variant}")
    assert main(view).get("fill") == role(view, fill) and trailing(view).get("fill") == role(view, fill)


def test_outlined_and_text_parts(tmp_path):
    view, _ = opened(tmp_path, "variant: outlined")
    assert main(view).get("stroke_width") == 1.0 and trailing(view).get("stroke_width") == 1.0
    (tmp_path / "t").mkdir()
    text, _ = opened(tmp_path / "t", "variant: text")
    assert text.node("root.sb.main").get("fill")[3] == 0 and text.node("root.sb.main").get("stroke_width") == 0.0


def test_size_goes_to_both_parts(tmp_path):
    view, _ = opened(tmp_path, "size: m")
    assert main(view).get("layout_height") == 56.0 and trailing(view).get("layout_height") == 56.0


def test_an_icon_leads_the_main_part(tmp_path):
    view, _ = opened(tmp_path, "icon: home")
    assert "root.sb.main.icon" in view._built.specs


def test_a_disabled_split_button_does_not_respond_on_either_part(tmp_path):
    view, vm = opened(tmp_path, "disabled: true")
    view.window.simulate("click", node=main(view))
    view.window.simulate("click", node=trailing(view))
    settle(view, 6)
    assert vm.log == [] and not view._shown_layers and main(view).get("disabled") is True and trailing(view).get("disabled") is True


def test_the_trailing_part_is_named_for_a_screen_reader_and_says_whether_it_is_expanded(tmp_path):
    view, _ = opened(tmp_path)
    assert trailing(view).get("label") == "More options for Save" and trailing(view).get("role") == "button"


def test_both_parts_are_tab_stops(tmp_path):
    view, _ = opened(tmp_path)
    assert main(view).get("focusable") and trailing(view).get("focusable")
