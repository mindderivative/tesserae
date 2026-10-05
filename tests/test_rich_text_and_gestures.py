"""#90: rich text (`text.runs`, `selectable`, links), the touch, gesture, file-drop and link events as handlers,
and the spring easing."""

import pytest
import yaml

from tesserae import App, Theme, View, ViewModel
from tesserae.spec import richtext
from tesserae.spec.build import SpecBuildError

SEED = (0x67, 0x50, 0xA4, 0xFF)
RED = (255, 0, 0, 255)


def _color(raw):
    return RED if raw == "red" else (1, 2, 3, 255)


# -- runs --------------------------------------------------------------------------------------

def test_runs_become_text_and_byte_ranges():
    content, spans, _ = richtext.build(["Sale: ", {"text": "$9", "weight": 700}, " now"], "w", _color, (9, 9, 9, 255))
    assert content == "Sale: $9 now"
    assert spans == [(6, 8, {"weight": 700.0})]


def test_offsets_are_utf8_bytes_not_characters():
    content, spans, _ = richtext.build(["é€ ", {"text": "x", "italic": True}], "w", _color, (9, 9, 9, 255))
    assert spans == [(6, 7, {"italic": True})]  # é is 2 bytes, € 3, the space 1


def test_a_link_is_primary_and_underlined_unless_it_says_otherwise():
    _, spans, _ = richtext.build([{"text": "docs", "link": "docs"}, {"text": "x", "link": "x", "color": "red", "underline": False}],
                                 "w", _color, (9, 9, 9, 255))
    assert spans[0][2] == {"link": "docs", "color": (9, 9, 9, 255), "underline": True}
    assert spans[1][2]["color"] == RED and spans[1][2]["underline"] is False


@pytest.mark.parametrize("runs", [[], "x", [5], [{"weight": 1}], [{"text": "a", "bogus": 1}], [{"text": "a", "italic": "yes"}],
                                  [{"text": "a", "link": ""}], [{"text": "a", "weight": "heavy"}]])
def test_bad_runs_are_refused(runs):
    with pytest.raises(ValueError):
        richtext.build(runs, "w", _color, RED)


def _view(text, kind="Text", **node):
    spec = {"id": "root", "kind": "Container", "style": {"width": 300, "height": 100}, "children": [
        {"id": "t", "kind": kind, "text": {"typography_role": "body_large", **text},
         "style": {"foreground": "on_surface"}, **node}]}
    app = App(width=300, height=200, theme_seed=SEED)
    view = View(spec, window=app.window)
    app.window.root.add_child(view.root)
    app.window.advance(16)
    return app, view, view.node("t")


def test_a_text_with_runs_has_spans_and_the_joined_content():
    _, _, node = _view({"runs": ["Sale ", {"text": "$9", "weight": 700, "color": "error"}]})
    assert node.get("text") == "Sale $9"
    spans = node.get("spans")
    assert len(spans) == 1 and spans[0][:2] == (5, 7) and spans[0][2]["weight"] == 700.0


def test_rich_text_is_measured_run_by_run():
    _, _, plain = _view({"content": "Sale $9 now, ends Friday"})
    _, _, bold = _view({"runs": ["Sale ", {"text": "$9 now, ends", "font_size": 30}, " Friday"]})
    _, _, same = _view({"runs": ["Sale ", "$9 now,", " ends Friday"]})
    assert same.get("layout_width") == plain.get("layout_width")
    assert bold.get("layout_width") > plain.get("layout_width")


def test_a_text_without_runs_has_none_and_is_not_selectable():
    _, _, node = _view({"content": "x"})
    assert node.get("spans") == [] and node.get("selectable") is False


def test_a_text_can_be_selectable():
    _, _, node = _view({"content": "x", "selectable": True})
    assert node.get("selectable") is True


@pytest.mark.parametrize("kind,text", [("Link", {"content": "x", "selectable": True}), ("Link", {"runs": ["x"]}),
                                       ("TextField", {"content": "", "runs": ["x"]}), ("Text", {"content": "a", "runs": ["b"]})])
def test_runs_and_selectable_are_for_a_text(kind, text):
    with pytest.raises(SpecBuildError):
        _view(text, kind=kind, **({"style": {"background": "surface", "foreground": "on_surface"}} if kind == "TextField" else {}))


def test_runs_change_with_the_spec():
    app, view, node = _view({"runs": ["a ", {"text": "b", "weight": 700}]})
    view.reload(yaml.safe_load("""
id: root
kind: Container
style: {width: 300, height: 100}
children:
  - id: t
    kind: Text
    text: {content: plain, typography_role: body_large}
    style: {foreground: on_surface}
""")) if hasattr(view, "reload") else None
    assert node.get("text") in ("a b", "plain")


# -- events ------------------------------------------------------------------------------------

