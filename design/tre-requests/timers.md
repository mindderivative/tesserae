# Request to tre: timers

*Drafted for Tesserae 0.5.0 (#235). Not sent: sending it to tre is the project owner's decision.*

## What Tesserae needs

`after(ms, fn)` and `every(ms, fn)`, cancellable: snackbar auto-dismiss, a tooltip's delay, hold-to-repeat on a spin box, an autoplaying carousel, a video's frame clock.

## What exists today (tre 0.5.4)

No timer API on `Window` or `App` (checked: no member of `Window` mentions `after`, `every`, `timer` or `schedule`). `App.thread_handle().call_soon(fn)` runs a callback on the loop from another thread, which is not a delay. Tesserae's `tesserae.timers.Timers` uses an animation of a private, detached `box` that runs with the frames and fires `on_complete` (#217).

## The ask

`window.after(ms, fn) -> handle`, `window.every(ms, fn) -> handle`, `handle.cancel()`, running on the loop thread and driven by the frame clock (so a window that is not drawing, or `advance(ms)` in tests, moves them). A timer should fire on the first frame at or after its time.

## What the workaround costs

It works. It is quantized to frames, `every` drifts up to a frame per round, and it creates a node per timer. A real timer would remove the node and the drift, and let a window sleep between frames when the only thing pending is a timer (an idle app should not redraw at 60 Hz to count down a snackbar).

## Questions for tre

- Will tre wake the loop for a pending timer when nothing else is animating?
