"""M33: a background thread's garbage collector can free a `tre` object
made on the main thread (`tre` issue #10, fixed in 0.3.4's M96).

Tesserae's watcher threads (`ViewWatcher.start`, `FileWatcher`) parse
YAML, and any allocation there can run Python's cyclic GC on that
thread. If the last reference to a `View` sits in a reference cycle, the
GC frees the `View` there. On `tre` 0.3.3 that raised a `PanicException`
and a `RuntimeError` ("View is unsendable, but is being dropped on
another thread") and leaked the `View`; CI saw it as unraisable-exception
warnings in `test_watch_thread.py`. 0.3.4 makes objects `ThreadBound`,
so the drop is safe.
"""

import gc
import sys
import threading

import tre


def _make_cyclic_garbage() -> None:
    view = tre.View(spec={"id": "root", "kind": "Rect", "style": {"width": 10, "height": 10, "background": "#112233"}})

    class Holder:
        pass

    holder = Holder()
    holder.view = view  # the only reference to the View...
    holder.me = holder  # ...kept alive by a plain cycle, so only the cyclic GC frees it


def test_a_background_thread_gc_can_free_a_main_thread_view(monkeypatch):
    unraisable = []
    monkeypatch.setattr(sys, "unraisablehook", unraisable.append)
    was_enabled = gc.isenabled()
    gc.disable()  # so this thread doesn't collect the cycle first
    try:
        _make_cyclic_garbage()
        collector = threading.Thread(target=gc.collect)
        collector.start()
        collector.join()
    finally:
        if was_enabled:
            gc.enable()

    assert [f"{type(u.exc_value).__name__}: {u.exc_value}" for u in unraisable] == []
