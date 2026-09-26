"""M42 Phase 3: `image` and `video`, built by Tesserae (`window.create
("image")` with decoded pixels), off `tre`'s `add_image_from_bytes`,
`add_video` and `push_frame`, which 0.3.5 removes.
"""

from pathlib import Path

import pytest
import tre

from tesserae import Theme
from tesserae.images import decode_image
from tesserae.widgets import image, video

PIXEL_PNG = str(Path(__file__).parent / "fixtures" / "pixel.png")
SEED = (0x67, 0x50, 0xA4, 0xFF)


def _window():
    window = tre.Window(width=400, height=300)
    window.root.set(padding_top=0, padding_right=0, padding_bottom=0, padding_left=0, align_items="flex_start")
    return window


def test_an_image_shows_the_files_decoded_pixels():
    window = _window()
    im = image(window, PIXEL_PNG, 60, 40, fit="contain")
    window.advance(16)
    rgba, width, height = decode_image(PIXEL_PNG)
    assert (im.node.get("layout_width"), im.node.get("layout_height")) == (60.0, 40.0)
    assert (im.node.get("pixel_width"), im.node.get("pixel_height"), im.node.get("fit")) == (width, height, "contain")
    assert bytes(im.node.get("rgba")) == rgba
    assert im.node.parent() == window.root


def test_an_image_is_decorative_unless_labelled():
    window = _window()
    assert image(window, PIXEL_PNG, 10, 10).node.get("a11y_hidden") is True
    logo = image(window, PIXEL_PNG, 10, 10, label="Logo")
    assert (logo.node.get("role"), logo.node.get("label")) == ("img", "Logo")


def test_an_image_rejects_a_bad_fit_or_file():
    window = _window()
    with pytest.raises(ValueError, match="'cover', 'contain' or 'fill'"):
        image(window, PIXEL_PNG, 10, 10, fit="stretch")
    with pytest.raises(OSError):
        image(window, "does/not/exist.png", 10, 10)


def test_a_video_starts_blank_and_shows_frames():
    window = _window()
    v = video(window, 80, 60)
    window.advance(16)
    assert (v.node.get("pixel_width"), v.node.get("pixel_height")) == (1, 1)
    v.frame(bytes([10, 20, 30, 255] * 6), 3, 2)
    assert (v.node.get("pixel_width"), v.node.get("pixel_height")) == (3, 2)
    assert bytes(v.node.get("rgba"))[:4] == bytes([10, 20, 30, 255])
    v.frame(bytes([0, 0, 0, 255] * 16), 4, 4)  # frames can change size
    assert v.node.get("pixel_width") == 4


def test_a_video_frame_must_be_its_size_in_rgba():
    window = _window()
    v = video(window, 80, 60)
    with pytest.raises(ValueError, match="a 2x2 frame is 16 bytes of RGBA, got 12"):
        v.frame(bytes(12), 2, 2)


def test_a_re_colour_keeps_the_latest_video_frame():
    window = _window()
    v = video(window, 80, 60)
    v.frame(bytes([1, 2, 3, 255] * 4), 2, 2)
    v.set_theme(Theme.resolve(theme_seed=SEED))
    assert (v.node.get("pixel_width"), v.node.get("pixel_height")) == (2, 2)
    assert bytes(v.node.get("rgba"))[:4] == bytes([1, 2, 3, 255])
