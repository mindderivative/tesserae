#!/usr/bin/env python3
"""Tesserae's own real, first vertical slice (§ARCHITECTURE.md): a real
`Counter_View.yaml` + `Counter_ViewModel.py` pair, registered and shown
through `App`, proving the whole real stack end to end -- `*_View.yaml`/
`*_ViewModel.py` -> `tesserae.App` -> `tre.Window.from_view` -> real GPU
paint, and a real dispatched click re-evaluating a bound `text` property
through `tre`'s own live Tree.

`app.py` is the real entry point (the user's own explicit design
requirement: "app.py should be the entry point for the app... calling
the view/viewModel").
"""

from pathlib import Path

from tesserae import App

from Counter_ViewModel import CounterViewModel

directory = Path(__file__).parent

app = App(width=240, height=120, title="Tesserae Counter")
# App.load enforces the *_View.yaml/*_ViewModel.py naming convention at
# runtime (previously documentation-only) and registers under the
# inferred prefix, "Counter" -- both files here already follow it, so
# this succeeds; a mismatched pair would raise ValueError immediately.
view, viewmodel = app.load(directory / "Counter_View.yaml", CounterViewModel)
window = app.show("Counter")

label = view.node("label")
button = view.node("button")

print(f"before any click: label={label.get_text()!r}")
assert label.get_text() == "Count: 0"

# Three real, dispatched clicks -- the same real proof `tre`'s own
# live_view.py example already establishes for a single, un-wrapped
# View, here going through Tesserae's own real App.show()/registry
# layer instead.
for _ in range(3):
    window.click(button)

print(f"after 3 clicks: label={label.get_text()!r}")
assert label.get_text() == "Count: 3"
assert app.current == "Counter"

app.run(max_frames=20)
print("examples/counter/app.py: exited cleanly after a real 20-frame render loop")
