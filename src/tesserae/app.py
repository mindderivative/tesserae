"""`App` -- the real, single Tesserae entry point every real `app.py`
owns exactly one of, per the user's own explicit design requirement:
"app.py should be the entry point for the app... this allows for
switching of current views without needing to bootstrap each
view/viewModel."

Owns a registry of named `(View, ViewModel)` pairs -- each `*_View.yaml`
+ `*_ViewModel.py` file pair a real app registers once, up front -- and
exactly one live `tre.Window`, created with the `App`. Screens are built
into it by Tesserae; `App.show(name)` attaches that screen's root
to the window and detaches the one shown before. Neither a `View` nor
its `ViewModel` is ever re-parsed,
re-attached, or otherwise re-bootstrapped by a later `show()` call --
each stays alive, its own `Signal` subscriptions intact, for the whole
life of the `App`.
"""

from __future__ import annotations

import os
import sys
import time
import weakref
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from loguru import logger
from tre import App as _TreApp
from tre import Window

from tesserae.follow import alive, app_of, register_app, retheme
from tesserae.listeners import Listeners
from tesserae.naming import check_naming_convention
from tesserae.project import Project, is_name, resolve_view
from tesserae import tokens
from tesserae.reactive import Computed, Effect, Signal, batch
from tesserae.spec import ViewWatcher, load_stylesheet, load_theme
from tesserae.view import View as TesseraeView
from tesserae.shell_file import load_shell_spec
from tesserae.spec.watch import ComponentWatcher, FileWatcher

#: How often `run(keepalive=True)` ticks, in seconds: about 50 times a second,
#: which costs about half a percent of one core while a window is idle.
KEEPALIVE_INTERVAL = 0.02


def _keepalive_interval(keepalive: bool | float | None) -> float | None:
    """Seconds between keepalive ticks for `run(keepalive=)`, or `None` for
    none. Off by default since 0.3.2: before `tre` 0.5.1 its idle window
    starved other Python threads (so a hot-reload watcher couldn't hand a
    reload over without a tick: 0.3.1 ticked by default), and Tesserae now
    requires a `tre` that doesn't. `None` is accepted as `False`, for code
    that passed 0.3.1's "follow hot_reload"."""
    if keepalive is None or keepalive is False:
        return None
    if keepalive is True:
        return KEEPALIVE_INTERVAL
    if isinstance(keepalive, (int, float)) and keepalive > 0:
        return float(keepalive)
    raise ValueError(f"keepalive must be True, False or a positive number of seconds, got {keepalive!r}")


@dataclass
class _Route:
    """A route: its pattern, the screen it names, and its segments,
    each a literal or a `(param, converter)`."""

    pattern: str
    name: str
    segments: list[Any]

    def match(self, parts: list[str]) -> dict[str, Any] | None:
        if len(parts) != len(self.segments):
            return None
        params: dict[str, Any] = {}
        for part, segment in zip(parts, self.segments):
            if isinstance(segment, str):
                if part != segment:
                    return None
                continue
            param, converter = segment
            if converter == "int":
                if not part.lstrip("-").isdigit():
                    return None
                params[param] = int(part)
            else:
                params[param] = part
        return params


def _route_parts(route: str) -> list[str]:
    """A route's segments: `"notes/42"` is `["notes", "42"]`, and `""` or
    `"/"` (the app's root) has none."""
    route = route.strip("/")
    return route.split("/") if route else []


@dataclass
class _Registered:
    view: Any
    viewmodel: Any


@dataclass
class _Built:
    """A view `App.build_view()` made -- one a theme or stylesheet reload
    reaches."""

    view: Any
    #: `True` if it was given its own stylesheet (file or dict) instead
    #: of the app's default.
    own_stylesheet: bool = False
    #: That own stylesheet's file, resolved, if it came from one.
    stylesheet_file: Path | None = None


def _os_dark(window: Any) -> bool | None:
    """The OS's appearance: `True` dark, `False` light, or `None` when it
    can't say. On
    Linux it answers at once; on macOS and Windows, once the window is open;
    headless, never. One function, so tests can fix the answer."""
    try:
        value = window.get("dark")
    except ValueError:  # a `tre` before 0.3.5.2
        return None
    return None if value is None else bool(value)


def _apply_all(views: list[Any], apply: Any, undo: Any) -> None:
    """`apply(view)` for each view; if one raises, `undo(view)` the ones
    already done, then re-raise -- so a rejected theme or stylesheet
    leaves every screen as it was."""
    done: list[Any] = []
    try:
        for view in views:
            apply(view)
            done.append(view)
    except Exception:
        for view in done:
            undo(view)
        raise


def _from_file(path: Path, what: str, fn: Any) -> Any:
    """Wraps `fn(arg)`, a change read from `path`: a `ValueError` from
    `tre` names the file, as a failed view reload does, and a change that
    applies is logged."""

    def apply(arg: Any) -> None:
        try:
            fn(arg)
        except ValueError as exc:
            raise ValueError(f"{path}: {exc}") from exc
        logger.info("{} from {}", what, path)

    return apply


def _inset(value: Any) -> tuple[float, float]:
    height, width = value
    return (float(height), float(width))


def _non_negative(name: str, value: Any, *, allow_none: bool = False) -> Any:
    if value is None and allow_none:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise ValueError(f"App: {name} must be a number of pixels, 0 or more, got {value!r}")
    return int(value)


def _file_or_spec(owner: str, file_arg: str, file: Any, spec: Any, loader: Any) -> Any:
    """One `*=` file path / `*_spec=` dict pair -> the dict (or `None`).
    The file is read here, by Tesserae; `tre` only ever gets the dict."""
    if file is not None and spec is not None:
        raise ValueError(f"{owner}: pass {file_arg}= or {file_arg}_spec=, not both")
    return loader(file) if file is not None else spec


def _script_folder() -> Path:
    """The folder of the script that runs (`app.py`), or the current folder."""
    script = getattr(sys.modules.get("__main__"), "__file__", None)
    return Path(script).resolve().parent if script else Path.cwd()


