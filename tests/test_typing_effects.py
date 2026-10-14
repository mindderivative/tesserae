"""#248: `typing_effect` (flash, fade_in) and `caret_effect` (glide) on a text input, from the engine's `caret_move` event and `text_rects`."""

import pytest
import tre

from tesserae import App, Signal, ViewModel, tokens
from tesserae.listeners import Listeners
from tesserae.typing_effects import BLINK_MS, FADE_MS, FLASH_MS, GLIDE_MS, HOLD_MS, TypingEffects

SCHEME = tokens.baseline_scheme()
WHITE = (255, 255, 255, 255)


def build(typing="none", caret="none", reduced=False, background=WHITE, multiline=False, width=200.0, options=None):
    window = tre.Window(width=400, height=160)
    window.root.set(padding_top=0, padding_left=0, padding_right=0, padding_bottom=0)
    box = window.create("box", position="absolute", x=20.0, y=20.0, width=300.0, height=100.0, fill=background, padding_left=12.0, padding_top=10.0)
    field = window.create("text_input", width=width, height=60.0 if multiline else 30.0, font_size=16.0, multiline=multiline)
    box.add_child(field)
    window.root.add_child(box)
    window.advance(16)
    effects = TypingEffects(window, field, typing=typing, caret=caret, scheme=SCHEME, reduced=lambda: reduced, listen=Listeners().listen, options=options)
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


def test_detaching_after_the_input_has_been_destroyed_is_quiet():
    window, field, effects = build("flash", "glide")
    window.simulate("input", text="a")
    window.advance(16)
    field.destroy()
    window.advance(16)
    effects.detach()  # the view may go before the effects do


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
        self.caret = Signal("glide")


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


# -- settable per field -------------------------------------------------------------------------

def tint_at(window, field):
    rect = field.text_rects(0, 1)[0]
    return pixel(window, field.get("layout_x") + rect[0] + rect[2] / 2, field.get("layout_y") + rect[1] + rect[3] - 3)


def test_typing_duration_sets_how_long_a_flash_lasts():
    window, field, effects = build("flash", options={"typing_duration": 1000.0})
    window.simulate("input", text="W")
    window.advance(FLASH_MS + 200)  # past the default, well inside a second
    assert effects._covers and tint_at(window, field) != (255, 255, 255)
    window.advance(900)
    assert effects._covers == []
    window, field, effects = build("flash", options={"typing_duration": 40.0})
    window.simulate("input", text="W")
    window.advance(16)
    window.advance(120)
    assert effects._covers == []


def test_typing_duration_sets_how_long_a_fade_in_lasts_and_zero_leaves_both_out():
    window, field, effects = build("fade_in", options={"typing_duration": 800.0})
    window.simulate("input", text="W")
    window.advance(FADE_MS + 200)
    assert effects._covers  # still fading after the default time
    for effect in ("flash", "fade_in"):
        window, field, effects = build(effect, options={"typing_duration": 0.0})
        window.simulate("input", text="W")
        window.advance(16)
        assert effects._covers == [] and field.children() == []
        effects._cover(0, 1)  # asked directly, before any tick could end a zero-length animation: nothing is even made
        assert field.children() == []


def test_flash_color_is_a_theme_role_or_a_colour():
    window, field, _ = build("flash", options={"flash_color": "#FF0000", "flash_opacity": 1.0, "typing_duration": 2000.0})
    window.simulate("input", text="W")
    window.advance(16)
    red = tint_at(window, field)
    assert red[0] > 200 and red[1] < 60 and red[2] < 60  # a red tint at full strength
    window, field, _ = build("flash", options={"flash_color": "tertiary", "flash_opacity": 1.0, "typing_duration": 2000.0})
    window.simulate("input", text="W")
    window.advance(16)
    want = tuple(SCHEME["tertiary"])[:3]
    assert all(abs(a - b) < 40 for a, b in zip(tint_at(window, field), want))


def test_flash_opacity_sets_how_strong_it_starts():
    tints = {}
    for opacity in (0.1, 0.9):
        window, field, _ = build("flash", options={"flash_opacity": opacity, "typing_duration": 4000.0})
        window.simulate("input", text="W")
        window.advance(16)
        tints[opacity] = sum(tint_at(window, field))
    assert tints[0.9] < tints[0.1] < 765  # stronger is further from the white background, and even the faint one is tinted


def test_glide_duration_sets_how_long_the_caret_takes_and_zero_makes_it_jump():
    window, field, effects = build(caret="glide", options={"glide_duration": 800.0})  # a number from a view is a float
    window.simulate("input", text="abc")
    window.advance(GLIDE_MS + 200)
    on_its_way = effects._bar.get("translate_x")
    assert on_its_way < -1  # still on its way after the default time
    window.advance(300)
    assert on_its_way < effects._bar.get("translate_x") < 0  # and it keeps coming: the animation runs, it is not stuck where it began
    window.advance(600)
    assert effects._bar.get("translate_x") == 0.0  # and arrives
    window, field, effects = build(caret="glide", options={"glide_duration": 0.0})
    window.simulate("input", text="abcdefghij")
    window.advance(1)  # no tick to spare: it is already there
    assert effects._bar.get("translate_x") == 0.0 and effects._bar.get("x") == pytest.approx(field.caret_rect()[0])


