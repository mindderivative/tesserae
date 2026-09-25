"""Tesserae's reactivity: `Signal`, `Computed`, `Effect`, `batch`,
`untrack` and `ViewModel` (M35).

Taken over from `tre` (`python/tre/__init__.py` at v0.3.4, MIT, same
author), which moves reactivity out of the engine (`tre` D5) and removes
its copy in 0.3.5. The behavior is `tre`'s exactly:

- `Signal.set`/`update` notify only when the value changes;
- `Computed` recomputes when a dependency changes, and notifies only if
  its own value changed;
- `batch` defers notification and runs each subscriber once;
- `untrack` hides reads from the enclosing scope;
- writing to a `Signal` while it's still notifying its subscribers
  raises a clear error.

Dependency tracking: `get()` records the object on the innermost open
recording frame. `Computed`, `Effect` and `untrack` open frames on this
module's own stack.

Bindings are evaluated by Tesserae (`tesserae.binding`, wired by
`tesserae.View`) in these same frames. (Until M37 Phase 6, a read with no
frame open was passed on to `tre`'s native `_record_read`, so `tre`'s
own `View` bindings tracked Tesserae's signals; no view uses `tre`'s
evaluation any more.)

Tesserae's classes track only each other, not `tre.Signal`, so an app
uses these (`from tesserae import Signal`), not `tre`'s.

Single-threaded, as in `tre`: module-level state, touched only on the
event-loop thread. Tesserae's watcher threads never read or write
signals.
"""

from __future__ import annotations

from typing import Any, Callable

__all__ = ["Computed", "Effect", "Signal", "ViewModel", "batch", "untrack"]

#: The recording stack: one list of read objects per open frame.
_frames: list[list[Any]] = []
_batch_depth = 0
_pending_notifications: list[Any] = []


def _record_read(obj: Any) -> None:
    if _frames:
        frame = _frames[-1]
        if not any(seen is obj for seen in frame):
            frame.append(obj)


def _begin_recording() -> None:
    _frames.append([])


def _end_recording() -> list[Any]:
    return _frames.pop()


def _schedule_notify(signal_like: Any) -> None:
    """Notifies now, or at the end of the outermost `batch()`."""
    if _batch_depth > 0:
        _pending_notifications.append(signal_like)
    else:
        signal_like._notify()


def batch(fn: Callable[[], Any]) -> Any:
    """Runs `fn()` with every `Signal`/`Computed` notification deferred
    until it returns, then runs each affected subscriber once -- not
    once per write, and not once per signal it depends on. Nested
    batches flush when the outermost returns. The flush happens even if
    `fn` raises, and the exception still propagates. Returns `fn()`'s
    result.

    Deduplication is per callback, across every pending signal: a
    `Computed` reading two signals written in one batch recomputes once.
    """
    global _batch_depth
    _batch_depth += 1
    try:
        return fn()
    finally:
        _batch_depth -= 1
        if _batch_depth == 0:
            pending, _pending_notifications[:] = _pending_notifications[:], []
            seen_signals: set[int] = set()
            invoked_callbacks: set[Any] = set()
            for signal_like in pending:
                if id(signal_like) in seen_signals:
                    continue
                seen_signals.add(id(signal_like))
                signal_like._notify(invoked_callbacks)


def untrack(fn: Callable[[], Any]) -> Any:
    """Runs `fn()` and returns its result, without its reads being
    recorded by the enclosing `Computed`, `Effect` or binding."""
    _begin_recording()
    try:
        return fn()
    finally:
        _end_recording()  # discarded: that's the point


