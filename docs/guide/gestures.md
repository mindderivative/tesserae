# Touch, Gestures & Files

Every node can hear touch, gestures and files dropped on it, as handlers on its `handlers:` mapping. Each names a
ViewModel method, which takes the event (or nothing). A disabled node hears none.

```yaml
id: canvas
kind: Container
style: {width: 320, height: 240, background: surface_container}
handlers:
  on_tap: tapped
  on_pan: panned
  on_pinch: pinched
  on_file_drop: opened
```

| Handler | Event | The event's fields |
| --- | --- | --- |
| `on_tap` | a quick touch and lift | `count` (2 for a double tap) |
| `on_long_press` | a finger held in place | |
| `on_pan` | a finger dragged | `phase` (`began`, `changed`, `ended`, `cancelled`), `delta_x`, `delta_y`, `total_x`, `total_y`; on `ended` also `velocity_x`, `velocity_y` |
| `on_pinch` | two fingers, or a trackpad pinch | `phase`, `scale`, `scale_delta` (the step to apply) |
| `on_touch_start`, `on_touch_move`, `on_touch_end`, `on_touch_cancel` | each finger | `pointer_id` |
| `on_file_hover`, `on_file_hover_cancel`, `on_file_drop` | files dragged over, away from, or dropped on it | `paths`, and `path` for the first |
| `on_link` | a link in [rich text](rich-text.md) was clicked | `href` |

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
            self.documents.append(Path(path).read_text())
```

For a drop anywhere on the window, `app.on_file_drop(handler)`. The OS gives no position to a file drag while it is
over the window, so the node that hears it is the one under the pointer's last known place. A file drop doesn't work
on Wayland.

## Testing

`window.simulate` delivers all of these without a display: `touch_start`, `touch_move`, `touch_end`,
`trackpad_pinch`, `file_hover`, `file_drop` and `link`. A tap or a pan is a sequence of touches.