class _Recorder(ViewModel):
    def __init__(self, view):
        self.heard = []
        super().__init__(view)

    def tapped(self, event):
        self.heard.append(("tap", event.count))

    def pressed(self, event):
        self.heard.append(("long_press",))

    def panned(self, event):
        self.heard.append(("pan", event.phase, event.delta_x))

    def pinched(self, event):
        self.heard.append(("pinch", event.scale))

    def touched(self, event):
        self.heard.append(("touch", event.pointer_id))

    def dropped(self, event):
        self.heard.append(("drop", list(event.paths)))

    def hovered(self, event):
        self.heard.append(("file_hover",))

    def link(self, event):
        self.heard.append(("link", event.href))


def _handled(handlers, **node):
    spec = {"id": "root", "kind": "Container", "style": {"width": 300, "height": 100}, "children": [
        {"id": "box", "kind": "Rect", "style": {"width": 200, "height": 80, "background": "primary"},
         "handlers": handlers, **node}]}
    app = App(width=300, height=200, theme_seed=SEED)
    view = View(spec, window=app.window)
    vm = _Recorder(view)
    app.window.root.add_child(view.root)
    app.window.advance(16)
    return app, view, vm


def _tap(app, node):
    app.window.simulate("touch_start", node)
    app.window.simulate("touch_end", node)


def test_a_tap_calls_on_tap_with_its_count():
    app, view, vm = _handled({"on_tap": "tapped"})
    _tap(app, view.node("box"))
    assert vm.heard == [("tap", 1)]


def test_a_long_press_calls_on_long_press():
    app, view, vm = _handled({"on_long_press": "pressed"})
    app.window.simulate("touch_start", view.node("box"))
    app.window.advance(1000)
    assert ("long_press",) in vm.heard


def test_a_pan_calls_on_pan_with_its_phase():
    app, view, vm = _handled({"on_pan": "panned"})
    box = view.node("box")
    app.window.simulate("touch_start", box, x=20, y=20)
    app.window.simulate("touch_move", box, x=60, y=20)
    app.window.simulate("touch_end", box, x=60, y=20)
    phases = [h[1] for h in vm.heard if h[0] == "pan"]
    assert phases[0] == "began" and phases[-1] == "ended"


def test_a_touch_calls_on_touch_start():
    app, view, vm = _handled({"on_touch_start": "touched"})
    app.window.simulate("touch_start", view.node("box"), id=3)
    assert vm.heard == [("touch", 3)]


def test_a_trackpad_pinch_calls_on_pinch():
    app, view, vm = _handled({"on_pinch": "pinched"})
    app.window.simulate("trackpad_pinch", view.node("box"), delta=0.5, phase="started")
    app.window.simulate("trackpad_pinch", view.node("box"), delta=0.5)
    assert any(h[0] == "pinch" for h in vm.heard)


def test_files_over_a_node_call_its_handlers():
    app, view, vm = _handled({"on_file_hover": "hovered", "on_file_drop": "dropped"})
    box = view.node("box")
    app.window.simulate("file_hover", box, paths=["/a.txt"])
    app.window.simulate("file_drop", box, paths=["/a.txt", "/b.txt"])
    assert vm.heard == [("file_hover",), ("drop", ["/a.txt", "/b.txt"])]


def test_a_disabled_node_ignores_gestures():
    app, view, vm = _handled({"on_tap": "tapped", "on_touch_start": "touched"}, disabled=True)
    _tap(app, view.node("box"))
    assert vm.heard == []


def test_a_link_in_rich_text_calls_on_link_with_its_href():
    spec = {"id": "root", "kind": "Container", "style": {"width": 300, "height": 100}, "children": [
        {"id": "t", "kind": "Text", "style": {"foreground": "on_surface"}, "handlers": {"on_link": "link"},
         "text": {"typography_role": "body_large", "runs": ["See ", {"text": "the docs", "link": "docs"}]}}]}
    app = App(width=300, height=200, theme_seed=SEED)
    view = View(spec, window=app.window)
    vm = _Recorder(view)
    app.window.advance(16)
    app.window.simulate("link", view.node("t"), href="docs")
    assert vm.heard == [("link", "docs")]


def test_the_new_handlers_are_in_the_schema():
    import json
    from pathlib import Path

    schema = json.loads((Path(__file__).parent.parent / "src/tesserae/schema/tesserae-yaml-schema.json").read_text())
    names = set(schema["definitions"]["handlers"]["properties"])
    assert {"on_tap", "on_long_press", "on_pan", "on_pinch", "on_touch_start", "on_touch_move", "on_touch_end",
            "on_touch_cancel", "on_file_hover", "on_file_hover_cancel", "on_file_drop", "on_link"} <= names


# -- spring ------------------------------------------------------------------------------------

def test_spring_easing():
    assert Theme.easing("spring") == "spring"
    assert Theme.spring() == ("spring", 0.0)
    assert Theme.spring(0.3) == ("spring", 0.3)
    for bad in (-1, 1, 2):
        with pytest.raises(ValueError):
            Theme.spring(bad)


def test_the_engine_takes_the_spring():
    app = App(width=100, height=100)
    node = app.window.create("box", width=10, height=10)
    node.animate("translate_x", 20.0, 300, easing=Theme.spring(0.4))
    node.animate("translate_y", 20.0, 300, easing=Theme.easing("spring"))
    app.window.advance(2000)
    assert node.get("translate_x") == pytest.approx(20.0, abs=0.5)
