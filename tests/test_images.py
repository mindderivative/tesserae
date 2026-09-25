"""M29 Phase 2: Tesserae decodes images itself (Pillow) and hands `tre`
only RGBA bytes -- `tre` never opens an image file.

`tre` has no API to read an image node's pixels back, so this covers
the decode and extraction steps directly, proves (by wrapping `tre`'s
entry points) that no `src:` or file path reaches `tre`, and loads real
views end to end -- `push_frame` rejects a frame whose byte length
doesn't match its size, so a clean load means `tre` accepted the frame.
"""

import importlib.util
import sys
from pathlib import Path

import pytest
import tre
from PIL import Image

from tesserae import View, instantiate
from tesserae.images import decode_image
from tesserae.spec import ComponentError, load_view
from tesserae.spec.images import extract_images

RED_BLUE = b"\xff\x00\x00\xff" + b"\x00\x00\xff\xff"


def _png(path: Path, mode: str = "RGB", size=(2, 1), pixels=((255, 0, 0), (0, 0, 255))) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new(mode, size)
    img.putdata(list(pixels))
    img.save(path)
    return path


# -- decode_image ------------------------------------------------------


def test_decode_image_returns_straight_rgba_bytes_and_pixel_size(tmp_path: Path):
    rgba, width, height = decode_image(_png(tmp_path / "rb.png"))
    assert (width, height) == (2, 1)
    assert rgba == RED_BLUE


def test_decode_image_converts_non_rgba_modes(tmp_path: Path):
    # Greyscale+alpha in, RGBA out: 4 bytes per pixel, alpha preserved.
    path = _png(tmp_path / "la.png", mode="LA", size=(1, 1), pixels=((128, 64),))
    rgba, width, height = decode_image(path)
    assert (width, height, rgba) == (1, 1, b"\x80\x80\x80\x40")


def test_decode_image_missing_file_raises_oserror_naming_it(tmp_path: Path):
    with pytest.raises(OSError, match="nope.png"):
        decode_image(tmp_path / "nope.png")


def test_decode_image_corrupt_file_raises_oserror(tmp_path: Path):
    bad = tmp_path / "bad.png"
    bad.write_bytes(b"not an image")
    with pytest.raises(OSError, match="bad.png"):
        decode_image(bad)


# -- extract_images ----------------------------------------------------


def _image_node(node_id="img", src="rb.png", fit="cover"):
    return {"id": node_id, "kind": "Image", "image": {"src": src, "fit": fit}}


def test_extract_images_strips_src_keeps_fit_and_decodes(tmp_path: Path):
    _png(tmp_path / "rb.png")
    spec = {"id": "root", "kind": "Container", "children": [_image_node()]}

    stripped, frames = extract_images(spec, tmp_path)

    assert stripped["children"][0]["image"] == {"fit": "cover"}
    assert frames == [("img", RED_BLUE, 2, 1)]
    assert spec["children"][0]["image"]["src"] == "rb.png"  # input not modified


def test_extract_images_finds_nested_images_and_leaves_others_alone(tmp_path: Path):
    _png(tmp_path / "rb.png")
    blank = {"id": "blank", "kind": "Image", "image": {"fit": "fill"}}
    spec = {
        "id": "root",
        "kind": "Container",
        "children": [
            {"id": "row", "kind": "Container", "children": [_image_node("deep")]},
            blank,
            {"id": "label", "kind": "Text", "text": {"content": "src"}},
        ],
    }
    stripped, frames = extract_images(spec, tmp_path)
    assert [f[0] for f in frames] == ["deep"]
    assert stripped["children"][1] == blank
    assert stripped["children"][2] == spec["children"][2]


@pytest.mark.parametrize(
    "src, match",
    [
        ("missing.png", "cannot read"),
        ("../outside.png", "resolves outside the view directory"),
    ],
)
def test_extract_images_rejects_unreadable_or_escaping_paths(tmp_path: Path, src, match):
    _png(tmp_path / "outside.png")
    app = tmp_path / "app"
    app.mkdir()
    with pytest.raises(ComponentError, match=match):
        extract_images(_image_node(src=src), app)


