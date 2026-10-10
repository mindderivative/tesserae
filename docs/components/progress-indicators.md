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

| Property | Widget | Meaning |
| --- | --- | --- |
| `value` | linear, circular | 0 to 1, or nothing for a wait with no end; an expression follows its Signals |
| `track` | linear, circular | the colour role of the track behind the indicator (a bar has `surface_container_highest`, a ring none) |
| `buffer` | linear | 0 to 1: how much has loaded, a lighter bar behind the value |
| `stop_indicator` | linear | a dot at the end of the track |
| `thickness` | linear, circular | the bar's height or the ring's width in pixels (4 is the standard one; MD3 Expressive's are thicker) |
| `wavy` | linear, circular | the bar (or the ring's arc) is a sine wave whose crests flow along (or round) a plain track; the bar is taller by the wave's height |
| `two_bar` | linear | a wait with no end sweeps as two bars, a long one and a short one a little behind, as MD3 draws it, not one |
| `contained` | loading indicator | the shape sits in a `primary_container` circle, in `on_primary_container` |
| `label` | all | what a screen reader calls it |

The colour is `style.foreground`; the bar's length is `style.width` and a ring's size is `style.width` too. A screen reader hears a progress bar
with its value as a percentage, or as busy when there is none. An app that reduces motion gets a still bar and arc instead of the endless motion.
With a `track`, a determinate ring and its track are a gap apart (4 px between the rounded ends), as in MD3. The widths of the two bars are fixed (the engine
cannot animate a width), so the two-bar sweep approximates MD3's, whose bars grow and shrink; the wave's size and speed and the thicker sizes are written
from memory of the spec and have not been checked against it. The default look is still the one `tre`'s recorded trees draw: a track and a stop dot are opt-in.

`widget: LinearProgress` is the view-language form (see [The View Language](../guide/view-language.md)); the fragment below is the older `component:` form, which keeps working.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: LinearProgress` | A linear progress indicator: determinate with a value, indeterminate without. | [`LinearProgress_Stylesheet.yaml`](../stylesheets/progress-indicators/linear-progress.md) |
| `component: CircularProgress` | A circular progress indicator: determinate with a value, indeterminate without. | [`CircularProgress_Stylesheet.yaml`](../stylesheets/progress-indicators/circular-progress.md) |
| `component: LoadingIndicator` | A loading indicator: a shape that morphs while something loads. | [`LoadingIndicator_Stylesheet.yaml`](../stylesheets/progress-indicators/loading-indicator.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `LinearProgress`

A linear progress indicator: determinate with a value, indeterminate without. Its look: [`LinearProgress_Stylesheet.yaml`](../stylesheets/progress-indicators/linear-progress.md).

| Parameter | | Default |
| --- | --- | --- |
| `width` | required |  |
| `height` | required |  |
| `value` | required |  |

```yaml
params: [width, height, value]
id: root
kind: LinearProgress
value: "{{ value }}"
```

### `CircularProgress`

A circular progress indicator: determinate with a value, indeterminate without. Its look: [`CircularProgress_Stylesheet.yaml`](../stylesheets/progress-indicators/circular-progress.md).

| Parameter | | Default |
| --- | --- | --- |
| `size` | required |  |
| `value` | required |  |

```yaml
params: [size, value]
id: root
kind: CircularProgress
value: "{{ value }}"
```

### `LoadingIndicator`

A loading indicator: a shape that morphs while something loads. Its look: [`LoadingIndicator_Stylesheet.yaml`](../stylesheets/progress-indicators/loading-indicator.md).

| Parameter | | Default |
| --- | --- | --- |
| `size` | required |  |
| `background` | required |  |

```yaml
params: [size, background]
id: root
kind: LoadingIndicator
```

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

## Using the fragment

In a view:

```yaml
# Home_View.yaml
id: root
kind: Container
children:
  - id: upload
    component: LinearProgress
    with: {width: 240, height: 4, value: 0.4}
```

In Python:

```python
from tesserae.widgets import linear_progress

upload = linear_progress(app.window, 240, value=0.4)
upload.value.set(0.8)
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# LinearProgress_Stylesheet.yaml, next to your views
styles:
  - id: root
    style: {width: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Controls](../guide/controls.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
