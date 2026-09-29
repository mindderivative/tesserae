"""M59 (#6): a declarative video. An `Image` takes a `frame` binding whose
value is `(rgba bytes, width, height)`; the view shows each new frame and
keeps the latest, so a re-theme or reconcile shows it too. The `Video`
fragment is that Image, blank until its `frame` binding gives it one.
Decoding stays the app's.
"""

import pytest
import yaml

import tesserae
from tesserae import Signal, View
from tesserae.spec import expand_components_to_spec
from tesserae.widgets import video

SEED = (0x67, 0x50, 0xA4, 0xFF)


def _frame(width, height, value):
    return (bytes([value, value, value, 255]) * (width * height), width, height)


class Player(tesserae.ViewModel):
    def __init__(self, view):
        self.frame = Signal(_frame(2, 2, 10))
        self.label = Signal("x")
        super().__init__(view)


def _image(**fields):
    return {"id": "screen", "kind": "Image", "image": {"fit": "fill"}, "style": {"width": 64, "height": 36}, **fields}


def _view(*nodes, **kwargs):
    view = View({"id": "root", "kind": "Container", "children": list(nodes)}, theme_seed=SEED, **kwargs)
    return view, Player(view)


def _shown(node):
    return node.get("rgba"), node.get("pixel_width"), node.get("pixel_height")


def test_a_frame_binding_shows_each_new_frame():
    view, player = _view(_image(bindings={"frame": "{{ frame.get() }}"}))
    node = view.node("screen")
    assert _shown(node) == _frame(2, 2, 10)
    player.frame.set(_frame(3, 1, 200))  # a new frame, a new size
    assert _shown(node) == _frame(3, 1, 200)
    player.frame.set(None)  # no frame yet: the last one stays
    assert _shown(node) == _frame(3, 1, 200)


def test_the_latest_frame_survives_a_re_theme_and_a_reconcile():
    spec = {"id": "root", "kind": "Container", "children": [_image(bindings={"frame": "{{ frame.get() }}"})]}
    view, player = _view(*spec["children"])
    player.frame.set(_frame(1, 1, 99))
    view.set_theme(theme_seed=SEED, dark=True)
    assert _shown(view.node("screen")) == _frame(1, 1, 99)
    changed = {**spec, "children": [_image(bindings={"frame": "{{ frame.get() }}"}, style={"width": 80, "height": 45})]}
    view.reconcile(changed)
    assert _shown(view.node("screen")) == _frame(1, 1, 99) and view.node("screen").get("width") == 80.0


def test_a_bad_frame_or_a_frame_on_something_else_is_named():
    view, player = _view(_image(bindings={"frame": "{{ frame.get() }}"}))
    with pytest.raises(ValueError, match=r'widget "screen" binding on "frame".*a 2x2 frame is 16 bytes of RGBA, got 4'):
        player.frame.set((bytes(4), 2, 2))
    with pytest.raises(ValueError, match="a frame is"):
        player.frame.set("not a frame")
    with pytest.raises(ValueError, match="only an Image takes a frame"):
        _view({"id": "t", "kind": "Rect", "style": {"width": 1, "height": 1, "background": "#000000"},
               "bindings": {"frame": "{{ frame.get() }}"}})


def test_the_video_fragment_with_and_without_a_frame_binding():
    spec = expand_components_to_spec(yaml.safe_dump({"id": "v", "component": "Video", "with": {
        "width": 64, "height": 36, "frame": "{{ frame.get() }}"}}))
    assert spec["bindings"] == {"frame": "{{ frame.get() }}"} and spec["kind"] == "Image"
    view = View({"id": "root", "kind": "Container", "children": [spec]}, theme_seed=SEED)
    player = Player(view)
    assert _shown(view.node("v")) == _frame(2, 2, 10) and view.node("v").get("a11y_hidden") is True
    player.frame.set(_frame(1, 1, 5))
    assert _shown(view.node("v")) == _frame(1, 1, 5)
    blank = expand_components_to_spec(yaml.safe_dump({"id": "v", "component": "Video",
                                                      "with": {"width": 64, "height": 36}}))
    assert "bindings" not in blank  # no frame: blank until code pushes one


def test_the_video_widget_shares_the_frame_check():
    import tre

    window = tre.Window(width=200, height=100)
    surface = video(window, 64, 36)
    surface.frame(*_frame(2, 1, 7))
    assert _shown(surface.node) == _frame(2, 1, 7)
    with pytest.raises(ValueError, match="a 2x2 frame is 16 bytes of RGBA, got 4"):
        surface.frame(bytes(4), 2, 2)
