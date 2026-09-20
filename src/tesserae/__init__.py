"""Tesserae -- a pyCopper-style declarative Python GUI framework, powered
by the Tesserae Render Engine (`tre`) instead of pyCopper's own direct
GLFW/wgpu-py stack.

Real, current surface (v1): `App`, the real single entry point owning a
named `View`/`ViewModel` registry and one live `Window`, letting
`App.show(name)` switch which pair is currently rendered without
re-bootstrapping either -- powered directly by `tre.Window.show_view`
(TRE M42 Phase 2). `Signal`/`View`/`ViewModel` are `tre`'s own real,
already-working MVVM primitives, re-exported here unmodified rather than
duplicated -- Tesserae's own real, additive value starts at `App`.
"""

from tre import Signal, View, ViewModel

from tesserae.app import App

__all__ = ["App", "Signal", "View", "ViewModel"]
