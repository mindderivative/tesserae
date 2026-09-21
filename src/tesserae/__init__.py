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
keyed add/remove diffing. `Signal`/`View`/`ViewModel`/`Component` are
`tre`'s own real, already-working primitives, re-exported here unmodified
rather than duplicated -- Tesserae's own real, additive value is `App`/
`instantiate`/`Repeater`.
"""

from tre import Component, Signal, View, ViewModel

from tesserae.app import App
from tesserae.component import instantiate
from tesserae.repeater import Repeater

__all__ = ["App", "Component", "Repeater", "Signal", "View", "ViewModel", "instantiate"]
