# Gradients & Effects

A node's `style:` can paint a gradient, blur itself or what is behind it, blend with what is under it, filter its
colours, stick to the top of a scroll view and choose its pointer. All of them work in a stylesheet too. Every key is
listed in the [YAML reference](../api/yaml.md).

## Gradients

`background`, `foreground` and `border_color` take a gradient where they take a colour. Write one as a CSS-like
string:

```yaml
widget: Container
style: {flex_direction: vertical, gap: 12, padding: 16, width: 360, background: surface}
children:
  - widget: Rect
    name: banner
    style: {height: 64, corner_radius: 16, background: "linear-gradient(90deg, primary, tertiary)"}
  - widget: Rect
    name: glow
    style: {height: 64, corner_radius: 16, background: "radial-gradient(at 30% 30%, primary_container, surface)"}
  - widget: Text
    name: title
    text: Gradient text
    typography_role: headline_medium
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
widget: Rect
style:
  width: 200
  height: 80
  background: {gradient: linear, angle: 45, stops: [primary, [0.6, secondary], tertiary]}
  border_width: 3
  border_color: {gradient: sweep, stops: [primary, secondary, primary]}
```

`gradient` is `linear`, `radial` or `sweep` (conic); `angle`, `center` (`[x, y]` as fractions of the box), `radius`
and `start` go with the kind. A gradient follows its box as the layout resizes it. A control's own colour (a
`Switch`, a `Slider`) takes a plain colour only.

## Elevation that moves

A raised surface lifts when the pointer is over it and again when it is pressed. Give the levels in rules by state, and `transition: {elevation: 200}`
eases the shadows between them. The base level belongs in a rule too: an `elevation` written on the node itself beats every rule.

```yaml
styles:
  - widget: Card
    style: {elevation: 1, transition: {elevation: 200}}
  - widget: Card
    state: hovered
    style: {elevation: 3}
  - widget: Card
    state: pressed
    style: {elevation: 5}
```

A press during a hover carries on from where the shadow is. A level a view works out itself, such as a lift while dragging, eases the same way:
`style: {elevation: "{{ 4 if dragging else 1 }}", transition: {elevation: 200}}`. An app that reduces motion gets the level at once. Levels are 0 to 5, or
`level_0` to `level_5`.

## Frosted surfaces

`frosted: true` on the navigation surfaces (`NavigationRail`, `NavigationDrawer`, `NavigationDrawerModal`, `Menu`, `SearchBar`, `SearchView` and
`TopAppBar`) makes them 72% of their colour with a 20 pixel backdrop blur. It is off by default. For any other node, write the same with
`backdrop_blur` (below).

## Corner radius

`corner_radius` is one radius for every corner (pixels, or a shape token `none` ... `extra_large`, `full`). Give four to round the corners
differently, as a list `[top_left, top_right, bottom_right, bottom_left]` or as a mapping of corners and edges, where an edge (`top`, `right`,
`bottom`, `left`) is its two corners, a corner named beats its edge and the corners left out are square:

```yaml
widget: Container
style: {width: 120, height: 48, background: primary, corner_radius: {left: full, top_right: 4}}   # a pill end on the left
```

The tokens are `none` (0), `extra_small` (4), `small` (8), `medium` (12), `large` (16), `extra_large` (28) and `full` (a pill or a circle).

It is a style field like the others, so a rule can give it, a `transition:` eases it, and the state layer and focus ring follow the shape.

## Blur, and a frosted surface

`blur` blurs the node and what it draws, by that many pixels. `backdrop_blur` blurs what is *behind* it, so a node
with a translucent `background` and a `backdrop_blur` is a frosted pane:

```yaml
widget: Container
style: {width: 240, height: 120, background: "#FFFFFF55", backdrop_blur: 16, corner_radius: 20}
```

A colour takes an alpha two ways: `"#FFFFFF55"`, or a theme role with a percentage, `"surface@72%"`.

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
widget: Container
style: {width: 200, height: 80, background: primary_container, filter: {saturate: 0.2}}
```

## Sticky headers

In a [`ScrollView`](layout.md#scrolling), `sticky: N` makes a node hold the top edge of the scroll view, `N` pixels
down, as CSS's `position: sticky` does: it scrolls with its content until it reaches that edge, then stays there
while the container it is in scrolls past, and the end of that container pushes it out. Put a header in each section:

```yaml
widget: ScrollView
style: {height: 240, flex_direction: vertical}
children:
  - widget: Container
    name: fruit
    style: {flex_direction: vertical}
    children:
      - widget: Rect
        name: fruit_header
        style: {height: 40, background: surface_container_high, sticky: 0, z_index: 1}
      - widget: Rect
        name: apple
        style: {height: 56, background: surface}
      - widget: Rect
        name: pear
        style: {height: 56, background: surface}
