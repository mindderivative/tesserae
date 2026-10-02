# Progress indicators

*Communication*

## In Material Design 3

Progress indicators show that something is happening. **Determinate** ones fill as a value from 0 to 1
grows; **indeterminate** ones keep moving when there's no value to show. The loading indicator is MD3's
shape-morphing one, for short waits.

## In Tesserae

Each is a Tesserae control (`tesserae.controls`), not a drawing of `tre`'s: the node kinds `LinearProgress`,
`CircularProgress` and `LoadingIndicator`. Leave `value` out for the indeterminate form.

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
