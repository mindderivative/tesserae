# Gradients & Effects

A node's `style:` can paint a gradient, blur itself or what is behind it, blend with what is under it, filter its
colours, stick to the top of a scroll view and choose its pointer. All of them work in a stylesheet too. Every key is
listed in the [YAML reference](../api/yaml.md).

## Gradients

`background`, `foreground` and `border_color` take a gradient where they take a colour. Write one as a CSS-like
string:

```yaml
id: root
kind: Container
style: {flex_direction: vertical, gap: 12, padding: 16, width: 360, background: surface}
children:
  - id: banner
    kind: Rect
    style: {height: 64, corner_radius: 16, background: "linear-gradient(90deg, primary, tertiary)"}
  - id: glow
    kind: Rect
    style: {height: 64, corner_radius: 16, background: "radial-gradient(at 30% 30%, primary_container, surface)"}
  - id: title
    kind: Text
    text: {content: "Gradient text", typography_role: headline_medium}
    style: {foreground: "linear-gradient(to right, primary, error)"}
```

- `linear-gradient([angle | to side,] stop, stop, ...)`: the angle is in `deg` (0 up, 90 right, 180 down, the
  default), or `to right`, `to bottom left` and the like.
- `radial-gradient([at x y,] stop, ...)`: outward from a point, the middle unless `at 30% 30%` says otherwise.
- `conic-gradient([from angle] [at x y,] stop, ...)`: around a point.
- A stop is a [theme role](../themes/index.md) or a CSS colour, with an optional place: `primary 40%`. Stops with no
  place are spread evenly between the ones that have one.

The mapping form says the same with keys, and is what to write when a string is awkward:

```yaml
style:
  background: {gradient: linear, angle: 45, stops: [primary, [0.6, secondary], tertiary]}
  border_width: 3
  border_color: {gradient: sweep, stops: [primary, secondary, primary]}
```

`gradient` is `linear`, `radial` or `sweep` (conic); `angle`, `center` (`[x, y]` as fractions of the box), `radius`
and `start` go with the kind. A gradient follows its box as the layout resizes it. A control's own colour (a
`Switch`, a `Slider`) takes a plain colour only.

## Blur, and a frosted surface

`blur` blurs the node and what it draws, by that many pixels. `backdrop_blur` blurs what is *behind* it, so a node
with a translucent `background` and a `backdrop_blur` is a frosted pane:

```yaml
- id: pane
  kind: Container
  style: {width: 240, height: 120, background: "#FFFFFF55", backdrop_blur: 16, corner_radius: 20}
```

Both can animate. A pane only has something to blur when other nodes are drawn behind it.

## Blend modes and colour filters

`blend_mode` draws a node over what is behind it the way CSS's `mix-blend-mode` does: `normal` (the default),
`multiply`, `screen`, `overlay`, `darken`, `lighten`, `color_dodge`, `color_burn`, `hard_light`, `soft_light`,
`difference`, `exclusion`, `hue`, `saturation`, `color` and `luminosity`.

`filter` changes the colours of a node and everything in it, as CSS filters do; the filters apply in the order
written:

| Key | Unchanged at | Range |
| --- | --- | --- |
| `saturate`, `brightness`, `contrast` | 1 | 0 and up |
| `grayscale`, `invert`, `sepia` | 0 | 0 to 1 |
| `hue_rotate` | 0 | degrees |

A disabled-looking card is `filter: {grayscale: 1, brightness: 1.2}`.

```yaml
- id: card
  kind: Container
  style: {width: 200, height: 80, background: primary_container, filter: {saturate: 0.2}}
```

## Sticky headers

In a [`ScrollView`](layout.md#scrolling), `sticky: N` makes a node hold the top edge of the scroll view, `N` pixels
down, as CSS's `position: sticky` does: it scrolls with its content until it reaches that edge, then stays there
while the container it is in scrolls past, and the end of that container pushes it out. Put a header in each section:

```yaml
- id: list
  kind: ScrollView
  style: {height: 240, flex_direction: vertical}
  children:
    - id: fruit
      kind: Container
      style: {flex_direction: vertical}
      children:
        - id: fruit_header
          kind: Rect
          style: {height: 40, background: surface_container_high, sticky: 0, z_index: 1}
        - id: apple
          kind: Rect
          style: {height: 56, background: surface}
```

The node is only moved when it is drawn: layout, hit testing and its siblings don't change. Content later in the
section paints over a stuck header unless the header has a `z_index`.

## The pointer

`cursor` is the name of a pointer shape (`pointer`, `text`, `grab`, `grabbing`, `move`, `not_allowed`, `wait`,
`progress`, `crosshair`, `help`, `copy`, the resize pointers and the rest, listed in the
[YAML reference](../api/yaml.md)), or a picture next to the view:

```yaml
style: {cursor: {src: pointers/pen.png, hotspot: [2, 30]}}
```

The picture is read with the view, like an `Image`'s: relative to the view's folder, inside it, 1 to 256 pixels a
side, and `hotspot` is the pixel that is the pointer's place. It is in device pixels, so give a larger one for a
high-density screen. A picture is only given in a node's own `style:`, not in a stylesheet. A `Link` keeps
`pointer` unless it says another.
