# `App`

## `App`

**`App(width=480, height=320, title="Tesserae App")`**

`width`/`height`/`title` describe the one real window this `App`
opens the first time `show()` is called -- every registered view is
shown inside that same window, at whatever size it already is, not its
own independent size (matching `Window.show_view`'s own real, stated
scope: only the *currently* active view's own `width`/`height` are
kept in sync with the window).

## `register`

**`register(name, view, viewmodel) -> None`**

Registers an already-loaded `view` and its already-`_attach`ed
`viewmodel` under `name`, for a later `show(name)` to display. Raises
`ValueError` if `name` is already registered.

## `load`

**`load(view_path, viewmodel_cls, name=None) -> (view, viewmodel)`**

Loads a `*_View.yaml` + `*_ViewModel.py` pair and registers it -- see
[Naming Convention](../guide/naming-convention.md). `name` defaults to
the shared prefix. Returns the constructed `(view, viewmodel)` pair.

## `show`

**`show(name) -> Window`**

Shows the view registered under `name`. The first call opens the real
`Window`; every call after switches the same live `Window`.

## `current`

**`current -> str | None`**

The name last passed to `show()`, or `None` before the first real
call.

## `run`

**`run(max_frames=None) -> None`**

The one blocking call -- opens the real window `show()` already built
and runs `tre`'s own real render loop. `max_frames` caps it (headless/
CI-safe); omit it for a real, interactive run. Raises `RuntimeError`
if called before `show()`.