def test_extract_images_rejects_absolute_paths(tmp_path: Path):
    target = _png(tmp_path / "rb.png")
    with pytest.raises(ComponentError, match="must be a relative path"):
        extract_images(_image_node(src=str(target)), tmp_path)


def test_extract_images_needs_a_base_directory():
    with pytest.raises(ComponentError, match="no base directory"):
        extract_images(_image_node(), None)


def test_extract_images_undecodable_file_names_the_widget(tmp_path: Path):
    (tmp_path / "rb.png").write_bytes(b"not an image")
    with pytest.raises(ComponentError, match=r"widget 'img': cannot decode image"):
        extract_images(_image_node(), tmp_path)


# -- end to end --------------------------------------------------------

IMAGE_FRAGMENT_VIEW = """
id: root
kind: Container
style: {width: 200, height: 200}
children:
  - id: img
    component: Image
    with: {src: assets/rb.png, width: 100, height: 100, fit: cover}
"""


def test_load_view_decodes_images_into_image_nodes(tmp_path: Path):
    """Tesserae decodes the file and builds its pixels into a `tre`
    `image` node (M37); `tre` is given no path."""
    _png(tmp_path / "assets" / "rb.png")
    view_path = tmp_path / "Gallery_View.yaml"
    view_path.write_text(IMAGE_FRAGMENT_VIEW)
    node = load_view(view_path).node("img")
    rgba, width, height = decode_image(tmp_path / "assets" / "rb.png")
    assert (node.get("pixel_width"), node.get("pixel_height"), node.get("fit")) == (width, height, "cover")
    assert node.get("rgba") == rgba


def test_load_view_decodes_a_hand_written_image_too(tmp_path: Path):
    _png(tmp_path / "rb.png")
    view_path = tmp_path / "Hand_View.yaml"
    view_path.write_text(
        "id: root\nkind: Container\nchildren:\n"
        "  - {id: pic, kind: Image, image: {src: rb.png}, style: {width: 20, height: 10}}\n"
    )
    assert load_view(view_path).node("pic") is not None


def test_load_view_missing_image_is_a_component_error(tmp_path: Path):
    view_path = tmp_path / "Broken_View.yaml"
    view_path.write_text(IMAGE_FRAGMENT_VIEW)
    with pytest.raises(ComponentError, match=r"widget 'img'.*cannot read"):
        load_view(view_path)


def test_instantiate_decodes_a_components_images(tmp_path: Path):
    """An embedded component's images are decoded by Tesserae too, and the
    spec its host builds has no `src:` left."""
    _png(tmp_path / "assets" / "rb.png")
    parent_path = tmp_path / "Parent_View.yaml"
    parent_path.write_text(
        "id: root\nkind: Container\nstyle: {width: 300, height: 300}\n"
        "children:\n  - {id: slot, kind: Container, style: {width: 250, height: 250}}\n"
    )
    item_path = tmp_path / "Tile_View.yaml"
    item_path.write_text(IMAGE_FRAGMENT_VIEW)
    vm_path = tmp_path / "Tile_ViewModel.py"
    vm_path.write_text("from tesserae import ViewModel\n\n\nclass TileViewModel(ViewModel):\n    pass\n")

    module_spec = importlib.util.spec_from_file_location("Tile_ViewModel", vm_path)
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_spec.name] = module
    module_spec.loader.exec_module(module)

    view = View(str(parent_path))
    calls = []

    original = view.instantiate

    def recording(path, into, spec=None, frames=None):
        calls.append((spec, frames))
        return original(path, into, spec=spec, frames=frames)

    view.instantiate = recording
    component, _ = instantiate(view, item_path, module.TileViewModel, view.node("slot"))

    assert component.node("img").get("pixel_width") == 2
    spec, frames = calls[0]
    assert spec["children"][0]["image"] == {"fit": "cover"}
    assert set(frames) == {"img"}
