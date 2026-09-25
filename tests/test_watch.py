"""M29 Phase 3: `ViewWatcher` -- Tesserae-owned hot reload by polling
file modification times, replacing `tre`'s own `poll_reload`.

Every edit here bumps the file's mtime explicitly (`_edit`), so the
tests don't depend on how finely the filesystem records timestamps.
"""

import os
import re
from pathlib import Path

import pytest
from PIL import Image

from tesserae.spec import ComponentError, ViewWatcher, load_view


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def _bump_mtime(path: Path, before: int) -> None:
    os.utime(path, ns=(before + 1_000_000_000, before + 1_000_000_000))


def _edit(path: Path, text: str) -> None:
    before = path.stat().st_mtime_ns
    path.write_text(text)
    _bump_mtime(path, before)


def _text_view(content: str, extra_children: str = "") -> str:
    return (
        "id: root\nkind: Container\nchildren:\n"
        f"  - {{id: label, kind: Text, text: {{content: {content}, font_family: Roboto, font_size: 16}},"
        ' style: {width: 100, height: 20, foreground: "#000000"}}\n'
        + extra_children
    )


def _png(path: Path, color=(255, 0, 0)) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (2, 2), color).save(path)
    return path


def _watched(tmp_path: Path, text: str, **kwargs):
    view_path = _write(tmp_path / "Home_View.yaml", text)
    view = load_view(view_path, **kwargs)
    return view_path, view, ViewWatcher(view, view_path, **kwargs)


def test_poll_reports_no_change_until_a_file_changes(tmp_path: Path):
    _, _, watcher = _watched(tmp_path, _text_view("Hello"))
    assert watcher.poll() is False
    assert watcher.poll() is False


def test_editing_the_view_file_reconciles_the_live_view(tmp_path: Path):
    view_path, view, watcher = _watched(tmp_path, _text_view("Hello"))
    label = view.node("label")

    _edit(view_path, _text_view("Goodbye"))

    assert watcher.poll() is True
    assert view.node("label").get_text() == "Goodbye"
    assert label.get_text() == "Goodbye"  # same node, updated in place
    assert watcher.poll() is False


def test_editing_an_included_file_reloads(tmp_path: Path):
    part = _write(tmp_path / "parts" / "footer.yaml", _text_view("v1").replace("id: root", "id: footer", 1))
    _, view, watcher = _watched(
        tmp_path, "id: page\nkind: Container\nchildren:\n  - include: parts/footer.yaml\n"
    )
    assert part.resolve() in watcher.files

    _edit(part, _text_view("v2").replace("id: root", "id: footer", 1))

    assert watcher.poll() is True
    assert view.node("label").get_text() == "v2"


def test_editing_a_component_fragment_reloads(tmp_path: Path):
    frags = tmp_path / "frags"
    fragment = _write(
        frags / "Greeting_Component.yaml",
        "params: [width]\nid: root\nkind: Text\n"
        'text: {content: "Hi", font_family: Roboto, font_size: 16}\n'
        'style: {width: "{{ width }}", height: 20, foreground: "#000000"}\n',
    )
    _, view, watcher = _watched(
        tmp_path,
        "id: page\nkind: Container\nchildren:\n  - {id: greet, component: Greeting, with: {width: 80}}\n",
        component_dirs=[frags],
    )
    assert fragment.resolve() in watcher.files

    _edit(fragment, fragment.read_text().replace('"Hi"', '"Hello there"'))

    assert watcher.poll() is True
    assert view.node("greet").get_text() == "Hello there"


def test_changing_an_image_file_reloads(tmp_path: Path):
    image = _png(tmp_path / "logo.png")
    _, _, watcher = _watched(
        tmp_path,
        "id: root\nkind: Container\nchildren:\n"
        "  - {id: logo, kind: Image, image: {src: logo.png}, style: {width: 20, height: 20}}\n",
    )
    assert image.resolve() in watcher.files

    before = image.stat().st_mtime_ns
    _png(image, color=(0, 0, 255))
    _bump_mtime(image, before)

    assert watcher.poll() is True  # re-decoded and pushed without error


def test_a_newly_added_include_is_watched_after_reload(tmp_path: Path):
    view_path, view, watcher = _watched(tmp_path, _text_view("Hello"))
    rect = 'id: extra\nkind: Rect\nstyle: {{width: {n}, height: {n}, foreground: "#112233"}}\n'
    part = _write(tmp_path / "extra.yaml", rect.format(n=5))
    assert part.resolve() not in watcher.files

    _edit(view_path, _text_view("Hello", "  - include: extra.yaml\n"))
    assert watcher.poll() is True
    assert part.resolve() in watcher.files
    assert view.node("extra") is not None

    _edit(part, rect.format(n=9))
    assert watcher.poll() is True


def test_a_broken_edit_raises_once_then_recovers(tmp_path: Path):
    view_path, view, watcher = _watched(tmp_path, _text_view("Hello"))

    _edit(view_path, "id: root\nkind: Container\nchildren:\n  - {id: x, component: NoSuchThing}\n")
    with pytest.raises(ComponentError, match="unknown component 'NoSuchThing'"):
        watcher.poll()
    assert watcher.poll() is False  # same broken state: no repeat error
    assert view.node("label").get_text() == "Hello"  # view left as it was

    _edit(view_path, _text_view("Fixed"))
    assert watcher.poll() is True
    assert view.node("label").get_text() == "Fixed"


def test_a_spec_tre_rejects_is_reported_naming_the_view_file(tmp_path: Path):
    view_path, _, watcher = _watched(tmp_path, _text_view("Hello"))
    _edit(view_path, "id: root\nkind: NotARealKind\n")
    with pytest.raises(ValueError, match=rf"^{re.escape(str(view_path))}: .*NotARealKind"):
        watcher.poll()
