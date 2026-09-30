"""0.3.0 M2 Phase 3 (#47): every press Tesserae tracks clears on
`pointer_cancel`. Since `tre` 0.5.0 the OS can take a press -- to move
the window from its title bar, maximize it, or show its menu -- and the
pressed node gets `pointer_cancel` instead of `pointer_up` (and no
click). A pressed state layer, a split button's squeeze, a splitter's or
slider's drag would otherwise stay pressed. Each is released as on
`pointer_up`: a drag keeps what it reached, and nothing is clicked.
"""

import ast
from pathlib import Path

from tesserae import View, ViewModel, interaction

SRC = Path(__file__).resolve().parent.parent / "src" / "tesserae"
SEED = (0x67, 0x50, 0xA4, 0xFF)


def test_every_function_listening_for_pointer_up_listens_for_pointer_cancel():
    """The invariant, over Tesserae's source: wherever a press's release
    is heard, its cancellation is too (ten places in 0.3.0 M2, and any
    added later). Nodes that take the pointer capture (a slider, a
    splitter) can't be dragged in `tre`, so this is how theirs are held."""
    missing, found = [], 0
    for path in sorted(SRC.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for fn in ast.walk(tree):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            inner = {id(n) for sub in ast.walk(fn) if sub is not fn and isinstance(sub, ast.FunctionDef)
                     for n in ast.walk(sub)}
            own = {n.value for n in ast.walk(fn) if id(n) not in inner
                   and isinstance(n, ast.Constant) and isinstance(n.value, str)}
            if "pointer_up" in own:
                found += 1
                if "pointer_cancel" not in own:
                    missing.append(f"{path.relative_to(SRC)}:{fn.lineno} {fn.name}")
    assert found >= 10 and missing == [], missing


class VM(ViewModel):
    clicks = 0

    def go(self):
        self.clicks += 1


def _button_in_a_title_bar():
    """A button marked as a drag region: `tre` moves the window from a
    press on it, as it would from a title bar."""
    spec = {"id": "root", "kind": "Container", "style": {"width": 400, "height": 300},
            "children": [{"id": "btn", "kind": "Rect", "handlers": {"on_click": "go"},
                          "style": {"width": 200, "height": 80, "background": "#6750A4"}}]}
    view = View(spec, theme_seed=SEED)
    vm = VM(view)
    view.node("btn").set(window_region="drag")
    view.window.advance(0)
    return view, vm


def test_a_pressed_state_layer_clears_when_the_os_takes_the_press():
    view, vm = _button_in_a_title_bar()
    it = view.interaction("btn")
    window = view.window
    window.simulate("pointer_move", x=100, y=40)
    window.simulate("pointer_down", x=100, y=40)
    for _ in range(4):
        window.advance(16)
    assert it.ripples, "pressed: a ripple"
    window.simulate("pointer_up", x=100, y=40)  # the window was dragged: pointer_cancel, no pointer_up
    for _ in range((interaction.MINIMUM_PRESS_MS + interaction.RELEASE_FADE_MS) // 16 + 4):
        window.advance(16)
    assert it.ripples == []  # released: the ripple faded out, as after pointer_up
    assert vm.clicks == 0  # a drag isn't a click
