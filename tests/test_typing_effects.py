"""#248: `typing_effect` (flash, fade_in) and `caret_effect` (glide) on a text input, from the engine's `caret_move` event and `text_rects`."""

import pytest
import tre

from tesserae import App, Signal, ViewModel, tokens
from tesserae.listeners import Listeners
from tesserae.typing_effects import BLINK_MS, FADE_MS, FLASH_MS, GLIDE_MS, HOLD_MS, TypingEffects

SCHEME = tokens.baseline_scheme()
WHITE = (255, 255, 255, 255)


def build(typing="none", caret="none", reduced=False, background=WHITE, multiline=False, width=200.0):
    window = tre.Window(width=400, height=160)
    window.root.set(padding_top=0, padding_left=0, padding_right=0, padding_bottom=0)
    box = window.create("box", position="absolute", x=20.0, y=20.0, width=300.0, height=100.0, fill=background, padding_left=12.0, padding_top=10.0)
    field = window.create("text_input", width=width, height=60.0 if multiline else 30.0, font_size=16.0, multiline=multiline)
    box.add_child(field)
    window.root.add_child(box)
    window.advance(16)
    effects = TypingEffects(window, field, typing=typing, caret=caret, scheme=SCHEME, reduced=lambda: reduced, listen=Listeners().listen)
    field.focus()
    window.advance(16)
    return window, field, effects


def pixel(window, x, y):
    rgba, width, _ = window.snapshot()
    i = (int(y) * width + int(x)) * 4
    return tuple(rgba[i:i + 3])


def darkest(window, field, rect):
    nx, ny = field.get("layout_x"), field.get("layout_y")
    best = (255, 255, 255)
    for dx in range(int(rect[2])):
        for dy in range(int(rect[3])):
            p = pixel(window, nx + rect[0] + dx, ny + rect[1] + dy)
            if sum(p) < sum(best):
                best = p
    return best


# -- flash --------------------------------------------------------------------------------------

def test_a_flash_tints_the_characters_just_typed_and_is_gone_after_its_time():
    window, field, effects = build("flash")
    window.simulate("input", text="W")
    window.advance(16)
    rect = field.text_rects(0, 1)[0]
    x, y = field.get("layout_x") + rect[0] + rect[2] / 2, field.get("layout_y") + rect[1] + rect[3] - 3  # the lower part of the character's box
    tinted = pixel(window, x, y)
    assert tinted != (255, 255, 255) and tinted[2] > tinted[1]  # the primary colour is violet: blue over green
    assert len(effects._covers) == 1 and len(field.children()) == 1
    window.advance(FLASH_MS + 100)
    assert pixel(window, x, y) == (255, 255, 255) and effects._covers == [] and field.children() == []


def test_a_flash_covers_only_what_was_inserted_not_what_was_there():
    window, field, effects = build("flash")
    window.simulate("input", text="ab")
    window.advance(FLASH_MS + 100)
    window.simulate("input", text="c")
    window.advance(16)
    cover = effects._covers[0]
    assert cover.get("x") == pytest.approx(field.text_rects(2, 3)[0][0]) and cover.get("width") == pytest.approx(field.text_rects(2, 3)[0][2])


def test_a_flash_over_text_on_several_lines_covers_each_line():
    window, field, effects = build("flash", multiline=True)
    text = "ab\ncd\nef"
    window.simulate("input", text=text)
    window.advance(16)
    rects = field.text_rects(0, len(text))
    assert len(rects) == 3 and len(effects._covers) == 3
    assert [round(c.get("y")) for c in effects._covers] == [round(r[1]) for r in rects]  # one on each line


def test_the_effects_take_no_pointer_and_hide_from_a_screen_reader():
    window, field, effects = build("flash", "glide")
    window.simulate("input", text="a")
    window.advance(16)
    for node in (*effects._covers, effects._bar):
        assert node.get("hit_testable") is False and node.get("a11y_hidden") is True


# -- fade_in ------------------------------------------------------------------------------------

def test_fade_in_hides_the_new_characters_at_first_and_shows_them_after():
    window, field, effects = build("fade_in")
    reference, ref_field, _ = build("none")
    reference.simulate("input", text="W")
    reference.advance(400)
    settled = darkest(reference, ref_field, ref_field.text_rects(0, 1)[0])
    window.simulate("input", text="W")
    window.advance(16)
    rect = field.text_rects(0, 1)[0]
    assert sum(darkest(window, field, rect)) > sum(settled) + 200  # the glyph is covered: far lighter than it will be
    window.advance(FADE_MS + 100)
    assert darkest(window, field, rect) == settled and effects._covers == []


