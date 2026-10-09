# Video

*Content*

## In Material Design 3

Video is content, not a component, in Material Design 3; Tesserae shows frames you supply.

## In Tesserae

An `Image` takes a `frame`, `(rgba bytes, width, height)`, from a binding and shows each new one; it keeps the last when the binding gives nothing. There is no decoder: the app decodes and pushes.

`widget: VideoPlayer` is a view Tesserae ships (`VideoPlayer_View.yaml`) that puts transport controls under such a picture: a play/pause button, the time, a seek slider, the length and a mute button.

| Property | Type | Meaning |
| --- | --- | --- |
| `frame` | `(rgba, width, height)` | the picture, pushed by the app as the video plays |
| `width`, `height`, `fit` | | the picture's size (the controls are as wide) and how it fills its box |
| `playing` | true or false; two-way | the play button flips it; the app's player follows |
| `position` | seconds; two-way | the seek slider shows and writes it; the app moves it on as it plays |
| `duration` | seconds | the length (the slider is off without one) |
| `muted` | true or false; two-way | the volume button flips it |
| `buffering` | true or false | a wait ring over the picture |
| `caption` | text | a subtitle on a darkened band at the foot of the picture |
| `step`, `label` | | how far the arrow keys move the slider; the player's accessible name |

On the seek slider: Space plays or pauses, the arrows step the position, M mutes. Not built: a decoder (decode with the library you choose, and set `frame`), full-screen, speeds, a volume level, a poster.

`widget: VideoPlayer` is the view-language form (see [The View Language](../guide/view-language.md)); the fragment below is the older `component:` form, which keeps working.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: Video` | A frame of video, fitted to its box. Frames come from a binding. | [`Video_Stylesheet.yaml`](../stylesheets/video/video.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `Video`

A frame of video, fitted to its box. Frames come from a binding. Its look: [`Video_Stylesheet.yaml`](../stylesheets/video/video.md).

| Parameter | | Default |
| --- | --- | --- |
| `width` | required |  |
| `height` | required |  |
| `fit` | optional | `fill` |
| `frame` | optional | `None` |

```yaml
params:
  - width
  - height
  - {fit: fill}
  - {frame: null}
id: root
kind: Image
image:
  fit: "{{ fit }}"
bindings:
  if: "{{ frame }}"
  then:
    frame: "{{ frame }}"
a11y: {hidden: true}
```

## Using it

```yaml
name: movie
widget: Container
style: {width: 520, height: 320, padding: 16}
children:
  - widget: VideoPlayer
    frame: "{{ frame }}"
    playing: "{{ playing }}"
    position: "{{ position }}"
    duration: 125
    muted: "{{ muted }}"
    caption: "{{ words }}"
```

## Using the fragment

In a view:

```yaml
# Home_View.yaml
id: root
kind: Container
children:
  - id: clip
    component: Video
    with: {width: 320, height: 180, fit: contain}
```

In Python:

```python
from tesserae.widgets import video

clip = video(app.window, 320, 180, fit="contain")
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# Video_Stylesheet.yaml, next to your views
styles:
  - id: root
    style: {width: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
