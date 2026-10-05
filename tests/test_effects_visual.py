"""#90: what the effects look like, read back from the window's headless snapshot (`window.snapshot()`)."""

import yaml

from tesserae import App, View

SEED = (0x67, 0x50, 0xA4, 0xFF)


def _render(children, **app_args):
    spec = yaml.safe_load("id: root\nkind: Container\nstyle: {width: 300, height: 120, background: '#000000'}\nchildren: []")
    spec["children"] = children
    app = App(width=300, height=120, theme_seed=SEED, dark=True, **app_args)
    view = View(spec, window=app.window)
    app.window.root.add_child(view.root)
    app.window.advance(32)
    rgba, width, height = app.window.snapshot()
    return lambda x, y: tuple(rgba[(y * width + x) * 4:(y * width + x) * 4 + 4])


def _rect(id, x, y, w, h, **style):
    return {"id": id, "kind": "Rect", "style": {"position": "absolute", "x": x, "y": y, "width": w, "height": h, **style}}


def test_a_linear_gradient_goes_from_one_colour_to_the_other():
    pixel = _render([_rect("g", 0, 0, 300, 40, background="linear-gradient(90deg, #ff0000, #0000ff)")])
    left, right = pixel(5, 20), pixel(294, 20)
    assert left[0] > 200 and left[2] < 50
    assert right[2] > 200 and right[0] < 50


def test_a_vertical_gradient_changes_down_not_across():
    pixel = _render([_rect("g", 0, 0, 300, 100, background="linear-gradient(180deg, #ffffff, #000000)")])
    assert pixel(150, 5)[0] > 200 > 50 > pixel(150, 94)[0]
    assert abs(pixel(5, 50)[0] - pixel(290, 50)[0]) < 4


def test_a_filter_greys_a_colour():
    pixel = _render([_rect("g", 0, 0, 100, 40, background="#ff0000", filter={"grayscale": 1.0})])
    r, g, b, _ = pixel(50, 20)
    assert abs(r - g) < 6 and abs(g - b) < 6


def test_a_blend_mode_changes_what_is_behind():
    plain = _render([_rect("a", 0, 0, 100, 40, background="#808080"),
                     _rect("b", 0, 0, 100, 40, background="#808080")])(50, 20)
    multiplied = _render([_rect("a", 0, 0, 100, 40, background="#808080"),
                          _rect("b", 0, 0, 100, 40, background="#808080", blend_mode="multiply")])(50, 20)
    assert multiplied[0] < plain[0] - 30


def test_a_backdrop_blur_softens_what_is_behind_it():
    stripes = [_rect("l", 0, 0, 150, 60, background="#ffffff"), _rect("r", 150, 0, 150, 60, background="#000000"),
               _rect("glass", 100, 0, 100, 60, background="#00000001", backdrop_blur=16)]
    pixel = _render(stripes)
    assert 20 < pixel(150, 30)[0] < 235  # the hard edge at x=150 is a ramp under the glass
    assert pixel(20, 30)[0] > 250