def test_caret_blink_sets_the_period_and_zero_keeps_it_solid():
    window, field, effects = build(caret="glide", options={"caret_blink": 0.0})
    window.simulate("input", text="a")
    window.advance(16)
    assert not effects._timers.running("hold") and not effects._timers.running("blink")  # nothing is even scheduled
    for _ in range(12):
        window.advance(400)
        assert effects._bar.get("visible") is True
    window, field, effects = build(caret="glide", options={"caret_blink": 100.0})
    window.simulate("input", text="a")
    window.advance(HOLD_MS + 50)  # the first change is at about +100
    seen = []
    for _ in range(8):
        window.advance(100)
        seen.append(effects._bar.get("visible"))
    assert sum(1 for a, b in zip(seen, seen[1:]) if a != b) >= 6  # on, off, on, off: a change at nearly every look (the default 530 would show runs of five)


def test_an_option_that_is_not_a_colour_names_the_property():
    with pytest.raises(ValueError, match="flash_color 'sparkly' is not a theme role or a colour"):
        build("flash", options={"flash_color": "sparkly"})
    with pytest.raises(ValueError, match="unknown typing effect option"):
        build("flash", options={"colour": "red"})


def test_an_option_left_out_or_none_is_the_default():
    window, field, effects = build("flash", options={"typing_duration": None, "flash_color": None, "flash_opacity": None})
    assert effects._duration is None and effects._flash_color_raw is None and effects._flash_opacity == pytest.approx(0.24)


# -- through the view language: a TextField takes them, and a bad number is a load error --------------

def field_view(extra):
    return VIEW.replace("    caret_effect: glide\n", "    caret_effect: glide\n" + extra)


def test_a_text_field_passes_the_settings_to_its_input(tmp_path):
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text(field_view("    typing_duration: 700\n    flash_color: tertiary\n    flash_opacity: 0.6\n    glide_duration: 300\n    caret_blink: 0\n"))
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    view.window.advance(32)
    vm = app.bindings.viewmodel_for("main")
    vm.effect.set("flash")
    view.window.advance(32)
    field = input_node(view)
    field.focus()
    view.window.advance(16)
    view.window.simulate("input", text="a")
    view.window.advance(16)
    covers = [c for c in field.children() if c.get("width") != 1.5]
    tert = tuple(SCHEME["tertiary"])[:3]
    assert covers and tuple(covers[0].get("fill"))[:3] == tert and 0.5 < covers[0].get("opacity") <= 0.6  # the role and the strength that were asked for, just begun
    view.window.advance(FLASH_MS + 200)
    assert [c for c in field.children() if c.get("width") != 1.5], "700 ms outlasts the default 260 ms"
    view.window.advance(1000)
    view.window.simulate("input", text="bcdefghijk")  # a long way for the caret to go
    view.window.advance(GLIDE_MS + 100)  # past the default 120 ms, inside the 300 that were asked for
    bar = next(c for c in field.children() if c.get("width") == 1.5)
    assert bar.get("translate_x") < -0.5
    for _ in range(10):  # caret_blink: 0 keeps it solid
        view.window.advance(400)
        assert bar.get("visible") is True


def counting(monkeypatch):
    """Counts the `TypingEffects` made and detached."""
    from tesserae import typing_effects

    made, detached = [], []
    init, detach = typing_effects.TypingEffects.__init__, typing_effects.TypingEffects.detach

    def counted_init(self, *args, **kwargs):
        made.append(self)
        init(self, *args, **kwargs)

    def counted_detach(self):
        detached.append(self)
        detach(self)

    monkeypatch.setattr(typing_effects.TypingEffects, "__init__", counted_init)
    monkeypatch.setattr(typing_effects.TypingEffects, "detach", counted_detach)
    return made, detached


def test_the_effects_are_made_once_and_live_through_every_focus_change_and_keystroke(tmp_path, monkeypatch):
    """The view wires its inputs again whenever the composition changes, which each keystroke does by writing the text back: made afresh each
    time, the caret would begin every move where it ended, and a glide would never be seen."""
    made, detached = counting(monkeypatch)
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text(field_view("    glide_duration: 600\n    caret_blink: 0\n"))
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    view.window.advance(32)
    field = input_node(view)
    field.focus()
    view.window.advance(16)
    for letter in "abcdefghij":
        view.window.simulate("input", text=letter)
        view.window.advance(16)
    assert len(made) == 1 and detached == []
    bar = next(c for c in field.children() if c.get("width") == 1.5)
    assert bar.get("translate_x") < -0.5  # a glide, in a real field, across ten keystrokes