class _Notifiable:
    """The subscriber list and notification shared by `Signal` and
    `Computed`. `_subscribe`/`_unsubscribe` are called by bindings, by
    `Repeater`, and by `Computed`/`Effect` tracking their dependencies; not
    public API."""

    def __init__(self) -> None:
        self._subscribers: list[Callable[[], None]] = []
        self._notifying = False

    def _subscribe(self, callback: Callable[[], None]) -> None:
        self._subscribers.append(callback)

    def _unsubscribe(self, callback: Callable[[], None]) -> None:
        """A no-op if `callback` isn't subscribed."""
        try:
            self._subscribers.remove(callback)
        except ValueError:
            pass

    def _notify(self, already_invoked: set[Any] | None = None) -> None:
        """Runs every subscriber once. `already_invoked` is shared across
        one `batch()` flush. Iterates a snapshot, since a subscriber
        (a `Computed` re-tracking) can unsubscribe and resubscribe while
        this runs. Raises if this object is written again while it's
        still notifying, rather than recursing without end."""
        if self._notifying:
            raise RuntimeError(
                f"{type(self).__name__} {self!r} was written to again while still notifying "
                "its own subscribers from an earlier write on the same call stack -- something "
                "invoked during this notification wrote back to it, directly or through a "
                "chain of other Signals/Computeds. If a read caused this Signal to be "
                "over-broadly recorded as a dependency it shouldn't be, wrap that read in "
                "tesserae.untrack(...); otherwise restructure the code so this Signal's own "
                "subscribers don't write back to it."
            )
        self._notifying = True
        try:
            invoked = already_invoked if already_invoked is not None else set()
            for callback in list(self._subscribers):
                if callback in invoked:
                    continue
                invoked.add(callback)
                callback()
        finally:
            self._notifying = False


class Signal(_Notifiable):
    """A reactive value. `get()` records a dependency when read inside a
    `Computed`, an `Effect` or a binding; `set()`/`update()` notify when
    the value actually changes.

    Skipping unchanged writes is what stops a two-way binding recursing:
    the widget's change writes the signal, which updates the widget,
    whose second write is the same value and stops there.
    """

    def __init__(self, value: Any) -> None:
        super().__init__()
        self._value = value

    def get(self) -> Any:
        _record_read(self)
        return self._value

    def set(self, value: Any) -> None:
        if value == self._value:
            return
        self._value = value
        _schedule_notify(self)

    def update(self, fn: Callable[[Any], Any]) -> None:
        """Sets the value to `fn(current)`, e.g. `clicks.update(lambda n:
        n + 1)`, unless that's the value it already holds."""
        new_value = fn(self._value)
        if new_value == self._value:
            return
        self._value = new_value
        _schedule_notify(self)


_UNSET = object()


class Computed(_Notifiable):
    """A derived, cached value. `fn` runs inside a recording frame to find
    its dependencies; when one changes, it runs again, and notifies its
    own subscribers only if the result changed:

        total = Computed(lambda: price.get() * quantity.get())

    It has `Signal`'s `get()`/`_subscribe`/`_unsubscribe` shape, so a
    binding, another `Computed` or an `Effect` can depend on it.
    Dependencies are re-subscribed in full on each recompute.
    """

    def __init__(self, fn: Callable[[], Any]) -> None:
        super().__init__()
        self._fn = fn
        self._dependencies: list[Any] = []
        self._value: Any = _UNSET
        self._recompute()

    def get(self) -> Any:
        _record_read(self)
        return self._value

    def _recompute(self) -> None:
        for dependency in self._dependencies:
            dependency._unsubscribe(self._recompute)
        _begin_recording()
        try:
            new_value = self._fn()
        finally:
            self._dependencies = _end_recording()
        for dependency in self._dependencies:
            dependency._subscribe(self._recompute)
        if new_value != self._value:
            self._value = new_value
            _schedule_notify(self)


class Effect:
    """Runs `fn` now, and again whenever something it read last time
    changes -- for side effects:

        Effect(lambda: logger.info("count is now {}", count.get()))

    `dispose()` stops it.
    """

    def __init__(self, fn: Callable[[], None]) -> None:
        self._fn = fn
        self._dependencies: list[Any] = []
        self._run()

    def _run(self) -> None:
        for dependency in self._dependencies:
            dependency._unsubscribe(self._run)
        _begin_recording()
        try:
            self._fn()
        finally:
            self._dependencies = _end_recording()
        for dependency in self._dependencies:
            dependency._subscribe(self._run)

    def dispose(self) -> None:
        for dependency in self._dependencies:
            dependency._unsubscribe(self._run)
        self._dependencies = []


class ViewModel:
    """The object a view's bindings and handlers resolve against.
    Constructing one attaches it to `view`: every declared handler is
    wired and every binding evaluated and subscribed. Create the signals
    the view names before calling `super().__init__(view)`:

        class CounterViewModel(ViewModel):
            def __init__(self, view):
                self.clicks = Signal(0)
                super().__init__(view)

            def bump(self):
                self.clicks.update(lambda n: n + 1)

    `view` is a `tesserae.View` or `Component`.
    """

    def __init__(self, view: Any) -> None:
        self._view = view
        view._attach(self)