class App:
    """`width`/`height`/`title` describe the one real `Window` this
    `App` opens the first time `show()` is called -- every registered
    view is shown inside that same window, at whatever size it already
    is, not its own independent size (matching `Window.show_view`'s own
    real, stated scope: only the *currently* active view's `width`/
    `height` are kept in sync with the window).

    M30: the theme is app-wide -- `theme_seed=`, `dark=`,
    `default_theme=`/`custom_theme=` (file paths) or their `*_spec=`
    dict forms apply to every screen `build_view()`/`load()` builds. The
    theme is Tesserae's (`tesserae.Theme`, `app.theme`); since M42 the
    window's own `tre` theme is never set or read, as nothing `tre` draws
    uses it any more.

    `stylesheet=`/`stylesheet_spec=` here is the default stylesheet for
    every screen; `load(stylesheet=...)` replaces it for one screen (a
    stylesheet is genuinely per-`View` in `tre`).

    The theme and default stylesheet files are read once, here, by
    Tesserae (so a `FontFallbackWarning` fires once, not once per
    screen); a screen's own `load(stylesheet=...)` file is read when it
    loads. `tre` only ever gets the dicts.
    """

    def __init__(
        self,
        width: int = 480,
        height: int = 320,
        title: str = "Tesserae App",
        *,
        theme_seed: tuple[int, int, int, int] | None = None,
        dark: bool | str = "system",
        default_theme: str | Path | None = None,
        default_theme_spec: dict[str, Any] | None = None,
        custom_theme: str | Path | None = None,
        custom_theme_spec: dict[str, Any] | None = None,
        stylesheet: str | Path | None = None,
        stylesheet_spec: dict[str, Any] | None = None,
        state: Any = None,
        root: str | Path | None = None,
        search: Any = (),
        recursive: bool = False,
        decorations: bool = True,
        resize_border: int | None = None,
        min_width: int = 0,
        min_height: int = 0,
        fullscreen: bool = False,
        system_menu: bool = False,
        icon: str | Path | None = None,
        window_border: bool = True,
    ) -> None:
        #: The app's shared state (M65): any object, typically a class of
        #: `Signal`s every screen reads. A ViewModel reaches it as
        #: `self.state`, and a binding as `{{ state.<name>.get() }}`.
        self.state = state
        #: The project's files, found by name: `Views/`, `ViewModels/`, `Components/`, `Themes/` and `Styles/`
        #: under `root` (the folder of the script that runs, by default), and the folders in `search`; with
        #: `recursive`, the whole project. See `tesserae.project`.
        self.project = Project(root if root is not None else _script_folder(), search, recursive)
        default_theme = self._named("theme", default_theme)
        custom_theme = self._named("theme", custom_theme)
        stylesheet = self._named("stylesheet", stylesheet)
        self._width = width
        self._height = height
        self._title = title
        self._theme_seed = theme_seed
        if dark not in (True, False, "system"):
            raise ValueError(f'App: dark must be True, False or "system", got {dark!r}')
        #: "system" follows the OS; True/False is the app's own fixed choice (M38).
        self._dark_mode: bool | str = dark
        #: The appearance in use. "system" starts with the OS's, once the window
        #: exists to ask (M53), and dark where the OS can't say yet (M38 Q3).
        self._dark: bool = True if dark == "system" else bool(dark)
        self._default_theme_spec = _file_or_spec("App", "default_theme", default_theme, default_theme_spec, load_theme)
        self._custom_theme_spec = _file_or_spec("App", "custom_theme", custom_theme, custom_theme_spec, load_theme)
        #: The theme files, for `run(hot_reload=True)` to watch (M31).
        self._theme_files = {"default": default_theme, "custom": custom_theme}
        #: Every view `build_view()` made -- the ones a reload reaches.
        self._built: list[_Built] = []
        self._stylesheet_spec = _file_or_spec("App", "stylesheet", stylesheet, stylesheet_spec, load_stylesheet)
        #: The default stylesheet's file, for `run(hot_reload=True)`.
        self._stylesheet_file = stylesheet
        #: Each screen's own stylesheet file -> the dict `tre` last accepted.
        self._own_sheets: dict[Path, Any] = {}
        self._registered: dict[str, _Registered] = {}
        #: The navigation history (M66): each entry a screen's name and its
        #: params, and the index of the one showing (-1 before the first).
        self._history: list[tuple[str, dict[str, Any]]] = []
        self._at = -1
        #: Whether `back()`/`forward()` would move -- for a back button's
        #: `disabled` binding.
        self.can_go_back = Signal(False)
        self.can_go_forward = Signal(False)
        self._routes: list[_Route] = []
        # M37: the app's one window exists from the start, so screens are built
        # straight into it. Like a `Window.from_view` root: no padding, and a
        # screen root with no size of its own is sized to its content.
        self._window: Window = Window(width=width, height=height, title=title, decorations=bool(decorations))
        self._window.root.set(padding_top=0, padding_right=0, padding_bottom=0, padding_left=0,
                              align_items="flex_start")
        # 0.3.0 M2: the window's own options, for a title bar the app draws
        # (`tre` 0.5.0). An undecorated window resizes from a 6 px border
        # unless the app gives its own width (the design's Q6).
        self._resize_border: int | None = _non_negative("resize_border", resize_border, allow_none=True)
        self._window.set(resize_border=self._resize_for(bool(decorations)),
                         min_width=_non_negative("min_width", min_width),
                         min_height=_non_negative("min_height", min_height),
                         fullscreen=bool(fullscreen), system_menu=bool(system_menu))
        if icon is not None:
            self.set_icon(icon)
        #: Whether the window is maximized, and whether it has the OS's
        #: focus (0.3.0 M2): read-only, following `tre`'s `maximized` and
        #: `active` events, for a title bar's bindings --
        #: `{{ app.maximized.get() }}` swaps its maximize icon.
        self._maximized = Signal(bool(self._window.get("maximized")))
        self._active = Signal(bool(self._window.get("active")))
        self.maximized = Computed(self._maximized.get)
        self.active = Computed(self._active.get)
        self._window.on("maximized", lambda event: self._maximized.set(bool(event.maximized)))
        self._window.on("active", lambda event: self._active.set(bool(event.active)))
        #: macOS keeps its title bar, transparent, with the traffic lights
        #: (0.3.0 M3): `titlebar_inset` is `(height, width)` of the space
        #: they take -- `(0, 0)` elsewhere, decorated, and in fullscreen --
        #: and `native_controls` whether they're showing, for a title bar
        #: to leave room and hide its own buttons.
        self._titlebar_inset = Signal(_inset(self._window.get("titlebar_inset")))
        self._native_controls = Signal(bool(self._window.get("native_controls")))
        self.titlebar_inset = Computed(self._titlebar_inset.get)
        self.native_controls = Computed(self._native_controls.get)
        self._window.on("titlebar_inset", self._on_titlebar_inset)
        # 0.3.0 M4 (the design's Q9): an undecorated window's 1 px border,
        # built the first time it shows, and shown while undecorated,
        # neither maximized nor fullscreen, and not on macOS (its frame).
        self._decorated = Signal(bool(decorations))
        self._fullscreen = Signal(bool(fullscreen))
        self._window_border = Signal(bool(window_border))
        self._border: Any = None
        self._border_effect = Effect(self._show_border)
        if dark == "system":  # M53: Linux answers now; macOS and Windows once the window opens (run())
            os_dark = _os_dark(self._window)
            if os_dark is not None:
                self._dark = os_dark
        self._current: str | None = None
        self._shell: Any = None  # an `AppShell`, once `use_shell` is called (M45)
        self._shell_file: Path | None = None  # the `*_Shell.yaml` `load_shell` read (M52)
        self._shell_spec: Any = None  # ...its spec as last applied, and the viewmodel it was given
        self._shell_viewmodel: Any = None
        self._navigation: Any = None  # (the shell file's rail, its screens), for `show` to select (M52)
        self._tre_app: _TreApp | None = None
        #: The widgets made on this window with no `theme=`, which follow
        #: the app's theme (M50), in the order they were made (a dict as an
        #: ordered set, so a failed re-theme's rollback is predictable).
        self._followers: dict[Any, None] = {}
        register_app(self)
        #: Alt+Left and Alt+Right go back and forward (M66), and so do the
        #: mouse's side buttons (M72, on `tre` 0.4.1). Key presses and pointer
        #: events bubble to the window's root, wherever they happen.
        self._keys = Listeners()
        self._keys.listen(self._window.root, "key_down", self._history_key)
        self._keys.listen(self._window.root, "pointer_down", self._history_button)
        #: While `run(hot_reload=True)` runs: the loop's handle, every
        #: watcher started, and each component file's watcher (M51).
        self._hot_handle: Any = None
        self._watchers: list[Any] = []
        self._component_watchers: dict[Path, Any] = {}
        #: Every component `tesserae.instantiate` made on this window, in any
        #: view (M61); weakly held, so removed ones drop out.
        self._instances: weakref.WeakSet[Any] = weakref.WeakSet()
        self._window.on("color_scheme", self._on_color_scheme)

    # -- light and dark (M38) ---------------------------------------------------

    @property
    def dark(self) -> bool:
        """Whether the app is showing its dark scheme right now."""
        return self._dark

    @property
    def dark_mode(self) -> bool | str:
        """`"system"` (following the OS), or the app's fixed `True`/`False`."""
        return self._dark_mode

    def set_dark(self, dark: bool | str) -> None:
        """`True`/`False` fixes the app dark or light, re-theming every
        screen in place; `"system"` goes back to following
        the OS from its next switch."""
        if dark not in (True, False, "system"):
            raise ValueError(f'App.set_dark: dark must be True, False or "system", got {dark!r}')
        self._dark_mode = dark
        if dark != "system":
            self._apply_dark(bool(dark))

    def _on_color_scheme(self, event: Any) -> None:
        """The OS switched between light and dark: following the OS, the
        whole app follows; with a fixed choice, nothing changes."""
        if self._dark_mode == "system":
            self._apply_dark(bool(event.dark))

    def _adopt_os_appearance(self) -> None:
        """Following the OS, asks it again once the window is open (M53
        Q2): macOS and Windows can't say before, and the app re-themes then,
        as a `color_scheme` event would."""
        if self._dark_mode == "system":
            os_dark = _os_dark(self._window)
            if os_dark is not None:
                self._apply_dark(os_dark)

    def _apply_dark(self, dark: bool) -> None:
        if dark == self._dark:
            return
        old_theme = self._view_theme()
        self._dark = dark
        new_theme = self._view_theme()
        try:
            self._retheme(old_theme, new_theme)
        except Exception:
            self._dark = not dark
            raise
        logger.info("switched to the {} scheme", "dark" if dark else "light")

    def _retheme(self, old: dict[str, Any], new: dict[str, Any]) -> None:
        """Re-themes every view `build_view()` made, then every widget
        following the app, from the `old` theme arguments to `new`;
        if one fails, the ones done go back to `old` and it re-raises."""
        from tesserae.theme import Theme

        old_theme, new_theme = Theme.resolve(**old), Theme.resolve(**new)
        for f in [f for f in self._followers if not alive(f)]:
            del self._followers[f]  # its node was destroyed under it
        steps: list[tuple[Any, Any]] = [
            (lambda view=b.view: view.set_theme(**new), lambda view=b.view: view.set_theme(**old)) for b in self._built
        ]
        steps += [(lambda f=f: retheme(f, new_theme, new), lambda f=f: retheme(f, old_theme, old))
                  for f in list(self._followers)]
        _apply_all(steps, lambda step: step[0](), lambda step: step[1]())

    def _view_theme(self) -> dict[str, Any]:
        """The app's theme as `View(...)`/`View.set_theme` arguments."""
        theme: dict[str, Any] = {"dark": self._dark}
        if self._theme_seed is not None:
            theme["theme_seed"] = self._theme_seed
        if self._default_theme_spec is not None:
            theme["default_theme_spec"] = self._default_theme_spec
        if self._custom_theme_spec is not None:
            theme["custom_theme_spec"] = self._custom_theme_spec
        return theme

    @property
    def theme(self) -> Any:
        """The app's resolved theme (`tesserae.Theme`): roles, component
        shape and elevation, typography, and motion tokens."""
        from tesserae.theme import Theme

        return Theme.resolve(**self._view_theme())

    def _read_theme_files(self) -> tuple[Any, Any]:
        """Re-reads the theme files (a watcher-thread job, M31); a theme
        given as a `*_spec=` dict is kept as it is."""
        files = self._theme_files
        default = load_theme(files["default"]) if files["default"] is not None else self._default_theme_spec
        custom = load_theme(files["custom"]) if files["custom"] is not None else self._custom_theme_spec
        return default, custom

    def set_theme_specs(self, default_theme_spec: Any, custom_theme_spec: Any) -> None:
        """Re-themes the running app in place: every view
        `build_view()`/`load()` made. Both theme dicts
        are the complete new selection (`None` for none), as in `tre`,
        where each `set_theme` call is a fresh choice, not a patch; the
        seed and light/dark stay as they are. Bound values stay
        live (`tre` M91). Runs `tre` code, so call it on the event-loop
        thread -- `run(hot_reload=True)` does, for theme-file edits.
        """
        old_theme = self._view_theme()
        previous = (self._default_theme_spec, self._custom_theme_spec)
        self._default_theme_spec, self._custom_theme_spec = default_theme_spec, custom_theme_spec
        try:
            self._retheme(old_theme, self._view_theme())
        except Exception:
            self._default_theme_spec, self._custom_theme_spec = previous
            raise

    def set_stylesheet_spec(self, stylesheet_spec: dict[str, Any] | None) -> None:
        """Replaces the app's default stylesheet in place:
        every view `build_view()`/`load()` made with the default -- not
        one given its own `stylesheet=` -- is re-styled, and views built
        later use it too. `None` means no stylesheet. Bound values stay
        live (`tre` M91). If `tre` rejects it, it raises and every screen
        keeps its old stylesheet. Call it on the event-loop thread;
        `run(hot_reload=True)` does, when the default stylesheet file
        changes.
        """
        previous = self._stylesheet_spec
        _apply_all(
            [b.view for b in self._built if not b.own_stylesheet],
            lambda view: view.set_stylesheet(stylesheet_spec=stylesheet_spec),
            lambda view: view.set_stylesheet(stylesheet_spec=previous),
        )
        self._stylesheet_spec = stylesheet_spec

    def _set_own_stylesheet(self, path: Path, stylesheet_spec: dict[str, Any]) -> None:
        """A screen's own stylesheet file changed: re-style the views
        built with it."""
        previous = self._own_sheets.get(path)
        _apply_all(
            [b.view for b in self._built if b.stylesheet_file == path],
            lambda view: view.set_stylesheet(stylesheet_spec=stylesheet_spec),
            lambda view: view.set_stylesheet(stylesheet_spec=previous),
        )
        self._own_sheets[path] = stylesheet_spec

    def build_view(
        self,
        view_path: str | Path,
        *,
        stylesheet: str | Path | None = None,
        stylesheet_spec: dict[str, Any] | None = None,
    ) -> Any:
        """Builds a view with this app's theme and stylesheet, without
        registering it -- for a screen given to `register()`, e.g. one
        whose `ViewModel` needs the `app` itself. `stylesheet=`/
        `stylesheet_spec=` replace the app's default stylesheet for this
        view. `load()` builds its views through this too.
        """
        view_path = self._named("view", view_path)
        stylesheet = self._named("stylesheet", stylesheet)
        sheet = _file_or_spec("App.build_view", "stylesheet", stylesheet, stylesheet_spec, load_stylesheet)
        built = _Built(None, own_stylesheet=sheet is not None)
        if stylesheet is not None:
            built.stylesheet_file = Path(stylesheet).resolve()
            self._own_sheets[built.stylesheet_file] = sheet
        if sheet is None:
            sheet = self._stylesheet_spec
        kwargs = self._view_theme()
        if sheet is not None:
            kwargs["stylesheet_spec"] = sheet
        try:
            built.view = TesseraeView(Path(view_path), window=self._window, project=self.project, **kwargs)
        except ValueError:
            raise
        self._built.append(built)
        return built.view

    def register(self, name: str, view: Any, viewmodel: Any) -> None:
        """Registers `view` (already loaded) and its already-`_attach`ed
        `viewmodel` (e.g. `FooViewModel(view)`) under `name`, for a later
        `show(name)` to display. Raises if `name` is already registered
        -- a real, load-bearing collision a caller should know about
        immediately, not silently overwrite.

        The caller builds `view`, so the caller themes it: build it with
        `app.build_view("Foo_View.yaml")` to give it this app's theme and
        stylesheet. A view built any other way keeps whatever theme
        it was built with. A view built from a file keeps it (`view.path`),
        so `run(hot_reload=True)` watches it as it does a `load()`ed one
.
        """
        if name in self._registered:
            raise ValueError(f"a view named {name!r} is already registered")
        if not isinstance(view, TesseraeView):
            raise TypeError(
                f"App.register({name!r}): the view must be a tesserae View (e.g. from app.build_view()), "
                f"got {type(view).__name__}"
            )
        view.move_to(self._window)  # a view built on its own is rebuilt in this app's window
        self._registered[name] = _Registered(view, viewmodel)

    def _named(self, kind: str, ref: Any) -> Any:
        """`ref` as a path: a bare name (`"Main"`) is found in the project, a path is left as it is."""
        return self.project.find(kind, ref) if is_name(ref) else ref

    def load(
        self,
        view_path: str | Path,
        viewmodel_cls: type | None = None,
        name: str | None = None,
        *,
        stylesheet: str | Path | None = None,
        stylesheet_spec: dict[str, Any] | None = None,
    ) -> tuple[Any, Any]:
        """Loads a `*_View.yaml` + `*_ViewModel.py` pair and registers it.

        `view_path` is a path, or a name found in the project (`app.load("Main")` is `Views/Main_View.yaml`).
        `viewmodel_cls` is the ViewModel class; left out, it is found by the view's name (`Main_ViewModel.py`,
        class `MainViewModel`, beside the view or in `ViewModels/`). The pair must follow the
        [naming convention](naming-convention.md): the same prefix, checked here, so a mismatch fails at load
        and not later when a handler name doesn't resolve.

        `name` defaults to that prefix (`"Main"`); it is only needed if two pairs would share it. The view is
        built with `build_view`, with the app's theme and its default stylesheet, or this screen's own
        `stylesheet=` / `stylesheet_spec=` (a path or a name).

        Returns the `(view, viewmodel)` pair, for code that wants a node to click in a test or a Signal to
        read back.
        """
        view_path, viewmodel_cls = resolve_view(self.project, view_path, viewmodel_cls)
        prefix = check_naming_convention(view_path, viewmodel_cls)

        view = self.build_view(view_path, stylesheet=stylesheet, stylesheet_spec=stylesheet_spec)
        viewmodel = viewmodel_cls(view)
        self.register(name or prefix, view, viewmodel)
        logger.debug("loaded {!r} from {}", name or prefix, view_path)
        return view, viewmodel

    def show(self, name: str) -> Window:
        """Shows the view registered under `name` in the app's window: its
        root is attached, and the screen shown before it is detached (kept
        alive, with its state and bindings). Returns the window, the same one
        every time.

        A jump, not a step in the history: it pushes nothing and calls
        no `on_navigated`, and it replaces the current history entry, so
        `back()` leaves it for the entry before. `navigate` records a step.
        """
        window = self._show(name)
        if self._at < 0:
            self._history, self._at = [(name, {})], 0
        else:
            self._history[self._at] = (name, {})
        self._sync_history()
        return window

    def navigate(self, name: str, /, **params: Any) -> Window:
        """Shows the screen registered under `name` as a step in the history
: `back()` returns from it. Its ViewModel's `on_navigated(params)`,
        if it has one, is called first with `params` (a dict). Forward
        entries are dropped, as a browser does; navigating to the entry
        already showing (the same screen and params) does nothing. `name`
        is positional-only, so a param can be called `name` too."""
        entry = (name, params)
        if 0 <= self._at and self._history[self._at] == entry:
            return self._window
        window = self._arrive(entry)
        del self._history[self._at + 1:]
        self._history.append(entry)
        self._at = len(self._history) - 1
        self._sync_history()
        return window

    def route(self, pattern: str, name: str) -> None:
        """Adds a route: a pattern like `"notes/{id}"` for the screen
        registered (now or later) under `name`. A `{param}` segment is a
        string param, `{param:int}` an `int`; the others must match
        exactly. Routes are tried in the order they were added."""
        segments: list[Any] = []
        seen: set[str] = set()
        for part in _route_parts(pattern):
            if part.startswith("{") and part.endswith("}"):
                param, _, converter = part[1:-1].partition(":")
                if not param.isidentifier() or converter not in ("", "int"):
                    raise ValueError(f"route {pattern!r}: {part!r} isn't {{name}} or {{name:int}}")
                if param in seen:
                    raise ValueError(f"route {pattern!r}: {param!r} appears twice")
                seen.add(param)
                segments.append((param, converter or None))
            elif not part or "{" in part or "}" in part:
                raise ValueError(f"route {pattern!r}: {part!r} isn't a segment")
            else:
                segments.append(part)
        self._routes.append(_Route(pattern, name, segments))

    def navigate_to(self, route: str) -> Window:
        """Navigates to the screen the first matching route names, with the
        params it reads from `route` (a deep link, say `"notes/42"`).
        Raises `KeyError` when no route matches."""
        parts = _route_parts(route)
        for candidate in self._routes:
            params = candidate.match(parts)
            if params is not None:
                return self.navigate(candidate.name, **params)
        raise KeyError(f"no route matches {route!r}")

    @property
    def location(self) -> str | None:
        """The screen showing, as a route string (for saving where the
        user was): from the first route of its screen that reads its
        params back exactly, or `None` if none does."""
        if self._at < 0:
            return None
        name, params = self._history[self._at]
        for candidate in self._routes:
            if candidate.name != name:
                continue
            text = "/".join(seg if isinstance(seg, str) else str(params.get(seg[0], "")) for seg in candidate.segments)
            if candidate.match(_route_parts(text)) == params:
                return text
        return None

    def back(self) -> bool:
        """Shows the history's previous entry, calling its ViewModel's
        `on_navigated` with that entry's params. Returns whether it moved."""
        return self._step(-1)

    def forward(self) -> bool:
        """Shows the entry `back()` left, if any. Returns whether it moved."""
        return self._step(1)

    def _step(self, by: int) -> bool:
        to = self._at + by
        if not 0 <= to < len(self._history):
            return False
        self._arrive(self._history[to])
        self._at = to
        self._sync_history()
        return True

    def _arrive(self, entry: tuple[str, dict[str, Any]]) -> Window:
        name, params = entry
        registered = self._registered.get(name)
        if registered is None:
            raise KeyError(f"no view registered under {name!r} -- call register() first")
        hook = getattr(registered.viewmodel, "on_navigated", None)
        if hook is not None:
            hook(dict(params))  # a copy: the history's entry stays as it was
        return self._show(name)

    def _history_key(self, event: Any) -> None:
        if not event.alt or event.ctrl or event.meta or event.shift or event.key not in ("arrow_left", "arrow_right"):
            return
        target = event.target
        if target is not None and target.get("kind") in ("text_input", "terminal"):
            return  # there Option+Left moves by word (macOS)
        if event.key == "arrow_left":
            self.back()
        else:
            self.forward()

    def _history_button(self, event: Any) -> None:
        if event.button == "back":
            self.back()
        elif event.button == "forward":
            self.forward()

    def _sync_history(self) -> None:
        def sync() -> None:  # together, so a follower never sees one updated and not the other
            self.can_go_back.set(self._at > 0)
            self.can_go_forward.set(self._at < len(self._history) - 1)
        batch(sync)

    def _show(self, name: str) -> Window:
        registered = self._registered.get(name)
        if registered is None:
            raise KeyError(f"no view registered under {name!r} -- call register() first")
        previous = self._registered[self._current].view.root if self._current not in (None, name) else None
        root = registered.view.root
        if self._shell is not None:  # M45: the shell places it (in its content, or as a center tab)
            self._shell.show_screen(root, name, previous)
        else:
            if previous is not None:
                previous.remove()  # detached, kept alive with its state
            if root.parent() is None:
                self._window.root.add_child(root)
        self._current = name
        if self._navigation is not None and name in self._navigation[1]:
            rail, screens = self._navigation
            rail.selected.set(screens.index(name))  # the rail follows, without calling its handler (M52)
        logger.debug("showing {!r}", name)
        return self._window

    @property
    def window(self) -> Window:
        """The app's one window (it exists from the start)."""
        return self._window

    def use_shell(self, shell: Any) -> None:
        """Shows screens inside `shell.content`: an
        `AppShell` built on this app's window -- a top app bar, navigation,
        docked panels and a status bar around the screens. A screen already
        showing moves into it."""
        if getattr(shell, "window", None) is not self._window:
            raise ValueError("App.use_shell: build the shell on this app's window (AppShell(app.window, ...))")
        self._shell = shell
        if self._current is not None:
            root = self._registered[self._current].view.root
            if root.parent() is not None:
                root.remove()
            shell.show_screen(root, self._current)

    def load_shell(self, path: str | Path, viewmodel: Any = None) -> Any:
        """Builds the app shell a `*_Shell.yaml` describes -- its top bar,
        navigation rail, status bar, docked zones, center tabs and panels
 -- and shows screens in it, as `use_shell` does. A panel is
        the screen registered under its name, or else `<Name>_View.yaml`
        (and `<Name>_ViewModel.py`) next to the shell file, registered under
        it. Choosing a rail item shows its screen, or calls `viewmodel`'s
        `on_navigate` method. Returns the `AppShell`. Raises
        `tesserae.shell_file.ShellSpecError` (a `ValueError`) naming the
        file and key for a mistake."""
        from tesserae.shell_file import bind_navigation, build_shell, check_references, load_shell_spec, place_panels

        path = Path(self._named("shell", path))
        spec = load_shell_spec(path)
        check_references(self, spec, path, viewmodel)  # before anything is built
        shell = build_shell(self, spec)
        self._shell_file, self._shell_spec, self._shell_viewmodel = path, spec, viewmodel
        self.use_shell(shell)
        place_panels(self, shell, spec, path)
        bind_navigation(self, shell, spec, path, viewmodel)
        logger.info("loaded the app shell from {}", path)
        return shell

    def screen(self, name: str) -> tuple[Any, Any]:
        """The `(view, viewmodel)` registered under `name` -- by `register`,
        `load`, or a shell file's panels, whose ViewModels the app
        builds; `viewmodel` is `None` for a view with none."""
        registered = self._registered.get(name)
        if registered is None:
            raise KeyError(f"no view registered under {name!r} -- call register() first")
        return registered.view, registered.viewmodel

    @classmethod
    def of(cls, view: Any) -> "App | None":
        """The live app whose window `view` (a view, a component, or a
        window) is on, or `None`: for a ViewModel's constructor,
        before `super().__init__(view)` gives it `self.app`."""
        return app_of(getattr(view, "window", view))

    @property
    def current(self) -> str | None:
        """The name last passed to `show()`, or `None` before the first
        real call -- lets a registered handler ask "which screen is this,
        anyway" without the app keeping its own separate bookkeeping.
        """
        return self._current

    # -- the window (0.3.0 M2: custom windowing, `tre` 0.5.0) ----------------

    #: The resize border of an undecorated window whose app gives none.
    DEFAULT_RESIZE_BORDER = 6

    def _resize_for(self, decorations: bool) -> int:
        if self._resize_border is not None:
            return self._resize_border
        return 0 if decorations else self.DEFAULT_RESIZE_BORDER

    @property
    def decorations(self) -> bool:
        """Whether the OS draws the title bar and borders. `False` leaves them
        to the app (on macOS the title bar stays, transparent, with the
        traffic lights); it can change while the app runs."""
        return bool(self._window.get("decorations"))

    @decorations.setter
    def decorations(self, value: bool) -> None:
        self._window.set(decorations=bool(value), resize_border=self._resize_for(bool(value)))
        self._decorated.set(bool(value))

    @property
    def resize_border(self) -> int:
        """How many pixels along each edge resize an undecorated window
        (`tre` turns it off while maximized or fullscreen, and on macOS).
        Unless set, 6 while undecorated and 0 otherwise."""
        return int(self._window.get("resize_border"))

    @resize_border.setter
    def resize_border(self, value: int | None) -> None:
        self._resize_border = _non_negative("resize_border", value, allow_none=True)
        self._window.set(resize_border=self._resize_for(self.decorations))

    @property
    def min_width(self) -> int:
        """The narrowest the user can resize the window to (0 for no limit)."""
        return int(self._window.get("min_width"))

    @min_width.setter
    def min_width(self, value: int) -> None:
        self._window.set(min_width=_non_negative("min_width", value))

    @property
    def min_height(self) -> int:
        """The shortest the user can resize the window to (0 for no limit)."""
        return int(self._window.get("min_height"))

    @min_height.setter
    def min_height(self, value: int) -> None:
        self._window.set(min_height=_non_negative("min_height", value))

    @property
    def fullscreen(self) -> bool:
        """Whether the window fills its monitor, borderless."""
        return bool(self._window.get("fullscreen"))

    @fullscreen.setter
    def fullscreen(self, value: bool) -> None:
        self._window.set(fullscreen=bool(value))
        self._fullscreen.set(bool(value))

    @property
    def window_border(self) -> bool:
        """Whether an undecorated window gets its 1 px border (on by
        default): around the window, in the theme's `outline_variant`, a
        node of class `window_border` a theme or stylesheet can restyle.
        It's hidden while maximized or fullscreen, and on macOS, where the
        OS draws the window's frame."""
        return self._window_border.get()

    @window_border.setter
    def window_border(self, value: bool) -> None:
        self._window_border.set(bool(value))

    def _show_border(self) -> None:
        shown = (self._window_border.get() and not self._decorated.get() and not self._maximized.get()
                 and not self._fullscreen.get() and self.platform != "macos")
        if shown and self._border is None:
            self._border = self._build_border()
        if self._border is not None:
            self._border.root.set(visible=shown)

    def _build_border(self) -> Any:
        style: dict[str, Any] = {"position": "absolute", "x": 0, "y": 0, "width": "100%", "height": "100%",
                                 "z_index": 1000}
        theme = self._view_theme()
        if "theme_seed" not in theme and self._default_theme_spec is None and self._custom_theme_spec is None:
            # an unthemed app has no roles to resolve: MD3's baseline colour
            style.update(background="transparent", border_width=1,
                         border_color="#{:02X}{:02X}{:02X}{:02X}".format(*tokens.BASELINE["outline_variant"]))
        spec = {"id": "window_border", "kind": "Rect", "classes": ["window_border"], "style": style}
        if self._stylesheet_spec is not None:
            theme["stylesheet_spec"] = self._stylesheet_spec
        view = TesseraeView(spec, window=self._window, **theme)
        view.root.set(hit_testable=False, a11y_hidden=True)  # drawn over the app, never in its way
        self._built.append(_Built(view))  # re-themed with the app's views
        self._window.root.add_child(view.root)
        return view

    @property
    def system_menu(self) -> bool:
        """Whether a secondary press on the title bar opens the OS's window
        menu (Windows, and Wayland compositors with one). Off by default,
        so a right-click there is the app's."""
        return bool(self._window.get("system_menu"))

    @system_menu.setter
    def system_menu(self, value: bool) -> None:
        self._window.set(system_menu=bool(value))

    @property
    def platform(self) -> str:
        """`"windows"`, `"macos"`, `"wayland"` or `"x11"`."""
        return str(self._window.get("platform"))

    def minimize(self) -> None:
        """Minimizes the window (before `run()`, it opens minimized)."""
        self._window.minimize()
        self._sync_maximized()

    def maximize(self) -> None:
        """Maximizes the window (before `run()`, it opens maximized)."""
        self._window.maximize()
        self._sync_maximized()

    def restore(self) -> None:
        """Restores the window from maximized or minimized."""
        self._window.restore()
        self._sync_maximized()

    def toggle_maximized(self) -> None:
        """Maximizes the window, or restores it if it's maximized: a title
        bar's maximize button."""
        if self._window.get("maximized"):
            self.restore()
        else:
            self.maximize()

    def _on_titlebar_inset(self, event: Any) -> None:
        self._titlebar_inset.set(_inset(event.titlebar_inset))
        self._native_controls.set(bool(self._window.get("native_controls")))

    def _sync_maximized(self) -> None:
        # Before `run()` these set how the window opens, and no event says
        # so; an open window's state is `tre`'s event's to report (it may
        # still read the old state here, and the event follows).
        self._maximized.set(bool(self._window.get("maximized")))

    def close(self) -> None:
        """Closes the window as the user's close would: `close_requested`
        fires first, so an app's "save changes?" check still runs and can
        cancel it. It happens on the loop's next turn."""
        self._window.close()

    def set_icon(self, icon: str | Path | None) -> None:
        """The window's icon, from an image file (a PNG, best square), or
        `None` for none. Shown on Windows and X11; Wayland and macOS take
        an app's icon from its desktop entry or bundle, as `tesserae build
        --installer` makes them."""
        if icon is None:
            self._window.set(icon=None)
            return
        from PIL import Image

        path = Path(icon)
        try:
            with Image.open(path) as image:
                rgba = image.convert("RGBA")
        except (OSError, ValueError) as exc:
            raise ValueError(f"App: icon {str(path)!r} isn't an image file ({exc})") from None
        self._window.set(icon=(rgba.tobytes(), rgba.width, rgba.height))

    def _screens_never_shown(self) -> bool:
        """The mistake `run()` reports (0.3.1): screens were registered and
        none was shown, with nothing else on the window. A window with no
        screens at all runs: an app built in Python starts empty and adds
        nodes to `app.window.root`. The window border an undecorated app
        draws is a child of the root too, and doesn't count as content."""
        if self._current is not None or not self._registered:
            return False
        return len(self._window.root.children()) <= (1 if self._border is not None else 0)

    def thread_handle(self) -> Any:
        """`tre`'s thread-safe `LoopHandle` for this app: the one
        object that may cross threads. `handle.call_soon(fn)` runs `fn`
        (no arguments) on the event-loop thread at the next frame, waking
        an idle loop -- the way for a background thread to touch a view,
        since views may only be used from the thread that created them.
        Usable before `run()`; a callable queued then runs on the first
        frame.
        """
        if self._tre_app is None:
            self._tre_app = _TreApp()
        return self._tre_app.thread_handle()

    def _start_watchers(self, handle: Any) -> list[Any]:
        """Every hot-reload watcher `run(hot_reload=True)` needs, started
        on `handle`."""
        watchers: list[Any] = []
        for name, registered in self._registered.items():
            # M48: a screen built from a file -- by `load()` or `build_view()`,
            # then `register()` -- keeps that file as `view.path`
            path = getattr(registered.view, "path", None)
            if path is not None:
                watchers.append(ViewWatcher(registered.view, path, project=self.project))
            else:
                logger.info("hot reload: screen {!r} isn't watched -- it was built from a spec, not a file", name)
        if self._stylesheet_file is not None:
            path = Path(self._stylesheet_file).resolve()
            watchers.append(
                FileWatcher(
                    [path],
                    lambda path=path: load_stylesheet(path),
                    _from_file(path, "re-styled the screens using the default stylesheet", self.set_stylesheet_spec),
                    name="stylesheet",
                )
            )
        for path in self._own_sheets:
            watchers.append(
                FileWatcher(
                    [path],
                    lambda path=path: load_stylesheet(path),
                    _from_file(
                        path,
                        "re-styled the screens loaded with this stylesheet",
                        lambda spec, path=path: self._set_own_stylesheet(path, spec),
                    ),
                    name=f"stylesheet:{path.name}",
                )
            )
        theme_files = [f for f in self._theme_files.values() if f is not None]
        if theme_files:
            watchers.append(
                FileWatcher(
                    theme_files,
                    self._read_theme_files,
                    self._apply_theme_files,
                    name="theme",
                )
            )
        shell_watcher = None
        if self._shell_file is not None:  # M52: the shell file, patched in place
            path = self._shell_file.resolve()
            shell_watcher = FileWatcher(
                [path], lambda path=path: load_shell_spec(path), self._reload_shell, name="shell")
            watchers.append(shell_watcher)
        for watcher in watchers:
            watcher.start(handle)
        self._hot_handle, self._watchers = handle, watchers
        if shell_watcher is not None:
            logger.info("hot reload: watching the shell file {}", self._shell_file.name)
        for path in sorted({c.path.resolve() for c in self._live_components()}):
            self.watch_component(path)
        views = sum(isinstance(w, ViewWatcher) and not isinstance(w, ComponentWatcher) for w in watchers)
        logger.info(
            "hot reload on: watching {} screen(s) and {} theme/stylesheet file(s)",
            views,
            sum(len(w.files) for w in watchers if not isinstance(w, ViewWatcher) and w is not shell_watcher),
        )
        return watchers

    def _stop_watchers(self) -> None:
        """Stops every hot-reload watcher, including component watchers
        started while the app ran; a later `instantiate` watches nothing."""
        for watcher in self._watchers:
            watcher.stop()
        self._hot_handle, self._watchers, self._component_watchers = None, [], {}

    def _live_components(self, path: Path | None = None) -> list[Any]:
        """Every live component built from a file (`tesserae.instantiate`)
        in the app's screens and views, nested ones included -- or only
        those built from `path` -- and, since M61, in any other view
        on the app's window, as `instantiate` registered them."""
        views = [r.view for r in self._registered.values()] + [b.view for b in self._built]
        views += [f for f in self._followers if isinstance(f, TesseraeView)]
        found: list[Any] = []
        seen: set[int] = set()
        stack = list(views)
        while stack:
            view = stack.pop()
            view._prune_components()
            for component in view._components:
                if id(component) in seen:
                    continue
                seen.add(id(component))
                stack.append(component)
                if component.path is not None and (path is None or component.path.resolve() == path):
                    found.append(component)
        for component in list(self._instances):  # M61: in a view the app doesn't otherwise know
            if id(component) in seen or not component._follow_alive():
                continue
            seen.add(id(component))
            if component.path is not None and (path is None or component.path.resolve() == path):
                found.append(component)
        return found

    def watch_component(self, path: str | Path) -> None:
        """While `run(hot_reload=True)` runs, watches a component file and
        reloads every live instance of it on change;
        `tesserae.instantiate` calls it, so a component first added while
        the app runs is watched too. Once per file; outside hot reload,
        nothing happens."""
        if self._hot_handle is None:
            return
        path = Path(path).resolve()
        if path in self._component_watchers:
            return
        watcher = ComponentWatcher(path, lambda path=path: self._live_components(path), project=self.project)
        watcher.start(self._hot_handle)
        self._component_watchers[path] = watcher
        self._watchers.append(watcher)
        logger.info("hot reload: watching component {} ({} instance(s))", path.name, len(self._live_components(path)))

    def _reload_shell(self, spec: dict[str, Any]) -> None:
        """Applies an edited shell file: what can change in place
        is patched; a structural change is logged as needing a restart.
        A panel or `on_navigate` it can't find fails before anything
        changes."""
        from tesserae.shell_file import check_references, reload_shell

        path = self._shell_file
        check_references(self, spec, path, self._shell_viewmodel)
        needs = reload_shell(self, self._shell, self._shell_spec, spec, path, self._shell_viewmodel)
        self._shell_spec = spec
        logger.info("reloaded the shell from {}", path)
        for change in needs:
            logger.warning("the shell file {} changed ({}): restart the app to see it", path.name, change)

    def _apply_theme_files(self, specs: tuple[Any, Any]) -> None:
        self.set_theme_specs(*specs)
        files = ", ".join(str(f) for f in self._theme_files.values() if f is not None)
        logger.info("re-themed the app from {}", files)

    def run(self, max_frames: int | None = None, *, hot_reload: bool = False,
            keepalive: bool | float = False) -> None:
        """The one blocking call -- opens the real `Window` and runs `tre`'s
        own real render loop, showing the screen `show()` made current and
        any nodes added to `app.window.root` by calls. Since 0.3.1 an app
        needs no screen: an empty window runs. Registering screens and not
        showing one is still the `RuntimeError` it was. `max_frames`
        is the identical headless-CI-safe convention `tre`'s own examples
        already use (TRE v1 finding #261) -- omit it for a real,
        interactive run that exits only when the window closes. With no
        display it returns at once; a window whose GPU can't be set up
        raises `RuntimeError` (`tre` 0.4.0).

        `hot_reload=True` watches every screen built from a file --
        by `load()`, or by `build_view()` and given to `register()`
        -- its view file and everything it was built from, and reloads it
        in place while the app runs, its ViewModel and bindings kept. Each
        screen gets a `ViewWatcher` on a background thread (`watchfiles`),
        which hands its reloads to the event loop through `tre`'s
        thread-safe `App.thread_handle()`. A failed reload is
        logged; the app keeps running. A screen built from a spec
        dict has no file, so it isn't watched, and the log says so. A
        component built with `tesserae.instantiate` is watched by its file
        too, one watcher for all its live instances, including ones added
        while the app runs. So is a shell file from `load_shell`:
        an edit is patched in place, and a structural one is logged as
        needing a restart.

        M31: the theme files given to `App(default_theme=, custom_theme=)`
        are watched too. An edit re-reads them on the watcher thread and
        re-themes every screen `build_view()`/`load()` made with
        `set_theme_specs`. So are stylesheet files: the
        default from `App(stylesheet=)` (re-applied, with
        `set_stylesheet_spec`, to every screen using it) and each screen's
        own `stylesheet=` file (re-applied to the screens built with it).

        `keepalive` (0.3.1, #77) keeps the window ticking about 50 times a
        second (a number is the seconds between ticks), for code that wants
        the loop woken regularly. It is off by default since 0.3.2:
        `tre` 0.5.1 lets other Python threads run while the window sits
        idle, so a hot-reload watcher, or any thread calling
        `thread_handle().call_soon`, needs no tick (0.3.1 ticked by default
        with `hot_reload`, for `tre` 0.5.0.x). Each tick sleeps on the loop
        thread, so input can wait up to a tick, and an idle window costs
        about half a percent of one core.

        M77: `TESSERAE_MAX_FRAMES=n` in the environment stops a run with no
        `max_frames` after `n` frames -- how `tesserae build --check` and CI
        run a built executable and see it exit. A frozen app (one
        `tesserae build` made) has no source files to edit, so
        `hot_reload` does nothing there. `TESSERAE_FRAMES_REPORT=<file>`
        writes how many frames the run drew to that file, so a check can
        tell a run that drew from one that found no display and returned.
        """
        if self._screens_never_shown():
            raise RuntimeError("App.run() called before show(): screens are registered but none is showing -- "
                               "show(name) one, or add nodes to app.window.root")
        if max_frames is None and os.environ.get("TESSERAE_MAX_FRAMES"):
            try:
                max_frames = int(os.environ["TESSERAE_MAX_FRAMES"])
            except ValueError:
                raise ValueError(f"TESSERAE_MAX_FRAMES must be a whole number of frames, "
                                 f"got {os.environ['TESSERAE_MAX_FRAMES']!r}") from None
        if hot_reload and getattr(sys, "frozen", False):
            logger.info("hot reload is off in a built app: there are no source files to watch")
            hot_reload = False
        interval = _keepalive_interval(keepalive)
        if self._tre_app is None:
            self._tre_app = _TreApp()
        tre_app = self._tre_app
        tre_app.add_window(self._window)
        tre_app.thread_handle().call_soon(self._adopt_os_appearance)  # on the first frame (M53 Q2)
        report = os.environ.get("TESSERAE_FRAMES_REPORT")
        drawn = [0]
        if report:
            handle = tre_app.thread_handle()

            def count() -> None:  # once a frame, each call queuing the next
                drawn[0] += 1
                handle.call_soon(count)

            handle.call_soon(count)
        ticking = [interval is not None]
        try:
            if interval is not None:
                tick_handle = tre_app.thread_handle()

                def tick() -> None:  # the sleep lets other threads take the GIL; each call queues the next
                    if ticking[0]:
                        time.sleep(interval)
                        tick_handle.call_soon(tick)

                tick_handle.call_soon(tick)
            if hot_reload:
                self._start_watchers(tre_app.thread_handle())
            tre_app.run(max_frames=max_frames)
        finally:
            ticking[0] = False
            self._stop_watchers()
            if report:
                Path(report).write_text(str(drawn[0]), encoding="utf-8")
            # A later run() starts from a fresh tre App, as before
            # thread_handle() existed; a handle from this run is spent.
            self._tre_app = None
