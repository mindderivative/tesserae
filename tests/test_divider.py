"""#152: the Material 3 divider -- `widget: Divider`, a shipped view with a shipped look."""

import pytest

from tesserae import App, ViewModel, tokens
from tesserae.shipped import shipped_rules, shipped_views


class VM(ViewModel):
    views = "main"


def opened(tmp_path, body, row=False):
    direction = "horizontal" if row else "vertical"
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        f"name: main\nwidget: Container\nstyle: {{flex_direction: {direction}, width: 300, height: 200}}\nchildren:\n" + body)
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    view.window.advance(16)
    return view


def line(view, name="d"):
    return view.node(f"root.{name}")


def role(view, name):
    return (view._scheme or tokens.BASELINE)[name]


def test_the_divider_is_shipped_with_its_look():
    assert "Divider" in shipped_views() and any(rule.widget == "Divider" for sheet in shipped_rules() for rule in sheet.rules)


def test_a_horizontal_divider_is_a_one_pixel_line_across_the_width(tmp_path):
    view = opened(tmp_path, "  - {widget: Divider, name: d}\n")
    d = line(view)
    assert (d.get("layout_width"), d.get("layout_height"), d.get("layout_x")) == (300.0, 1.0, 0.0)
    assert d.get("fill") == role(view, "outline_variant")


def test_a_vertical_divider_is_a_one_pixel_line_down_the_height(tmp_path):
    view = opened(tmp_path, "  - {widget: Divider, name: d, orientation: vertical}\n", row=True)
    d = line(view)
    assert (d.get("layout_width"), d.get("layout_height"), d.get("layout_y")) == (1.0, 200.0, 0.0)


def test_thickness_is_a_property(tmp_path):
    view = opened(tmp_path, "  - {widget: Divider, name: d, thickness: 4}\n")
    assert line(view).get("layout_height") == 4.0


def test_an_inset_divider_keeps_16_clear_of_the_start(tmp_path):
    view = opened(tmp_path, "  - {widget: Divider, name: d, variant: inset}\n")
    d = line(view)
    assert (d.get("layout_x"), d.get("layout_width")) == (16.0, 284.0)


def test_a_middle_inset_divider_keeps_16_clear_of_both_ends(tmp_path):
    view = opened(tmp_path, "  - {widget: Divider, name: d, variant: middle}\n")
    d = line(view)
    assert (d.get("layout_x"), d.get("layout_width")) == (16.0, 268.0)


def test_the_inset_of_a_vertical_divider_is_at_the_top(tmp_path):
    view = opened(tmp_path, "  - {widget: Divider, name: d, orientation: vertical, variant: middle}\n", row=True)
    d = line(view)
    assert (d.get("layout_y"), d.get("layout_height")) == (16.0, 168.0)


def test_it_is_hidden_from_a_screen_reader_and_cannot_be_tabbed_to(tmp_path):
    view = opened(tmp_path, "  - {widget: Divider, name: d}\n")
    d = line(view)
    assert d.get("a11y_hidden") is True and not d.get("focusable")


def test_a_divider_between_rows_separates_them(tmp_path):
    view = opened(tmp_path, "  - {widget: Container, name: a, style: {height: 20}}\n  - {widget: Divider, name: d}\n"
                            "  - {widget: Container, name: b, style: {height: 20}}\n")
    assert line(view, "a").get("layout_y") + 20 == line(view).get("layout_y") and line(view).get("layout_y") + 1 == line(view, "b").get("layout_y")


def test_the_app_can_restyle_it_and_a_call_can_override_the_colour(tmp_path):
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        "name: main\nwidget: Container\nstyle: {flex_direction: vertical, width: 300, height: 200}\nchildren:\n"
        "  - {widget: Divider, name: a}\n  - {widget: Divider, name: b, style: {background: '#FF0000'}}\n")
    app = App(root=tmp_path, stylesheet_spec={"styles": [{"widget": "Divider", "style": {"background": "#00FF00"}}]})
    app.bind(VM)
    view = app.open_view("Main")
    assert line(view, "a").get("fill") == (0, 255, 0, 255) and line(view, "b").get("fill") == (255, 0, 0, 255)


@pytest.mark.parametrize("body, message", [
    ("  - {widget: Divider, variant: wide}\n", "variant"), ("  - {widget: Divider, orientation: diagonal}\n", "orientation"),
    ("  - {widget: Divider, thickness: thick}\n", "thickness"),
])
def test_a_wrong_property_is_a_load_error(tmp_path, body, message):
    with pytest.raises(Exception, match=message):
        opened(tmp_path, body)


@pytest.mark.parametrize("orientation", ["horizontal", "vertical"])
def test_it_matches_the_python_widgets_look(tmp_path, orientation):
    """The Python `divider` and `widget: Divider` draw the same line: its colour and its thickness."""
    from tesserae.widgets import divider

    py_app = App(width=300, height=200)
    py = divider(py_app.window, 100, orientation=orientation)
    py_app.window.advance(16)
    view = opened(tmp_path, f"  - {{widget: Divider, name: d, orientation: {orientation}}}\n", row=orientation == "vertical")
    d = line(view)
    assert py.node.get("fill") == d.get("fill")
    thin = "layout_height" if orientation == "horizontal" else "layout_width"
    assert py.node.get(thin) == d.get(thin) == 1.0
