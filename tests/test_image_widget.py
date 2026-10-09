"""#196: `widget: Image` -- alt text, fit, shape from `corner_radius`, and a source that follows a Signal."""

import pytest
from PIL import Image

from tesserae import App, Signal, ViewModel


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.picture = Signal("red.png")
        self.clicked = Signal(0)


def make(tmp_path, name, color, size=(8, 8)):
    Image.new("RGBA", size, color).save(tmp_path / "Views" / name)


def opened(tmp_path, body, files=(("red.png", (255, 0, 0, 255)),)):
    (tmp_path / "Views").mkdir(exist_ok=True)
    for name, color in files:
        make(tmp_path, name, color)
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        "name: main\nwidget: Container\nstyle: {flex_direction: vertical, align_content: top_left, width: 100, height: 100}\nchildren:\n" + body)
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    view.window.advance(16)
    return view, app.bindings.viewmodel_for("main")


def alpha_at(view, node, x, y):
    """The picture's alpha `x`, `y` pixels in from the picture's own top-left corner."""
    rgba, width, height = view.window.snapshot()
    pts = [(px, py) for py in range(height) for px in range(width) if rgba[(py * width + px) * 4 + 3] > 0]
    x0, y0 = min(p[0] for p in pts), min(p[1] for p in pts)
    return rgba[((y0 + y) * width + x0 + x) * 4 + 3]


def test_a_picture_with_alt_is_an_image_for_a_screen_reader(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: Image, name: i, src: red.png, alt: A red square, style: {width: 40, height: 40}}\n")
    node = view.node("root.i")
    assert node.get("role") == "img" and node.get("label") == "A red square" and not node.get("a11y_hidden")


def test_a_picture_without_alt_is_decorative(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: Image, name: i, src: red.png, style: {width: 40, height: 40}}\n")
    assert view.node("root.i").get("a11y_hidden") is True


def test_a_picture_that_is_pressed_is_not_hidden(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: Image, name: i, src: red.png, style: {width: 40, height: 40}, handlers: {on_click: 'clicked += 1'}}\n")
    assert not view.node("root.i").get("a11y_hidden")


def test_a11y_on_the_node_beats_alt(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: Image, name: i, src: red.png, alt: Plain, a11y: {label: Better}, style: {width: 40, height: 40}}\n")
    assert view.node("root.i").get("label") == "Better" and view.node("root.i").get("role") == "img"


@pytest.mark.parametrize("fit", ["cover", "contain", "fill"])
def test_fit_is_passed_to_the_picture(tmp_path, fit):
    view, _ = opened(tmp_path, f"  - {{widget: Image, name: i, src: red.png, fit: {fit}, style: {{width: 40, height: 20}}}}\n")
    assert view.node("root.i").get("fit") == fit


def test_a_fit_that_is_not_one_is_a_load_error(tmp_path):
    from tesserae.spec.nodes import LoadError

    with pytest.raises(LoadError, match=r"Main_View.yaml:\d+:\d+.*fit.*cover, contain, fill"):
        opened(tmp_path, "  - {widget: Image, name: i, src: red.png, fit: stretch}\n")


def test_corner_radius_is_the_pictures_shape(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: Image, name: i, src: red.png, style: {width: 40, height: 40, corner_radius: full}}\n")
    node = view.node("root.i")
    assert alpha_at(view, node, 20, 20) == 255 and alpha_at(view, node, 1, 1) == 0 and alpha_at(view, node, 38, 38) == 0  # a circle


def test_each_corner_can_have_its_own_radius(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: Image, name: i, src: red.png, style: {width: 40, height: 40, corner_radius: {top_left: 20}}}\n")
    node = view.node("root.i")
    assert alpha_at(view, node, 1, 1) == 0 and alpha_at(view, node, 38, 1) == 255 and alpha_at(view, node, 1, 38) == 255


def test_a_plain_picture_is_square(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: Image, name: i, src: red.png, style: {width: 40, height: 40}}\n")
    node = view.node("root.i")
    assert alpha_at(view, node, 1, 1) == 255 and alpha_at(view, node, 38, 38) == 255


def test_the_source_follows_a_signal(tmp_path):
    view, vm = opened(tmp_path, "  - {widget: Image, name: i, src: '{{ picture }}', style: {width: 4, height: 4}}\n",
                      files=(("red.png", (255, 0, 0, 255)), ("blue.png", (0, 0, 255, 255))))
    pixel = lambda: tuple(view.node("root.i").get("rgba")[:4])  # noqa: E731
    assert pixel() == (255, 0, 0, 255)
    vm.picture.set("blue.png")
    view.window.advance(16)
    assert pixel() == (0, 0, 255, 255)


def test_a_missing_file_says_which_widget_and_which_file(tmp_path):
    with pytest.raises(Exception, match=r"i.*nowhere\.png|nowhere\.png.*i"):
        opened(tmp_path, "  - {widget: Image, name: i, src: nowhere.png, style: {width: 4, height: 4}}\n")


def test_it_matches_the_python_widgets_picture(tmp_path):
    from tesserae.widgets import image

    view, _ = opened(tmp_path, "  - {widget: Image, name: i, src: red.png, fit: contain, style: {width: 30, height: 20}}\n")
    py_app = App(width=100, height=100)
    py = image(py_app.window, str(tmp_path / "Views" / "red.png"), 30, 20, fit="contain")
    for prop in ("fit", "pixel_width", "pixel_height"):
        assert py.node.get(prop) == view.node("root.i").get(prop), prop
    assert py.node.get("rgba")[:4] == view.node("root.i").get("rgba")[:4]
