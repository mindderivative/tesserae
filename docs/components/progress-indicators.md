# Progress indicators

*Communication*

## In Material Design 3

Progress indicators show that something is happening. **Determinate** ones fill as a value from 0 to 1
grows; **indeterminate** ones keep moving when there's no value to show. The loading indicator is MD3's
shape-morphing one, for short waits.

## In Tesserae

Each is a Tesserae control (`tesserae.controls`), not a drawing of `tre`'s: `widget: LinearProgress`, `widget: CircularProgress` and
`widget: LoadingIndicator`. Leave `value` out, or let an expression give nothing, for a wait with no end; a number from 0 to 1 is determinate and
eases to each new value.

A bar is 240 pixels long and 4 thick, and a ring is 48 across, unless the call's `style:` gives a `width`; the colour is `style.foreground`, `primary` by default. A bar
has a `surface_container_highest` track behind it and a ring has none, until `track` names a colour role; a stop dot at the end of the bar's track is opt-in
(`stop_indicator`), as is a `buffer` (how much has loaded, 0 to 1, a lighter bar behind the value). With a `track`, a determinate ring and its track are a gap apart
(4 pixels between the rounded ends), as in MD3. A `wavy` bar is taller than its `thickness` by the wave's height (6 pixels), and a wavy ring's arc is a wave round
a plain track. A screen reader hears a progress bar with its value as a percentage, or as busy when there is none. An app that reduces motion gets a still bar and arc
instead of the endless motion. The two bars of `two_bar` keep their widths as they cross, so the sweep approximates MD3's, whose bars grow and shrink; the wave's size
and speed and the thicker sizes are written from memory of the spec and have not been checked against it.

## How it is built

### `LinearProgress`

A progress bar.

| Property | Type | Default | Meaning |
| --- | --- | --- | --- |
| `value` | `float` |  | 0 to 1; leave out, or give nothing, for a wait with no end. |
| `track` | `str` |  | The colour role of the track behind the indicator. |
| `thickness` | `float` |  | The bar's height in pixels (4 is the standard one; MD3 Expressive's are thicker). |
| `buffer` | `float` |  | 0 to 1: how much has loaded, drawn as a lighter bar behind the value. |
| `stop_indicator` | `bool` |  | A dot at the end of the track (Material 3). |
| `wavy` | `bool` |  | The bar is a sine wave that flows along a straight track (MD3 Expressive); the control is taller by the wave's height. |
| `two_bar` | `bool` |  | A wait with no end sweeps as two bars, a long one and a short one a little behind (MD3), not one. |
| `label` | `str` |  | What a screen reader calls it. |

Its `style:` also takes `foreground`.

### `CircularProgress`

A progress ring.

| Property | Type | Default | Meaning |
| --- | --- | --- | --- |
| `value` | `float` |  | 0 to 1; leave out, or give nothing, for a wait with no end. |
| `track` | `str` |  | The colour role of the track behind the indicator. |
| `wavy` | `bool` |  | The arc is a wave whose crests flow round the ring (MD3 Expressive). |
| `thickness` | `float` |  | The ring's width in pixels (4 is the standard one; MD3 Expressive's are thicker). With a `track` the arc and the track are a gap apart. |
| `label` | `str` |  | What a screen reader calls it. |

Its `style:` also takes `foreground`.

### `LoadingIndicator`

An indeterminate wait indicator.

| Property | Type | Default | Meaning |
| --- | --- | --- | --- |
| `contained` | `bool` |  | The shape in a `primary_container` circle, in `on_primary_container` (MD3 Expressive). |
| `label` | `str` |  | What a screen reader calls it. |

Its `style:` also takes `foreground`.

## Using it

```yaml
name: upload
widget: Container
style: {flex_direction: vertical, gap: 16, width: 280, height: 140, padding: 16}
children:
  - {widget: LinearProgress, value: "{{ sent }}", buffer: "{{ queued }}", label: Uploading, style: {width: 240}}
  - {widget: LinearProgress, style: {width: 240}}                  # no value: a wait with no end
  - {widget: CircularProgress, value: "{{ sent }}", track: secondary_container}
  - {widget: LinearProgress, value: "{{ sent }}", wavy: true, thickness: 4, style: {width: 240}}
```

## Using it in Python

```python
from tesserae.widgets import linear_progress

upload = linear_progress(app.window, 240, value=0.4)
upload.value.set(0.8)
```

## See also

- [Controls](../guide/controls.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
