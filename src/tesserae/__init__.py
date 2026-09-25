"""Tesserae -- a pyCopper-style declarative Python GUI framework, powered
by the Tesserae Render Engine (`tre`) instead of pyCopper's own direct
GLFW/wgpu-py stack.

Real, current surface (v1): `App`, the real single entry point owning a
named `View`/`ViewModel` registry and one live `Window`, letting
`App.show(name)` switch which pair is currently rendered without
re-bootstrapping either -- powered directly by `tre.Window.show_view`
(TRE M42 Phase 2). `Component`/`instantiate` are the real, multi-instance
embedded-component layer (TRE M43) -- a component gets its own,
independent `ViewModel`, and `instantiate` enforces the identical
`*_View.yaml`/`*_ViewModel.py` naming convention `App.load` already does
for top-level screens. `Repeater` is the declarative-*feeling* layer on
top of that: one list `Signal` as the single source of truth, automatic
keyed add/remove diffing. `Signal`/`Computed`/`Effect`/`batch`/
`untrack`/`ViewModel` are Tesserae's own (`tesserae.reactive`, M35),
taken over from `tre`, which removes its copy in 0.3.5 (`tre` D5).
`View`/`Component` are still `tre`'s, re-exported, until Tesserae builds
views itself (M37).
"""

from tre import Component, View

from tesserae.app import App
from tesserae.component import instantiate
from tesserae.fonts import register_font
from tesserae.log import configure_logging
from tesserae.reactive import Computed, Effect, Signal, ViewModel, batch, untrack
from tesserae.repeater import Repeater

__all__ = [
    "App",
    "Component",
    "Computed",
    "Effect",
    "Repeater",
    "Signal",
    "View",
    "ViewModel",
    "batch",
    "configure_logging",
    "instantiate",
    "register_font",
    "untrack",
]
