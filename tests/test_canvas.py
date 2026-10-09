"""#215: `Canvas`, drawing as data -- rects, circles and paths from a `draw:` list, following the Signals it reads."""

import pytest
import yaml

from tesserae import App, Signal, ViewModel, tokens
from tesserae.spec.canvas import plan
from tesserae.spec.nodes import LoadError


class Recorder:
    """Stands in for tre's Painter: what a canvas's draw callback asked it to paint."""

    def __init__(self):
        self.calls = []

    def fill_rect(self, *a):
        self.calls.append(("rect", *a))

    def fill_circle(self, *a):
        self.calls.append(("circle", *a))

    def stroke_path(self, *a):
        self.calls.append(("path", *a))


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.x = Signal(10)


def opened(tmp_path, canvas):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        "name: main\nwidget: Container\nstyle: {flex_direction: vertical, width: 200, height: 100}\nchildren:\n" + canvas)
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    return view, app.bindings.viewmodel_for("main")


def painted(view, name="root.c"):
    rec = Recorder()
    view.node(name).get("draw")(rec)
    return rec.calls


def test_a_canvas_paints_its_commands_in_order_with_theme_colours(tmp_path):
    view, _ = opened(tmp_path, "  - widget: Canvas\n    name: c\n    style: {width: 100, height: 40}\n    draw:\n"
                               "      - {rect: [0, 1, 20, 4], color: primary}\n      - {circle: [5, 6, 3], color: '#FF0000'}\n"
                               "      - {path: [[0, 0], [10, 10], [20, 0, 30, 10]], color: primary@50%, width: 2}\n")
    primary = (view._scheme or tokens.BASELINE)["primary"]
    rect, circle, path = painted(view)
    assert rect == ("rect", 0.0, 1.0, 20.0, 4.0, primary)
    assert circle == ("circle", 5.0, 6.0, 3.0, (255, 0, 0, 255))
    assert path[:2] == ("path", [[0.0, 0.0], [10.0, 10.0], [20.0, 0.0, 30.0, 10.0]]) and path[3] == 2.0
    assert path[2][:3] == primary[:3] and path[2][3] == round(primary[3] * 0.5)
    assert view.node("root.c").get("layout_width") == 100


def test_a_canvas_redraws_when_a_signal_it_reads_changes(tmp_path):
    view, vm = opened(tmp_path, "  - widget: Canvas\n    name: c\n    style: {width: 100, height: 40}\n"
                                "    draw: \"{{ [{'circle': [x, 5, 2], 'color': 'primary'}] }}\"\n")
    assert painted(view)[0][1] == 10.0
    vm.x.set(40)
    view.window.advance(16)
    assert painted(view)[0][1] == 40.0


@pytest.mark.parametrize("draw, message", [
    ("{}", "draw is a list of commands"),
    ("[3]", r"draw\[0\] is a mapping"),
    ("[{color: primary}]", "needs exactly one of rect, circle, path"),
    ("[{rect: [0, 0, 1, 1], circle: [0, 0, 1], color: primary}]", "needs exactly one of"),
    ("[{rect: [0, 0, 1, 1]}]", "rect needs a color"),
    ("[{rect: [0, 0, 1], color: primary}]", r"draw\[0\].rect is 4 numbers"),
    ("[{circle: [0, 0, true], color: primary}]", r"draw\[0\].circle is 3 numbers"),
    ("[{rect: [0, 0, 1, 1], color: primary, width: 2}]", "rect takes color, rect"),
    ("[{path: [[0, 0]], color: primary}]", "path is two or more points"),
    ("[{path: [[0, 0], [1, 2, 3]], color: primary}]", r"path\[1\] is 2 or 4 or 6 numbers"),
    ("[{path: [[0, 0, 1], [1, 2]], color: primary}]", r"path\[0\] is 2 numbers"),
    ("[{path: [[0, 0], [1, 2]], color: primary, width: 0}]", "width is a number above 0"),
])
def test_a_bad_command_names_the_widget_and_the_command(draw, message):
    with pytest.raises(ValueError, match=message):
        plan(yaml.safe_load(draw), lambda c: (0, 0, 0, 255))


def test_a_bad_colour_is_a_build_error(tmp_path):
    with pytest.raises(Exception, match="nonsense"):
        opened(tmp_path, "  - {widget: Canvas, name: c, draw: [{rect: [0, 0, 1, 1], color: nonsense}]}\n")


def test_a_canvas_with_nothing_to_draw_draws_nothing(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: Canvas, name: c, style: {width: 10, height: 10}}\n")
    assert painted(view) == []


def test_the_view_language_rejects_a_draw_that_is_not_a_list():
    from tesserae.spec.nodes import parse_view
    with pytest.raises(LoadError):
        parse_view("widget: Canvas\ndraw: 3\n", "T_View.yaml")


def test_a_path_is_one_pixel_wide_unless_it_says_otherwise():
    assert plan([{"path": [[0, 0], [1, 1]], "color": "primary"}], lambda c: (1, 2, 3, 4)) == [("path", [[0.0, 0.0], [1.0, 1.0]], (1, 2, 3, 4), 1.0)]
