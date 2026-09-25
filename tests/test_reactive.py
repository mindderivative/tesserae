"""M35: Tesserae's reactivity (`tesserae.reactive`) behaves exactly like
`tre`'s, which it replaces (`tre` D5).

Every behavioral test runs against both implementations while `tre`
0.3.4 still has its own, so a difference shows up as one side failing.
(M35's bridge, which fed `tre`'s own `View` bindings from Tesserae's
signals, was removed in M37 Phase 6; bindings on Tesserae views are
covered by `test_view.py`.)
"""

import pytest
import tre

import tesserae
import tesserae.reactive

IMPLS = {"tre": tre, "tesserae": tesserae.reactive}


@pytest.fixture(params=sorted(IMPLS))
def rx(request):
    return IMPLS[request.param]


def _counter():
    calls = []
    return calls, (lambda: calls.append(1))


# -- Signal ---------------------------------------------------------------


def test_signal_get_set_update(rx):
    s = rx.Signal(1)
    s.set(2)
    s.update(lambda n: n * 10)
    assert s.get() == 20


def test_a_signal_notifies_only_on_a_change(rx):
    s = rx.Signal(1)
    calls, cb = _counter()
    s._subscribe(cb)
    s.set(1)
    s.update(lambda n: n)
    assert calls == []
    s.set(2)
    assert calls == [1]
    s._unsubscribe(cb)
    s._unsubscribe(cb)  # a second unsubscribe is a no-op
    s.set(3)
    assert calls == [1]


# -- Computed -------------------------------------------------------------


def test_computed_follows_its_dependencies(rx):
    price, qty = rx.Signal(2), rx.Signal(3)
    total = rx.Computed(lambda: price.get() * qty.get())
    assert total.get() == 6
    qty.set(4)
    assert total.get() == 8


def test_computed_is_eager_and_runs_once_per_change(rx):
    runs = []
    s = rx.Signal(1)
    c = rx.Computed(lambda: runs.append(s.get()) or s.get())
    assert runs == [1]
    s.set(2)
    assert runs == [1, 2]  # recomputed at the write, before any get()
    assert c.get() == 2


def test_computed_notifies_only_when_its_value_changes(rx):
    s = rx.Signal(1)
    parity = rx.Computed(lambda: s.get() % 2)
    calls, cb = _counter()
    parity._subscribe(cb)
    s.set(3)  # still odd
    assert calls == []
    s.set(4)
    assert calls == [1]


def test_computed_tracks_dependencies_dynamically(rx):
    use_a, a, b = rx.Signal(True), rx.Signal("a"), rx.Signal("b")
    runs = []
    c = rx.Computed(lambda: runs.append(1) or (a.get() if use_a.get() else b.get()))
    use_a.set(False)
    assert c.get() == "b"
    before = len(runs)
    a.set("a2")  # no longer a dependency
    assert len(runs) == before
    b.set("b2")
    assert c.get() == "b2"


def test_a_chain_of_computeds_updates_in_order(rx):
    s = rx.Signal(1)
    double = rx.Computed(lambda: s.get() * 2)
    plus_one = rx.Computed(lambda: double.get() + 1)
    seen = []
    rx.Effect(lambda: seen.append(plus_one.get()))
    s.set(5)
    assert (double.get(), plus_one.get()) == (10, 11)
    assert seen == [3, 11]


# -- Effect ---------------------------------------------------------------


def test_effect_runs_now_and_on_each_change_until_disposed(rx):
    s = rx.Signal(1)
    seen = []
    e = rx.Effect(lambda: seen.append(s.get()))
    s.set(2)
    e.dispose()
    s.set(3)
    assert seen == [1, 2]


# -- batch ----------------------------------------------------------------


def test_batch_runs_each_subscriber_once(rx):
    x, y = rx.Signal(1), rx.Signal(1)
    runs = []
    total = rx.Computed(lambda: runs.append(1) or x.get() + y.get())
    runs.clear()
    seen = []
    rx.Effect(lambda: seen.append(total.get()))
    seen.clear()
    result = rx.batch(lambda: (x.set(10), y.set(20), "done")[-1])
    assert result == "done"
    assert runs == [1]  # one recompute for two writes
    assert seen == [30]


def test_nested_batches_flush_at_the_outermost(rx):
    s = rx.Signal(0)
    seen = []
    rx.Effect(lambda: seen.append(s.get()))

    def inner():
        s.set(1)
        assert seen == [0]

    def outer():
        rx.batch(inner)
        assert seen == [0]  # still deferred
        s.set(2)

    rx.batch(outer)
    assert seen == [0, 2]


def test_batch_flushes_and_reraises_when_fn_raises(rx):
    s = rx.Signal(0)
    seen = []
    rx.Effect(lambda: seen.append(s.get()))

    def fn():
        s.set(1)
        raise KeyError("boom")

    with pytest.raises(KeyError):
        rx.batch(fn)
    assert seen == [0, 1]


# -- untrack --------------------------------------------------------------


def test_untrack_hides_reads_from_the_enclosing_scope(rx):
    tracked, hidden = rx.Signal(1), rx.Signal(10)
    c = rx.Computed(lambda: tracked.get() + rx.untrack(lambda: hidden.get()))
    hidden.set(20)
    assert c.get() == 11  # didn't recompute
    tracked.set(2)
    assert c.get() == 22  # recomputed, reading hidden's new value


# -- re-entrancy ------------------------------------------------------------


def test_writing_a_signal_while_it_notifies_raises(rx):
    s = rx.Signal(0)
    s._subscribe(lambda: s.set(s._value + 1))
    with pytest.raises(RuntimeError, match="written to again while still notifying"):
        s.set(1)


# -- only Tesserae: the public names and the bridge to tre's bindings -------


def test_tesserae_exports_its_own_reactivity():
    for name in ("Signal", "Computed", "Effect", "ViewModel", "batch", "untrack"):
        assert getattr(tesserae, name) is getattr(tesserae.reactive, name)
        assert getattr(tesserae, name) is not getattr(tre, name)