def test_fade_in_takes_the_first_opaque_fill_going_up_and_the_surface_when_there_is_none():
    window, field, effects = build("fade_in", background=(10, 20, 30, 255))
    assert effects._background() == (10, 20, 30, 255)
    window, field, effects = build("fade_in", background=(10, 20, 30, 128))  # not opaque: look further up
    assert effects._background() == tuple(SCHEME["surface"])


# -- glide --------------------------------------------------------------------------------------

def test_a_gliding_caret_hides_the_engines_and_follows_the_text():
    window, field, effects = build(caret="glide")
    assert field.get("caret_visible") is False and effects._bar.get("visible") is True
    window.simulate("input", text="abc")
    window.advance(16)
    x, y, _, height = field.caret_rect()
    assert effects._bar.get("x") == pytest.approx(x) and effects._bar.get("y") == pytest.approx(y) and effects._bar.get("height") == pytest.approx(height)


def test_the_caret_eases_to_its_new_place_in_the_time_it_has():
    window, field, effects = build(caret="glide")
    window.simulate("input", text="abc")
    window.advance(16)
    first = effects._bar.get("translate_x")
    assert first < -5  # drawn well to the left of where it now is
    window.advance(60)
    middle = effects._bar.get("translate_x")
    assert first < middle < 0  # on its way
    window.advance(GLIDE_MS)
    assert effects._bar.get("translate_x") == 0.0


def test_the_caret_is_solid_while_it_moves_then_blinks_and_hides_when_the_input_loses_the_focus():
    window, field, effects = build(caret="glide")
    window.simulate("input", text="a")
    window.advance(HOLD_MS - 100)
    assert effects._bar.get("visible") is True
    window.advance(200)  # past the hold: blinking
    seen = set()
    for _ in range(4):
        window.advance(BLINK_MS)
        seen.add(effects._bar.get("visible"))
    assert seen == {True, False}
    window.simulate("input", text="b")  # a keystroke makes it solid again
    window.advance(16)
    assert effects._bar.get("visible") is True
    effects._unfocus(None)
    assert effects._bar.get("visible") is False
    window.advance(BLINK_MS * 3)
    assert effects._bar.get("visible") is False  # no blinking while unfocused


