"""`Repeater` -- automatic, keyed add/remove diffing on top of TRE M43's
real `Component`/`instantiate`, driven by one list `Signal` as the
single source of truth. The declarative-*feeling* half of "the essence
of MVVM and single page applications": an app writes `items.update(...)`
once and `Repeater` keeps exactly one `Component`+`ViewModel` alive per
item currently present, instead of the app hand-rolling add/remove
bookkeeping the way `examples/todo_list/` originally did.

**Real, deliberate scope boundary, not silently glossed over:**
reordering an already-present key is not supported -- its `Component`
keeps whatever position it was originally instantiated at in the shared
`Tree`. `engine_core::Tree` has no child-reorder primitive at all today
(confirmed by reading its own source before designing this), and
`engine_spec::Reconciler`'s own reconciliation already carries the
identical real, stated limitation for the same underlying reason. A
key that moves position in the list without being removed and re-added
is visually unaffected -- a real, honest v1 answer, not a silent bug.

Also real and deliberate: `Repeater` never re-applies a changed item's
own *data* to an existing instance. An item's own mutable fields are
that item's own `ViewModel`'s job (its own `Signal`s, written to from
its own handlers) -- `Repeater` only ever asks "which keys are
currently present," the identical real split `examples/todo_list/`'s
own `TodoItemViewModel` already establishes for a single item.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterator

from tesserae.component import instantiate
from tesserae.naming import check_naming_convention


class Repeater:
    def __init__(
        self,
        parent: Any,
        items_signal: Any,
        path: str | Path,
        viewmodel_cls: type,
        into: Any,
        key: Callable[[Any], Any] = lambda item: item,
        args: Callable[[Any], tuple[Any, ...]] = lambda item: (item,),
    ) -> None:
        check_naming_convention(path, viewmodel_cls)
        self._parent = parent
        self._items_signal = items_signal
        self._path = path
        self._viewmodel_cls = viewmodel_cls
        self._into = into
        self._key = key
        self._args = args
        self._by_key: dict[Any, tuple[Any, Any]] = {}
        self._order: list[Any] = []
        items_signal._subscribe(self._sync)
        self._sync()

    def _sync(self) -> None:
        items = self._items_signal.get()
        new_order = [self._key(item) for item in items]
        new_keys = set(new_order)

        for stale_key in [k for k in self._order if k not in new_keys]:
            component, _viewmodel = self._by_key.pop(stale_key)
            component.remove()

        for item, item_key in zip(items, new_order):
            if item_key not in self._by_key:
                self._by_key[item_key] = instantiate(
                    self._parent,
                    self._path,
                    self._viewmodel_cls,
                    self._into,
                    *self._args(item),
                )

        self._order = new_order

    def __getitem__(self, key: Any) -> tuple[Any, Any]:
        return self._by_key[key]

    def __iter__(self) -> Iterator[tuple[Any, Any, Any]]:
        for item_key in self._order:
            component, viewmodel = self._by_key[item_key]
            yield item_key, component, viewmodel

    def __len__(self) -> int:
        return len(self._order)

    def remove(self) -> None:
        """Real, structural teardown -- removes every currently-tracked
        instance and unsubscribes from `items_signal`, mirroring
        `Component.remove()`'s own "unsubscribe before tearing down"
        ordering (TRE M43 Phase 2).
        """
        self._items_signal._unsubscribe(self._sync)
        for component, _viewmodel in self._by_key.values():
            component.remove()
        self._by_key.clear()
        self._order = []
