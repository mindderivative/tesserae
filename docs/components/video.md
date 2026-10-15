# Video

*Content*

## In Material Design 3

Video is content, not a component, in Material Design 3; Tesserae shows frames you supply.

## In Tesserae

An `Image` takes a `frame`, `(rgba bytes, width, height)`, from a binding and shows each new one; it keeps the last when the binding gives nothing. There is no decoder: the app decodes and pushes.

`widget: VideoPlayer` is a view Tesserae ships (`VideoPlayer_View.yaml`) that puts transport controls under such a picture: a play/pause button, the time, a seek slider, the length and a mute button.

The app pushes each `frame` as the video plays; `width` and `height` are the picture's size (the controls are as wide) and `fit` how it fills its box (`contain` here). The three
two-way values are `playing` (the play button flips it; the app's player follows), `position` (seconds; the seek slider shows and writes it, and the app moves it on as it plays)
and `muted` (the volume button flips it). `duration` is the length in seconds, and the slider is off without one. `buffering` lays a wait ring over the picture, `caption` puts a
subtitle on a darkened band at its foot, `step` is how far the arrow keys move the slider, and `label` is the player's name for a screen reader.

On the seek slider: Space plays or pauses, the arrows step the position, M mutes. Not built: a decoder (decode with the library you choose, and set `frame`), full-screen, speeds, a volume level, a poster.

## How it is built

A view Tesserae ships is a `<Name>_View.yaml` (what it takes and what it is made of) with a `<Name>_Stylesheet.yaml` (how it looks). Use it by name: `widget: VideoPlayer`. A file of the same name in your project replaces it.

### `VideoPlayer`

A video player: a picture surface with the usual transport controls under it. Tesserae has no decoder, so the app supplies the frames: a `frame` (rgba bytes, width, height) that a ViewModel updates as it plays, like an `Image`'s `frame`. The player owns none of the playing: `playing` (two-way) is what the play button flips, `position` (two-way, seconds) is where the seek slider is and what it writes when dragged, and the app's player follows both and moves `position` on as the video plays. `duration` is the length in seconds. `muted` (two-way) is the volume button. `buffering` lays a wait ring over the picture; `caption` is a line of subtitle on a darkened band at its foot. Keys, on the seek slider: Space plays or pauses, the arrows step `position` by `step` seconds, M mutes (the buttons are Tab stops with their own keys). The role is a group named by `label`. Not here: a decoder, full-screen, speeds, a volume level.

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `frame` | `any` |  | The current picture: (rgba bytes, width, height), pushed by the app as the video plays. |
| `width` | `float` | `480` | The picture's width. |
| `height` | `float` | `270` | The picture's height. |
| `fit` | `cover` or `contain` or `fill` | `contain` | How the picture fills its box. |
| `playing` | `bool` | `false` | Whether it is playing; the play button flips it. Two-way: give it a bare reference and the view writes it back. |
| `position` | `float` | `0` | Seconds in; the seek slider shows and writes it. Two-way: give it a bare reference and the view writes it back. |
| `duration` | `float` | `0` | The length in seconds. |
| `muted` | `bool` | `false` | Whether the sound is off; the volume button flips it. Two-way: give it a bare reference and the view writes it back. |
| `buffering` | `bool` | `false` | A wait ring over the picture. |
| `caption` | `str` |  | A subtitle line shown at the foot of the picture. |
| `step` | `float` | `1` | Seconds the arrow keys move the seek slider (and a drag lands on a multiple of it). |
| `label` | `str` | `Video` | What a screen reader calls the player. |

Its parts, by name (a stylesheet rule's `part:` or `name:` addresses one): `stage` (Container), `picture` (Image), `wait` (CircularProgress), `caption` (Container), `caption_text` (Text), `controls` (Container), `play` (IconButton), `elapsed` (Text), `seek` (Slider), `total` (Text), `volume` (IconButton).

Its look is in [`VideoPlayer_Stylesheet.yaml`](../stylesheets/video/video-player.md).

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

## Using it in Python

```python
from tesserae.widgets import video

clip = video(app.window, 320, 180, fit="contain")
```

## Changing its look

To restyle it in your whole app, write rules for it in your app's stylesheet, or put a stylesheet of the same name next to your views. A rule names the widget and may narrow it by the properties it declares, a part and a state; the most specific rule wins, and a node's own `style:` beats every rule:

```yaml
# VideoPlayer_Stylesheet.yaml, or any stylesheet your app loads
styles:
  - widget: VideoPlayer
    part: elapsed
    style: {foreground: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
