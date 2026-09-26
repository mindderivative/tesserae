"""`App` -- the real, single Tesserae entry point every real `app.py`
owns exactly one of, per the user's own explicit design requirement:
"app.py should be the entry point for the app... this allows for
switching of current views without needing to bootstrap each
view/viewModel."

Owns a registry of named `(View, ViewModel)` pairs -- each `*_View.yaml`
+ `*_ViewModel.py` file pair a real app registers once, up front -- and
exactly one live `tre.Window`, created with the `App`. Screens are built
into it by Tesserae (M37); `App.show(name)` attaches that screen's root
to the window and detaches the one shown before. Neither a `View` nor
its `ViewModel` is ever re-parsed,
re-attached, or otherwise re-bootstrapped by a later `show()` call --
each stays alive, its own `Signal` subscriptions intact, for the whole
life of the `App`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from loguru import logger
from tre import App as _TreApp
from tre import Window

from tesserae.naming import check_naming_convention
from tesserae.spec import ViewWatcher, load_stylesheet, load_theme
from tesserae.view import View as TesseraeView
from tesserae.spec.watch import FileWatcher

#: `Window.set_theme` requires a seed even when the custom theme's own
#: `seed:` overrides it; `_window_theme` passes this one then.
_OVERRIDDEN_SEED = (0, 0, 0, 0xFF)


@dataclass
class _Registered:
    view: Any
    viewmodel: Any
    #: The `*_View.yaml` it was loaded from -- set by `load()`, so
    #: `run(hot_reload=True)` knows what to watch. `None` for a pair
    #: given to `register()` directly.
    path: Path | None = None


@dataclass
class _Built:
    """A view `App.build_view()` made -- one a theme or stylesheet reload
    reaches (M31)."""

    view: Any
    #: `True` if it was given its own stylesheet (file or dict) instead
    #: of the app's default.
    own_stylesheet: bool = False
    #: That own stylesheet's file, resolved, if it came from one.
    stylesheet_file: Path | None = None


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


def _file_or_spec(owner: str, file_arg: str, file: Any, spec: Any, loader: Any) -> Any:
    """One `*=` file path / `*_spec=` dict pair -> the dict (or `None`).
    The file is read here, by Tesserae; `tre` only ever gets the dict."""
    if file is not None and spec is not None:
        raise ValueError(f"{owner}: pass {file_arg}= or {file_arg}_spec=, not both")
    return loader(file) if file is not None else spec


class App:
    """`width`/`height`/`title` describe the one real `Window` this
    `App` opens the first time `show()` is called -- every registered
    view is shown inside that same window, at whatever size it already
    is, not its own independent size (matching `Window.show_view`'s own
    real, stated scope: only the *currently* active view's `width`/
    `height` are kept in sync with the window).

    M30: the theme is app-wide -- `theme_seed=`, `dark=`,
    `default_theme=`/`custom_theme=` (file paths) or their `*_spec=`
    dict forms apply to every screen `build_view()`/`load()` builds, and
    (M31) to the window itself. `tre` keeps the two apart: a `View`'s
    theme restyles its YAML nodes, while the window's theme -- set only by
    `Window.set_theme`, never by building a `View` -- is what imperative
    `tesserae.widgets` and interaction tints use. `Window.show_view` never
    switches it, so the theme is one per app, not per screen: `show()`
    gives the window the same theme the screens have.

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
    ) -> None:
        self._width = width
        self._height = height
        self._title = title
        self._theme_seed = theme_seed
        if dark not in (True, False, "system"):
            raise ValueError(f'App: dark must be True, False or "system", got {dark!r}')
        #: "system" follows the OS; True/False is the app's own fixed choice (M38).
        self._dark_mode: bool | str = dark
        #: The appearance in use. "system" starts dark: 0.3.4 can't read the
        #: OS's appearance until its first `color_scheme` event (M38 Q3).
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
        # M37: the app's one window exists from the start, so screens are built
        # straight into it. Like a `Window.from_view` root: no padding, and a
        # screen root with no size of its own is sized to its content.
        self._window: Window = Window(width=width, height=height, title=title)
        self._window.root.set(padding_top=0, padding_right=0, padding_bottom=0, padding_left=0,
                              align_items="flex_start")
        self._current: str | None = None
        self._tre_app: _TreApp | None = None
        self._set_window_theme()  # tesserae.widgets' composed widgets read the window's theme until M41
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
        screen and the window in place; `"system"` goes back to following
        the OS from its next switch."""
        if dark not in (True, False, "system"):
            raise ValueError(f'App.set_dark: dark must be True, False or "system", got {dark!r}')
        self._dark_mode = dark
        if dark != "system":
            self._apply_dark(bool(dark))

    def _on_color_scheme(self, event: Any) -> None:
        """The OS switched between light and dark. `tre` has already flipped
        the window's own theme (the legacy widgets and hover tints read it):
        following the OS, the whole app follows; with a fixed choice, the
        window is put back to it."""
        if self._dark_mode == "system":
            self._apply_dark(bool(event.dark))
        else:
            self._set_window_theme()

    def _apply_dark(self, dark: bool) -> None:
        if dark == self._dark:
            self._set_window_theme()
            return
        old_theme = self._view_theme()
        self._dark = dark
        new_theme = self._view_theme()
        try:
            _apply_all(
                [b.view for b in self._built],
                lambda view: view.set_theme(**new_theme),
                lambda view: view.set_theme(**old_theme),
            )
        except Exception:
            self._dark = not dark
            raise
        self._set_window_theme()
        logger.info("switched to the {} scheme", "dark" if dark else "light")

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

    def _window_theme(self) -> dict[str, Any] | None:
        """The app's theme as `Window.set_theme` arguments, resolved the
        way a `View` resolves it -- or `None` if it names no seed at all,
        leaving the window unthemed as before.

        `tre`'s two theme entry points differ (M31): a `View` takes its
        seed from `theme_seed`, else the custom theme's `seed:`, else the
        default theme's, and applies both themes' `colors:`; `Window.
        set_theme` lets the custom theme's `seed:` beat its `seed`
        argument and ignores the default theme's `seed:` and `colors:`.
        So the custom theme handed to the window is rewritten to say what
        the view would use. `tre` still does all the parsing.
        """
        default = self._default_theme_spec or {}
        custom = dict(self._custom_theme_spec or {})
        if self._theme_seed is not None:
            custom.pop("seed", None)
            seed = self._theme_seed
        else:
            seed = _OVERRIDDEN_SEED
            if "seed" not in custom:
                if "seed" not in default:
                    return None
                custom["seed"] = default["seed"]
        colors = {**(default.get("colors") or {}), **(custom.get("colors") or {})}
        if colors:
            custom["colors"] = colors
        theme: dict[str, Any] = {"seed": seed, "dark": self._dark}
        if self._default_theme_spec is not None:
            theme["default_theme_spec"] = self._default_theme_spec
        if custom:
            theme["custom_theme_spec"] = custom
        return theme

    def _set_window_theme(self) -> None:
        theme = self._window_theme()
        if self._window is not None and theme is not None:
            self._window.set_theme(**theme)

    def _read_theme_files(self) -> tuple[Any, Any]:
        """Re-reads the theme files (a watcher-thread job, M31); a theme
        given as a `*_spec=` dict is kept as it is."""
        files = self._theme_files
        default = load_theme(files["default"]) if files["default"] is not None else self._default_theme_spec
        custom = load_theme(files["custom"]) if files["custom"] is not None else self._custom_theme_spec
        return default, custom

    def set_theme_specs(self, default_theme_spec: Any, custom_theme_spec: Any) -> None:
        """Re-themes the running app in place (M31): every view
        `build_view()`/`load()` made, and the window. Both theme dicts
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
            new_theme = self._view_theme()
            _apply_all(
                [b.view for b in self._built],
                lambda view: view.set_theme(**new_theme),
                lambda view: view.set_theme(**old_theme),
            )
            self._set_window_theme()
        except Exception:
            self._default_theme_spec, self._custom_theme_spec = previous
            raise

    def set_stylesheet_spec(self, stylesheet_spec: dict[str, Any] | None) -> None:
        """Replaces the app's default stylesheet in place (M31 Phase 2):
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
            built.view = TesseraeView(Path(view_path), window=self._window, **kwargs)
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
        stylesheet (M30). A view built any other way keeps whatever theme
        it was built with.
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

    def load(
        self,
        view_path: str | Path,
        viewmodel_cls: type,
        name: str | None = None,
        *,
        stylesheet: str | Path | None = None,
        stylesheet_spec: dict[str, Any] | None = None,
    ) -> tuple[Any, Any]:
        """Loads a `*_View.yaml` + `*_ViewModel.py` pair and registers it
        -- the real, enforced-at-runtime counterpart to `README.md`'s own
        documented naming convention (previously convention-only, not
        checked). Mirrors pyCopper's own real, validated design (see
        `ARCHITECTURE.md`): a `ViewModel` is scoped one-per-view-file, so
        catching a mismatched pair immediately, at load time, is worth
        more than a cryptic failure much later when a handler name
        doesn't resolve.

        `tre.View` doesn't expose its own source path back to Python
        (confirmed by reading `view.rs` before writing this -- `path` is
        a private Rust field), so this takes `view_path` directly rather
        than trying to recover it from an already-constructed `View` --
        the caller already has it (it's what they'd otherwise pass to
        `View(...)` themselves).

        `name` defaults to the shared prefix (e.g. `"Counter"` for
        `Counter_View.yaml`/`Counter_ViewModel.py`) -- only needed
        explicitly if two different pairs would otherwise collide on it.

        Built with `build_view` -- `tesserae.spec.load_view` under the
        hood, so `include:`/`component:`/images are handled by Tesserae --
        using the app's theme and its default stylesheet, or this
        screen's own `stylesheet=`/`stylesheet_spec=` if given (M30).

        Returns the constructed `(view, viewmodel)` pair -- most real
        `app.py` scripts won't need it (everything from here on happens
        through `show()`/registered handlers), but a caller that wants a
        `Node` handle to dispatch a synthetic click/test against, or the
        `ViewModel` itself to read a `Signal` back, still can.
        """
        view_path = Path(view_path)
        prefix = check_naming_convention(view_path, viewmodel_cls)

        view = self.build_view(view_path, stylesheet=stylesheet, stylesheet_spec=stylesheet_spec)
        viewmodel = viewmodel_cls(view)
        self.register(name or prefix, view, viewmodel)
        self._registered[name or prefix].path = view_path
        logger.debug("loaded {!r} from {}", name or prefix, view_path)
        return view, viewmodel

    def show(self, name: str) -> Window:
        """Shows the view registered under `name` in the app's window: its
        root is attached, and the previously shown screen's detached (kept
        alive, with its state and bindings). Returns the window, the same one
        every time.
        """
        registered = self._registered.get(name)
        if registered is None:
            raise KeyError(f"no view registered under {name!r} -- call register() first")
        if self._current is not None and self._current != name:
            self._registered[self._current].view.root.remove()  # detached, kept alive with its state
        root = registered.view.root
        if root.parent() is None:
            self._window.root.add_child(root)
        self._current = name
        logger.debug("showing {!r}", name)
        return self._window

    @property
    def current(self) -> str | None:
        """The name last passed to `show()`, or `None` before the first
        real call -- lets a registered handler ask "which screen is this,
        anyway" without the app keeping its own separate bookkeeping.
        """
        return self._current

    def thread_handle(self) -> Any:
        """`tre`'s thread-safe `LoopHandle` for this app (tre M87): the one
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
        for registered in self._registered.values():
            if registered.path is not None:
                watchers.append(ViewWatcher(registered.view, registered.path))
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
        for watcher in watchers:
            watcher.start(handle)
        views = sum(isinstance(w, ViewWatcher) for w in watchers)
        logger.info(
            "hot reload on: watching {} screen(s) and {} theme/stylesheet file(s)",
            views,
            sum(len(w.files) for w in watchers if not isinstance(w, ViewWatcher)),
        )
        return watchers

    def _apply_theme_files(self, specs: tuple[Any, Any]) -> None:
        self.set_theme_specs(*specs)
        files = ", ".join(str(f) for f in self._theme_files.values() if f is not None)
        logger.info("re-themed the app from {}", files)

    def run(self, max_frames: int | None = None, *, hot_reload: bool = False) -> None:
        """The one blocking call -- opens the real `Window` `show()` has
        already built and runs `tre`'s own real render loop. `max_frames`
        is the identical headless-CI-safe convention `tre`'s own examples
        already use (TRE v1 finding #261) -- omit it for a real,
        interactive run that exits only when the window closes.

        `hot_reload=True` (M29) watches every screen registered through
        `load()` -- its view file and everything it was built from -- and
        reloads it in place while the app runs. Each screen gets a
        `ViewWatcher` on a background thread (`watchfiles`), which hands
        its reloads to the event loop through `tre`'s thread-safe
        `App.thread_handle()` (tre M87). A failed reload is logged by
        `tre` like a handler's exception; the app keeps running. Screens
        given to `register()` directly have no known file and aren't
        watched.

        M31: the theme files given to `App(default_theme=, custom_theme=)`
        are watched too. An edit re-reads them on the watcher thread and
        re-themes every screen `build_view()`/`load()` made, and the
        window, with `set_theme_specs`. So are stylesheet files: the
        default from `App(stylesheet=)` (re-applied, with
        `set_stylesheet_spec`, to every screen using it) and each screen's
        own `stylesheet=` file (re-applied to the screens built with it).
        """
        if self._current is None:
            raise RuntimeError("App.run() called before show() -- nothing to display yet")
        if self._tre_app is None:
            self._tre_app = _TreApp()
        tre_app = self._tre_app
        tre_app.add_window(self._window)
        watchers: list[Any] = []
        try:
            if hot_reload:
                watchers = self._start_watchers(tre_app.thread_handle())
            tre_app.run(max_frames=max_frames)
        finally:
            for watcher in watchers:
                watcher.stop()
            # A later run() starts from a fresh tre App, as before
            # thread_handle() existed; a handle from this run is spent.
            self._tre_app = None
