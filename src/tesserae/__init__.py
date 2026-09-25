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
keyed add/remove diffing. `Computed`/`Effect`/`batch`/`untrack` (TRE M45)
are the richer-reactivity layer built on `Signal`'s own dependency-
recording primitive -- derived/cached values, side-effect-only reactions,
and collapsing several related writes into one notification pass.
`Signal`/`View`/`ViewModel`/`Component`/`Computed`/`Effect`/`batch`/
`untrack` are `tre`'s own real, already-working primitives, re-exported
here unmodified rather than duplicated -- Tesserae's own real, additive
value is `App`/`instantiate`/`Repeater`.
"""

from tre import Component, Computed, Effect, Signal, View, ViewModel, batch, untrack

from tesserae.app import App
from tesserae.component import instantiate
from tesserae.fonts import register_font
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
    "instantiate",
    "register_font",
    "untrack",
]
