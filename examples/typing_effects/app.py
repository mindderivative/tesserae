#!/usr/bin/env python3
"""Typing effects on a text field: a flash and a fade-in on the characters just typed, and a caret that glides.

`typing_effect: flash | fade_in` is drawn over exactly the characters an edit inserted, and `caret_effect: glide` replaces the engine's caret with one
that eases to each new place and blinks after a moment. Both leave themselves out when the app asks for reduced motion. The last field sets the
looks itself (`flash_color`, `flash_opacity`, `typing_duration`, `glide_duration`, `caret_blink`). See the Text fields page.

It checks itself, then renders 20 frames and exits. Run it with `--interactive` to keep the window open and type in the fields by hand.
"""

import sys
from pathlib import Path

from loguru import logger

from tesserae import App, Signal, ViewModel, configure_logging

configure_logging()


class MainViewModel(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.a, self.b, self.c, self.d, self.e = Signal(""), Signal(""), Signal(""), Signal(""), Signal("")


app = App(root=Path(__file__).parent, title="Typing effects", theme_seed=(0x67, 0x50, 0xA4, 0xFF), dark=False,
          reduced_motion=False)  # the effects are what this shows: not the OS's setting (CI's macOS and Windows runners ask for reduced motion)
app.bind(MainViewModel)
view = app.open_view("Main")
app.show("main")
window = view.window
window.advance(32)


def field(name):
    return view.node(f"root.{name}.box.body.input")


def type_into(name, text):
    node = field(name)
    node.focus()
    window.advance(16)
    window.simulate("input", text=text)
    window.advance(16)
    return node


# -- self-checks: the same things a user would do -----------------------------------------------
flash = type_into("flash", "Hello")
assert flash.children(), "the flash is drawn over what was typed"
fade = type_into("fade", "Hello")
assert fade.children(), "the fade-in covers what was typed"
custom = type_into("custom", "Hello")
assert custom.children(), "the settings are the field's own: a tertiary flash that lasts 700 ms"
glide = type_into("glide", "Hello")
assert glide.get("caret_visible") is False and glide.children(), "the engine's caret is hidden and ours is drawn"
window.advance(600)
assert not flash.children() and not fade.children(), "the flash and the fade are gone by themselves"
assert view.node("root.flash.box.body.input").get("text") == "Hello" and app.bindings.viewmodel_for("main").a.get() == "Hello"

if "--interactive" in sys.argv[1:]:
    logger.info("interactive: type in the fields, close the window to quit")
    app.run()
else:
    app.run(max_frames=20)
    logger.info("examples/typing_effects/app.py: exited cleanly after a real 20-frame render loop")
