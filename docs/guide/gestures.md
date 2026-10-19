# Touch, Gestures & Files

Every node can hear touch, gestures and files dropped on it, as handlers on its `handlers:` mapping. A handler is the name of a
ViewModel method (called with nothing), or statements, in which `event` is the event: `on_pan: "panned(event)"` hands it to a method,
and `on_pan: "x = x + event.delta_x"` uses it in place. A disabled node's own handlers do not run. See
[Handlers](view-language.md#handlers) for what a handler can say.

```yaml
widget: Container
name: canvas
state: {x: 0, y: 0, zoom: 1}
style: {width: 320, height: 240, background: surface_container}
handlers:
  on_tap: "tapped(event)"
  on_pan: "x = x + event.delta_x; y = y + event.delta_y"
  on_pinch: "zoom = event.scale"
  on_file_drop: "opened(event)"
```

| Handler | Event | The event's fields |
| --- | --- | --- |
| `on_tap` | a quick touch and lift | `count` (2 for a double tap) |
| `on_long_press` | a finger held in place | |
| `on_pan` | a finger dragged | `phase` (`began`, `changed`, `ended`, `cancelled`), `delta_x`, `delta_y`, `total_x`, `total_y`; on `ended` also `velocity_x`, `velocity_y` |
| `on_pinch` | two fingers, or a trackpad pinch | `phase`, `scale` (the whole pinch so far), `scale_delta` (the step to apply) |
| `on_touch_start`, `on_touch_move`, `on_touch_end`, `on_touch_cancel` | each finger | `pointer_id` |
| `on_file_hover`, `on_file_hover_cancel`, `on_file_drop` | files dragged over, away from, or dropped on it | `paths`, and `path` for the first (not on `on_file_hover_cancel`) |
| `on_link` | a link range inside a text was activated (a [`Link`](rich-text.md#links) uses `on_click`) | `href` |

Every event except `on_file_hover_cancel` and `on_link` also has `x` and `y` (from the top left of the node that handles it) and `window_x` and `window_y`.

The first finger is also the pointer: a tap is a click, so an app written for the mouse works under a finger. When
that finger starts to pan, the press is cancelled and the pan scrolls the scroll view under it, unless a node on the
way has an `on_pan`, which takes the pan instead. Gestures bubble to ancestors, like clicks.

## Files

`on_file_hover` is the moment to show a drop target and `on_file_hover_cancel` to hide it; `on_file_drop` receives the
paths, all of a drop in one event. Reading the files is the app's.

```python
class MainViewModel(ViewModel):
    def opened(self, event):
        for path in event.paths:
            self.documents.set([*self.documents.get(), Path(path).read_text()])
```

with `on_file_drop: "opened(event)"` in the view.

For a drop anywhere on the window, `app.on_file_drop(handler)`. The OS gives no position to a file drag while it is
over the window, so the node that hears it is the one under the pointer's last known place. A file drop doesn't work
on Wayland.

## The mouse

For a drag with the mouse, use `on_press`, `on_move` and `on_release` with `capture()`, so the
node keeps hearing the pointer outside itself: [Dragging](view-language.md#dragging).

## Testing

`window.simulate` delivers all of these without a display: `touch_start`, `touch_move`, `touch_end`,
`trackpad_pinch`, `file_hover`, `file_hover_cancel`, `file_drop` and `link`. A tap or a pan is a sequence of touches.

```python
window.simulate("touch_start", node, x=20, y=20)
window.simulate("touch_move", node, x=60, y=30)     # the pan begins
window.simulate("touch_end", node, x=60, y=30)
```