def test_a_keystroke_in_the_middle_of_the_blink_makes_it_solid_for_the_whole_hold():
    window, field, effects = build(caret="glide")
    window.simulate("input", text="a")
    window.advance(HOLD_MS + BLINK_MS // 2)  # blinking, half way to its next change
    window.simulate("input", text="b")
    window.advance(16)
    for _ in range((HOLD_MS - 80) // 40):
        assert effects._bar.get("visible") is True  # an old blink timer left running would have turned it off by now
        window.advance(40)


def test_moving_the_caret_with_the_arrow_keys_glides_it_and_flashes_nothing():
    window, field, effects = build("flash", "glide")
    window.simulate("input", text="abc")
    window.advance(FLASH_MS + 100)
    assert effects._covers == []
    x = effects._bar.get("x")
    window.simulate("key_down", key="arrow_left")
    window.advance(16)
    assert effects._covers == [] and effects._bar.get("x") < x  # no insertion, so no flash; the caret went back a letter


def test_the_caret_stays_hidden_when_it_moves_while_the_input_has_no_focus():
    """The engine sends no `caret_move` for text changed from code while the input is unfocused, so this hands one over directly: the guard is ours."""
    from types import SimpleNamespace

    window, field, effects = build(caret="glide")
    other = window.create("box", width=20.0, height=20.0, focusable=True)
    window.root.add_child(other)
    window.advance(16)
    other.focus()  # the engine takes the focus away: a real unfocus
    window.advance(16)
    assert effects._focused is False and effects._bar.get("visible") is False
    effects._moved(SimpleNamespace(caret=(30.0, -1.0, 1.5, 20.0), inserted=None))
    assert effects._bar.get("visible") is False
    window.advance(HOLD_MS + BLINK_MS * 2)
    assert effects._bar.get("visible") is False  # and it does not start to blink


def test_detaching_stops_a_blink_that_is_running():
    window, field, effects = build(caret="glide")
    window.simulate("input", text="a")
    window.advance(HOLD_MS + 100)
    assert effects._timers.running("blink")
    effects.detach()
    assert not effects._timers.running("blink") and not effects._timers.running("hold")


def test_detaching_puts_the_engines_caret_back_and_removes_everything_drawn():
    window, field, effects = build("flash", "glide")
    window.simulate("input", text="ab")
    window.advance(16)
    assert field.children()
    effects.detach()
    assert field.get("caret_visible") is True and field.children() == [] and effects._timers.running("blink") is False
    window.simulate("input", text="c")
    window.advance(16)
    assert field.children() == []  # no longer listening


def test_a_flash_in_flight_is_dropped_by_detach():
    window, field, effects = build("flash")
    window.simulate("input", text="a")
    window.advance(16)
    assert effects._covers
    effects.detach()
    window.advance(FLASH_MS + 100)  # the animation's end must find nothing to destroy twice
    assert field.children() == []


# -- reduced motion -----------------------------------------------------------------------------

def test_with_reduced_motion_there_is_no_flash_no_fade_no_glide_and_no_blink():
    window, field, effects = build("flash", "glide", reduced=True)
    window.simulate("input", text="abc")
    window.advance(16)
    assert effects._covers == [] and effects._bar.get("translate_x") == 0.0
    assert effects._bar.get("x") == pytest.approx(field.caret_rect()[0])  # it jumped
    window.advance(HOLD_MS + BLINK_MS * 3)
    assert effects._bar.get("visible") is True  # steady


# -- through the view language ------------------------------------------------------------------

class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.text = Signal("")
        self.effect = Signal("none")


VIEW = """name: main
widget: Container
style: {width: 400, height: 200, padding: 20}
children:
  - widget: TextField
    name: tf
    label: Name
    text: "{{ text }}"
    typing_effect: "{{ effect }}"
    caret_effect: glide
"""


def opened(tmp_path, **app_kwargs):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(VIEW)
    app = App(root=tmp_path, **app_kwargs)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    view.window.advance(32)
    return app, view, app.bindings.viewmodel_for("main")


def input_node(view):
    return view.node("root.tf.box.body.input")


def test_a_text_field_takes_both_properties_and_the_effects_follow_them(tmp_path):
    app, view, vm = opened(tmp_path)
    field = input_node(view)
    assert field.get("caret_visible") is False  # caret_effect: glide, from the call
    field.focus()
    view.window.advance(16)
    view.window.simulate("input", text="a")
    view.window.advance(16)
    assert field.children() and all(c.get("hit_testable") is False for c in field.children())  # the bar, and no flash yet (the effect is none)
    count = len(field.children())
    vm.effect.set("flash")
    view.window.advance(32)
    field.focus()
    view.window.simulate("input", text="b")
    view.window.advance(16)
    assert len(field.children()) > count  # a flash cover joined the bar
    view.window.advance(FLASH_MS + 100)
    assert len(field.children()) == count


def test_an_app_that_asks_for_reduced_motion_gets_no_flash(tmp_path):
    app, view, vm = opened(tmp_path, reduced_motion=True)
    vm.effect.set("flash")
    view.window.advance(32)
    field = input_node(view)
    field.focus()
    view.window.advance(16)
    before = len(field.children())
    view.window.simulate("input", text="a")
    view.window.advance(16)
    assert len(field.children()) == before  # the bar, and nothing flashed


def test_a_value_that_is_not_an_effect_is_refused_naming_it(tmp_path):
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text(VIEW.replace("caret_effect: glide", "caret_effect: sparkle"))
    app = App(root=tmp_path)
    app.bind(VM)
    with pytest.raises(Exception, match="sparkle"):
        app.open_view("Main")


# -- the example --------------------------------------------------------------------------------

def test_the_example_runs_and_its_own_checks_pass(monkeypatch):
    import runpy
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent / "examples" / "typing_effects"
    monkeypatch.setattr(App, "run", lambda self, *args, **kwargs: None)
    runpy.run_path(str(root / "app.py"), run_name="__main__")


def test_the_example_keeps_its_window_open_when_asked(monkeypatch):
    import runpy
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent / "examples" / "typing_effects"
    calls = []
    monkeypatch.setattr(App, "run", lambda self, *args, **kwargs: calls.append(kwargs))
    runpy.run_path(str(root / "app.py"), run_name="__main__")
    monkeypatch.setattr(sys, "argv", ["app.py", "--interactive"])
    runpy.run_path(str(root / "app.py"), run_name="__main__")
    assert calls == [{"max_frames": 20}, {}]  # a frame limit by default, none when asked for