```

The node is only moved when it is drawn: layout, hit testing and its siblings don't change. Content later in the
section paints over a stuck header unless the header has a `z_index`.

## Transitions and transforms

`transition:` in a style says which changes ease to their new value instead of jumping. A node is where its style says when it is first drawn; the
next time the style gives a property a new value, it travels there:

```yaml
widget: Rect
state: {on: false}
handlers: {on_click: "on = not on"}
style:
  width: 200
  height: 80
  background: "{{ 'primary_container' if on else 'surface_container' }}"
  corner_radius: "{{ 24 if on else 12 }}"
  scale: "{{ 1.05 if on else 1 }}"
  opacity: "{{ 1 if on else 0.8 }}"
  transition:
    background: 150                                   # milliseconds, with the standard easing
    corner_radius: {duration: 200, easing: emphasized_decelerate}
    scale: {duration: 300, easing: spring, bounce: 0.3}
    opacity: {duration: 100, easing: [0.2, 0, 0, 1]}  # or four numbers: a cubic bezier
```

- The keys are style fields: `background`, `foreground` (a Text's or Icon's colour), `border_color`, `border_width`, `corner_radius`, `elevation`,
  `opacity`, `blur`, `backdrop_blur`, `scale`, `translate_x`, `translate_y` and `rotation_deg`. `all: 150` covers every one of them; a named key wins over `all`.
  An `Icon` also has `icon`, below.
- A value is a number of milliseconds, or `{duration, easing, bounce}`. The easings are `linear`, Material's `standard`, `standard_accelerate`,
  `standard_decelerate`, `emphasized`, `emphasized_accelerate` and `emphasized_decelerate`, four numbers (a cubic bezier, as CSS writes
  `cubic-bezier`), and `spring`, whose `duration` is its period and whose `bounce` is a number above -1 and below 1 (above 0 overshoots).
- Layout eases too: `width`, `height`, `x`, `y`, `gap`, `padding` and `margin` (`all` leaves these out, since a layout that changes is not always meant
  to glide). The engine eases them in pixels. A value that is not a number, such as `auto` or `50%`, changes at once, and a change begun in the middle of another goes on from where the first had got to.
- When the app has asked for reduced motion, a change happens at once.
- A transition is part of a style, so a stylesheet rule can carry it: a rule for `state: hovered` that changes `background` eases if the rule for the widget gives a `transition`.

An `Icon` whose glyph changes can morph into the next with `transition: {icon: 200}`: two closed shapes, or two open lines, in the same set of glyphs (Material Symbols or MDI) blend smoothly;
shapes with different numbers of parts switch halfway, and glyphs of the other set switch at once. `all` does not include `icon`. `IconButton` does this for its toggle icons.

`scale` (1 is unchanged), `translate_x`, `translate_y` (pixels) and `rotation_deg` (clockwise, about the node's centre) draw a node transformed, and
can be eased too. They change how it is drawn, not how much room it takes.

## The pointer

`cursor` is the name of a pointer shape, or a picture next to the view. The names are `default`, `pointer`, `text`, `grab`, `grabbing`, `move`,
`not_allowed`, `wait`, `progress`, `crosshair`, `help`, `col_resize`, `row_resize`, `ew_resize`, `ns_resize`, `nesw_resize`, `nwse_resize`, `copy`, `cell`,
`context_menu`, `zoom_in`, `zoom_out` and `all_scroll` (also in the [YAML reference](../api/yaml.md)). A handler can change a node's pointer while it runs
with `cursor('grabbing')` (see [Dragging](view-language.md#dragging)).

```yaml
widget: Container
style: {width: 120, height: 80, cursor: {src: pointers/pen.png, hotspot: [2, 30]}}
```

The picture is read with the view, like an `Image`'s: relative to the view's folder, inside it, 1 to 256 pixels a
side, and `hotspot` is the pixel that is the pointer's place. It is in device pixels, so give a larger one for a
high-density screen. A picture is only given in a node's own `style:`, not in a stylesheet. A `Link` keeps
`pointer` unless it says another.

`pointer_events: none` lets the pointer through the node itself, so a decorative layer laid over a button does not swallow the click: it goes to
whatever is under the layer, and the layer is not hovered or pressed. `auto` is the usual. It is about the node alone: what is inside a
`pointer_events: none` node still takes the pointer (as in CSS), and so does its focus and its place in the accessibility tree, which this
does not change.

```yaml
widget: Container
style: {width: 200, height: 80}
children:
  - widget: Rect              # the card
    name: card
    style: {width: 200, height: 80, background: surface_container}
    handlers: {on_click: open_card}
  - widget: Rect              # a shimmer over it; the card underneath still gets the click
    name: shimmer
    style: {position: absolute, x: 0, y: 0, width: "100%", height: "100%", background: "primary@8%", pointer_events: none}
```