def test_turning_an_effect_off_removes_it_and_gives_the_engines_caret_back(tmp_path, monkeypatch):
    made, detached = counting(monkeypatch)
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text(VIEW.replace("caret_effect: glide", 'caret_effect: "{{ caret }}"'))
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    view.window.advance(32)
    vm = app.bindings.viewmodel_for("main")
    field = input_node(view)
    assert field.get("caret_visible") is False and len(made) == 1
    vm.caret.set("glide")  # the same settings: the same effects, not new ones
    view.window.advance(32)
    assert len(made) == 1 and detached == []
    vm.caret.set("none")
    view.window.advance(32)
    assert len(detached) == 1 and field.get("caret_visible") is True and field.children() == []
    vm.caret.set("glide")  # and on again: made again
    view.window.advance(32)
    assert len(made) == 2 and field.get("caret_visible") is False


def test_changing_a_setting_makes_the_effects_again(tmp_path, monkeypatch):
    made, detached = counting(monkeypatch)
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text(VIEW.replace("caret_effect: glide", "caret_effect: glide\n    glide_duration: \"{{ speed }}\"").replace(
        "self.caret", "self.caret"))
    app = App(root=tmp_path)
    app.bind(VMWithSpeed)
    view = app.open_view("Main")
    app.show("main")
    view.window.advance(32)
    assert len(made) == 1
    app.bindings.viewmodel_for("main").speed.set(500.0)
    view.window.advance(32)
    assert len(made) == 2 and len(detached) == 1


class VMWithSpeed(VM):
    def __init__(self):
        super().__init__()
        self.speed = Signal(100.0)


def test_closing_the_view_takes_the_effects_away(tmp_path, monkeypatch):
    made, detached = counting(monkeypatch)
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text(VIEW)
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    view.window.advance(32)
    assert len(made) == 1
    view.close()
    assert len(detached) == 1


def test_the_flash_follows_the_apps_theme_including_when_it_changes(tmp_path):
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text(field_view("    typing_duration: 5000\n    flash_opacity: 1.0\n"))
    app = App(root=tmp_path, theme_seed=(0xB3, 0x26, 0x1E, 0xFF), dark=False)  # a red seed: its primary is not the baseline's violet
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    view.window.advance(32)
    app.bindings.viewmodel_for("main").effect.set("flash")
    view.window.advance(32)
    field = input_node(view)
    field.focus()
    view.window.advance(16)

    def flash_fill(text):
        view.window.simulate("input", text=text)
        view.window.advance(16)
        return tuple([c for c in field.children() if c.get("width") != 1.5][-1].get("fill"))[:3]  # the newest: earlier flashes may still be fading

    light = flash_fill("a")
    assert light == tuple(round(c) for c in app.theme.role("primary"))[:3] and light != tuple(SCHEME["primary"])[:3]
    app.set_dark(True)
    view.window.advance(32)
    field.focus()
    view.window.advance(16)
    dark = flash_fill("b")
    assert dark == tuple(round(c) for c in app.theme.role("primary"))[:3] and dark != light  # the dark scheme's primary, not the colour it was wired with


@pytest.mark.parametrize("line, message", [
    ("typing_duration: -5", r"'typing_duration' takes a number of 0 or more, got -5"),
    ("flash_opacity: 2", r"'flash_opacity' takes a number from 0 to 1, got 2"),
    ("glide_duration: -1", r"'glide_duration' takes a number of 0 or more"),
    ("caret_blink: -1", r"'caret_blink' takes a number of 0 or more"),
    ("typing_duration: fast", r"'typing_duration' takes a number"),
])
def test_a_setting_out_of_range_is_a_load_error_naming_it_and_where(tmp_path, line, message):
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text(field_view(f"    {line}\n"))
    app = App(root=tmp_path)
    app.bind(VM)
    with pytest.raises(Exception, match=message) as raised:
        app.open_view("Main")
    assert "Main_View.yaml:" in str(raised.value)  # the file and the line


def test_a_property_can_bound_a_number_and_a_view_param_can_too():
    from tesserae.spec.widgets import Property, decl_from_params, json_schema

    prop = Property("float", minimum=0, maximum=1)
    assert prop.coerce(0.5) == 0.5 and prop.coerce(0) == 0 and prop.coerce(1) == 1
    for bad in (-0.1, 1.1):
        with pytest.raises(Exception, match=r"takes a number from 0 to 1"):
            prop.coerce(bad)
    assert Property("int", minimum=3).coerce(3) == 3
    with pytest.raises(Exception, match="of 3 or more"):
        Property("int", minimum=3).coerce(2)
    with pytest.raises(Exception, match="of 9 or less"):
        Property("float", maximum=9).coerce(10)
    decl = decl_from_params("V", {"size": {"type": "int", "min": 1, "max": 5, "default": 2}})
    assert (decl.properties["size"].minimum, decl.properties["size"].maximum) == (1, 5)
    schema = str(json_schema())
    assert "'minimum': 0" in schema and "'maximum': 1" in schema  # editors are told the range


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
