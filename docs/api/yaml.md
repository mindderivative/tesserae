# YAML Reference

Every key Tesserae's YAML files take, with the values it accepts and what it does. This page is written from the same schemas your editor uses (`tesserae schema`), so it can't fall behind the code. For how the pieces fit, see the [guide](../guide/layout.md).

## The files

| File | What it is | Reference |
| --- | --- | --- |
| `<Name>_View.yaml` | A screen: one node with its children. | [The node](#the-node) |
| `<Name>_Component.yaml` | A reusable fragment with `params:`. | [Components](#components) |
| `<Name>_Theme.yaml` | A theme: colours, type, shapes and style rules. | [Theme and stylesheet](#theme-and-stylesheet) |
| `<Name>_Stylesheet.yaml` | Style rules for a view. | [Theme and stylesheet](#theme-and-stylesheet) |
| `<Name>_Style.yaml` | One node's `style:`, shared. | [The style](#the-style) |

## The node

A view is one node, with its children inside it. A node is a widget (`kind:`), a fragment used in place (`component:`), a file put in place (`include:`), or another view shown there (`view:`, below).

```yaml
id: <text>
kind: <one of 22 names>
classes: <a list>
style: <a style mapping or text>
text: <a mapping>
checked: <true or false or text>
selected: <true or false or text>
value: <a number or text>
hour: <a number or text>
minute: <a number or text>
min: <a number or text>
max: <a number or text>
step: <a number or text>
track: <text or any value>
ticks: <true or false or text>
value_indicator: <true or false or text>
icons: <true or false or text>
error: <true or false or text>
buffer: <a number or text>
stop_indicator: <true or false or text>
image:
  src: <text>
  fit: <text>
svg:
  src: <text>
  content: <text>
canvas:
  draw: <a list>
scroll:
  offset: <a number>
virtual:
  count: <an integer>
  extent: <a number>
overlay:
  modal: <true or false>
icon:
  name: <one of 164 names>
  path: <text>
  view_box: <a list>
bindings: <a mapping>
handlers: <a mapping>
two_way: <text>
interaction:
  color: <a color>
a11y: <a mapping>
group: <text>
component_of: <text>
disabled: <true or false or text>
window_region: <drag | none>
label: <text>
x: <a number or text>
y: <a number or text>
edges: <a list>
children: <a list>
```

| Key | Values | What it does |
| --- | --- | --- |
| `id` *(required)* | text | A name for this node, unique in the view. Handlers, bindings and `view.node(id)` use it. |
| `kind` *(required)* | a [kind](#the-kinds) | What this node is. |
| `classes` | a list | Style classes a theme or stylesheet rule can match. |
| `style` | a `style` mapping or text | How a node looks: a mapping, or the name of a `*_Style.yaml` file. |
| `text` | a mapping | What a Text, Link or TextField says, and in what type. |
| `checked` | `true` or `false` or text | A Checkbox's state. |
| `selected` | `true` or `false` or text | A Switch's or RadioButton's state. |
| `value` | a number or text | A Slider's or SpinBox's value. |
| `hour` | a number or text | A TimePickerDial's hour. |
| `minute` | a number or text | A TimePickerDial's minute. |
| `min` | a number or text | The least a Slider or SpinBox takes. |
| `max` | a number or text | The most a Slider or SpinBox takes. |
| `step` | a number or text | How far a Slider or SpinBox moves. |
| `track` | text or any value | The colour role of the track behind a progress indicator. |
| `ticks` | `true` or `false` or text | Whether a Slider marks each step. |
| `value_indicator` | `true` or `false` or text | Whether a Slider shows a bubble with its value over the handle. |
| `icons` | `true` or `false` or text | Whether a Switch shows a check or a cross on its handle. |
| `error` | `true` or `false` or text | Whether a Checkbox or RadioButton is drawn in the error colours. |
| `buffer` | a number or text | A LinearProgress's loaded share, 0 to 1. |
| `stop_indicator` | `true` or `false` or text | Whether a LinearProgress shows a dot at the end of its track. |
| `image` | a mapping | An Image's source and fit. |
| `image.src` | text | An image file, relative to this one. |
| `image.fit` | text | How it fills its box: `cover` (the default), `contain`, ... |
| `svg` | a mapping | An Svg's document: a file, or its text. |
| `svg.src` | text | An SVG file (`.svg` or `.svgz`), relative to this view. The pictures it refers to are decoded and found next to it. |
| `svg.content` | text | The SVG document itself, as text. |
| `canvas` | a mapping | A Canvas's drawing commands. |
| `canvas.draw` | a list | Commands painted in order: `rect: [x, y, w, h]`, `circle: [cx, cy, r]` or `path: [points]` (with `width`), each with a `color`. |
| `scroll` | a mapping | A ScrollView's position. |
| `scroll.offset` | a number | How far it is scrolled, in pixels. |
| `virtual` | a mapping | A VirtualList's length: how many rows there are, and how tall each is. |
| `virtual.count` | an integer | How many rows the list has. |
| `virtual.extent` | a number | How tall each row is, in pixels. |
| `overlay` | a mapping | An Overlay's shape. |
| `overlay.modal` | `true` or `false` | Whether the layer is a scrim over the whole window. |
| `icon` | a mapping | An Icon's glyph. |
| `icon.name` | one of 164 names | An icon in Tesserae's set. |
| `icon.path` | text | SVG path data, instead of a name. |
| `icon.view_box` | a list | [min_x, min_y, width, height] the path is drawn in (default 0 -960 960 960). |
| `bindings` | a mapping | Properties kept live from the ViewModel: `{{ expression }}`. |
| `handlers` | a mapping | What a user's action calls: the name of a ViewModel method, or `window.<action>`. |
| `two_way` | text | The one bound property whose user edits write back to the ViewModel. |
| `interaction` | `true` or `false` or a mapping | A Rect or Container's hover, press and focus feedback: `true`, `false`, or `{color: ...}`. |
| `interaction.color` | a color | A color. |
| `a11y` | a mapping | What assistive technology is told about this node. |
| `group` | text | A RadioButton's group: the ones with one name exclude each other. |
| `component_of` | text | The fragment this node is the root of. |
| `disabled` | `true` or `false` or text | Whether the node ignores input and fades. |
| `window_region` | `drag` \| `none` | `drag`: a press here moves the window (a title bar); `none`: it does not. |
| `label` | text | A GraphNode's title. |
| `x` | a number or text | A GraphNode's place. |
| `y` | a number or text | A GraphNode's place. |
| `edges` | a list | A NodeGraph's edges. |
| `children` | a list | The nodes inside this one. |

## The kinds

`kind:` says what a node is. Beyond the keys every node has, each kind uses a few.

| Kind | What it is | It also uses |
| --- | --- | --- |
| `Rect` | A box you paint: a fill, a border, rounded corners, a shadow. Holds children. Takes `interaction:` and click handlers. | Only the common keys. |
| `Container` | A box that lays out its children and paints nothing unless you style it. Takes `interaction:` and click handlers. | Only the common keys. |
| `ScrollView` | A box whose children scroll when they are bigger than it. | Only the common keys. |
| `Text` | Text in one style. | `text:` |
| `Link` | Text that is clickable, with focus and a keyboard activation. | `text:`, `handlers: {on_click}` |
| `TextField` | A single-line text input in a box. | `text:`, `two_way:`, `handlers: {on_change}` |
| `Image` | A picture from a file. | `image:` |
| `Svg` | An SVG document, drawn by the engine: shapes, gradients, text, clips and masks. `style.foreground` is what `currentColor` means, so an icon follows the theme. | `svg:` |
| `VirtualList` | A scrolling list of equal rows that builds only the rows in view. Its one child is a `for:`. | `virtual:`, `scroll:` |
| `Overlay` | A layer over the window while `open`: anchored to a node, or a modal scrim. Takes no room where it is written; its children are the layer's. | `overlay:` |
| `Canvas` | A drawing surface: rectangles, circles and paths from a `draw:` list, repainted when the Signals it reads change. | `canvas:` |
| `Icon` | A glyph from Tesserae's icon set, or from SVG path data, coloured by `style.foreground`. | `icon:` (`name:`, or `path:` and `view_box:`) |
| `Checkbox` | MD3's checkbox. | `checked:`, `disabled:`, `handlers: {on_change}` |
| `RadioButton` | MD3's radio button; the ones with one `group:` exclude each other. | `selected:`, `group:`, `disabled:` |
| `Switch` | MD3's switch. | `selected:`, `disabled:` |
| `Slider` | MD3's slider. | `value:`, `min:`, `max:`, `step:` |
| `SpinBox` | A number field between − and + buttons. | `value:`, `min:`, `max:`, `step:` |
| `CircularProgress` | A circular progress indicator; no `value:` means indeterminate. | `value:` |
| `LinearProgress` | A linear progress indicator; no `value:` means indeterminate. | `value:` |
| `LoadingIndicator` | MD3's loading indicator, always indeterminate. | Only the common keys. |
| `TimePickerDial` | MD3's time picker dial. | `hour:`, `minute:` |
| `NodeGraph` | A pannable canvas of `GraphNode`s joined by edges. | `edges:`, children that are `GraphNode`s |
| `GraphNode` | A node in a `NodeGraph`: a titled box at a place. | `label:`, `x:`, `y:` |
| `TitleBar` | A title bar: an icon, a title, your content and the window's buttons (`App(borderless=True)`), or a close button for a dialog or a sheet (`buttons: [dismiss]`). | `title:`, `icon:`, `buttons:` |
| `Window` | The root of a view that is the whole OS window: its title, `borderless`, a `title_bar:`, and the content under it. | `title:`, `borderless:`, `min_width:`, `min_height:`, `title_bar:` |
| `Dock` | Panels docked in zones (left, right, top, bottom, center) around the middle, with handles to resize them. One per window. | `DockPanel` children |
| `DockPanel` | A panel in a Dock, in the zone its `style: {zone: ...}` names; panels in one zone are its tabs. Inside another DockPanel it is a split of it. | `title:`, `style: {zone}` |

## The style

A node's `style:` is a mapping of these fields, or the name of a `*_Style.yaml` file, which holds them under a `style:` key (and an optional `id:` naming it): `{id: row_style, style: {gap: 8}}`. The same fields go in a stylesheet's or theme's rules.

### Size and spacing

| Field | Values | What it does |
| --- | --- | --- |
| `aspect_ratio` | a number | Width over height: gives the missing side from the one set. |
| `height` | a number or `auto` or a percentage such as `50%` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `margin` | a number or a mapping | Space outside it: one number, or `{left, right, top, bottom}`. |
| `margin.top` | a number | Space on the top side. |
| `margin.right` | a number | Space on the right side. |
| `margin.bottom` | a number | Space on the bottom side. |
| `margin.left` | a number | Space on the left side. |
| `max_height` | a number or `auto` or a percentage such as `50%` | The most height it can take. |
| `max_width` | a number or `auto` or a percentage such as `50%` | The most width it can take. |
| `min_height` | a number or `auto` or a percentage such as `50%` | The least height it can take. |
| `min_width` | a number or `auto` or a percentage such as `50%` | The least width it can take. |
| `padding` | a number or a mapping | Space inside it: one number, or `{left, right, top, bottom}`. |
| `padding.top` | a number | Space on the top side. |
| `padding.right` | a number | Space on the right side. |
| `padding.bottom` | a number | Space on the bottom side. |
| `padding.left` | a number | Space on the left side. |
| `width` | a number or `auto` or a percentage such as `50%` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |

### Flex

| Field | Values | What it does |
| --- | --- | --- |
| `flex` | `none` \| `expand_horizontal` \| `expand_vertical` \| `fill` | How it takes room in its parent: `none` (the default) is as big as its content and never squeezed, `expand_horizontal` and `expand_vertical` take the room left over in that direction, `fill` both. |
| `flex_direction` | `horizontal` \| `vertical` | How its children are laid out: `horizontal` (the default) or `vertical`. |
| `flex_wrap` | `no_wrap` \| `wrap` | `wrap` lets children flow onto more lines; `no_wrap` keeps one. |
| `gap` | a number | Space between its children. |

### Alignment

| Field | Values | What it does |
| --- | --- | --- |
| `align_content` | `top_left` \| `top` \| `top_right` \| `left` \| `center` \| `right` \| `bottom_left` \| `bottom` \| `bottom_right` | Where its children sit: `top_left`, `top`, `top_right`, `left`, `center`, `right`, `bottom_left`, `bottom` or `bottom_right`. Not set, they fill the space across the layout. |
| `align_self` | `top_left` \| `top` \| `top_right` \| `left` \| `center` \| `right` \| `bottom_left` \| `bottom` \| `bottom_right` | Its own place in its parent, over the parent's `align_content`. |
| `align_wrapped` | `start` \| `center` \| `end` \| `stretch` \| `between` \| `around` \| `evenly` | With `flex_wrap: wrap`: how the lines share the room left over. |
| `spread` | `none` \| `between` \| `around` \| `evenly` | Spreads its children along the layout: `between` (the space goes between them), `around` or `evenly`. |

### Grid

| Field | Values | What it does |
| --- | --- | --- |
| `align_cells` | `top_left` \| `top` \| `top_right` \| `left` \| `center` \| `right` \| `bottom_left` \| `bottom` \| `bottom_right` | In a grid: where each item sits in its cell. |
| `align_tracks` | `start` \| `center` \| `end` \| `stretch` \| `between` \| `around` \| `evenly` | In a grid: how the tracks share the room left over. |
| `column_gap` | a number | Space between columns (defaults to `gap`). |
| `display` | `flex` \| `grid` | `flex` (the default) or `grid`. |
| `grid_auto_columns` | text | The size of columns the template doesn't name. |
| `grid_auto_flow` | `row` \| `column` \| `row dense` \| `column dense` \| `dense` | How grid children fill the cells. |
| `grid_auto_rows` | text | The size of rows the template doesn't name. |
| `grid_column` | text or an integer | Which grid column it takes: `2`, or `1 / 3`. |
| `grid_row` | text or an integer | Which grid row it takes: `2`, or `1 / 3`. |
| `grid_template_columns` | text | The grid's columns, as in CSS: `1fr 2fr 100px`. |
| `grid_template_rows` | text | The grid's rows, as in CSS. |
| `row_gap` | a number | Space between rows (defaults to `gap`). |

### Position

| Field | Values | What it does |
| --- | --- | --- |
| `position` | `relative` \| `absolute` | `absolute` takes it out of the flow and places it at `x` and `y`. |
| `sticky` | a number | In a scroll view, it sticks this many pixels from the top edge as its siblings scroll past. |
| `x` | a number or `auto` | Where an `absolute` node sits from the left. |
| `y` | a number or `auto` | Where an `absolute` node sits from the top. |
| `z_index` | an integer | Stacking order: higher is in front. |

### Docking

| Field | Values | What it does |
| --- | --- | --- |
| `zone` | `left` \| `right` \| `top` \| `bottom` \| `center` | A DockPanel's zone in its Dock: where it docks. Only a DockPanel directly in a Dock has one; anywhere else it is an error. |

### Motion

| Field | Values | What it does |
| --- | --- | --- |
| `rotation_deg` | a number | Turns the node by this many degrees, clockwise, about its centre. |
| `scale` | a number | Draws the node and what is in it at this multiple of its size (1 is unchanged), about its centre. |
| `transition` | a mapping | Which style changes ease to their new value: a duration in milliseconds, or `{duration, easing, bounce}`. `all` covers every one that can. A node is where it says when first drawn; only a change eases. |
| `transition.<name>` | a number or a mapping | One for each of 21 names, such as `all`, `background`, `foreground`, `border_color`. |
| `translate_x` | a number | Draws the node this many pixels to the right of where it is laid out. |
| `translate_y` | a number | Draws the node this many pixels lower than where it is laid out. |

### Paint and effects

| Field | Values | What it does |
| --- | --- | --- |
| `backdrop_blur` | a number | Blurs what is behind it, by this many pixels: with a translucent `background`, a frosted surface. |
| `background` | a color or a gradient | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| `blend_mode` | one of 16 names | How it is drawn over what is behind it, as CSS `mix-blend-mode`. |
| `blur` | a number | Blurs the node and what it draws, by this many pixels. |
| `border_color` | a color or a gradient | The colour of its border: a colour or a gradient. |
| `border_width` | a number | The width of its border, in pixels. |
| `clip_children` | `true` or `false` | Whether children are cut off at its edge. |
| `corner_radius` | a number or `extra_large` \| `extra_small` \| `large` \| `medium` \| `none` \| `small` \| `full` or a list or a mapping | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |
| `corner_radius.top_left` | a number or `extra_large` \| `extra_small` \| `large` \| `medium` \| `none` \| `small` \| `full` | The radius of the top left corner. |
| `corner_radius.top_right` | a number or `extra_large` \| `extra_small` \| `large` \| `medium` \| `none` \| `small` \| `full` | The radius of the top right corner. |
| `corner_radius.bottom_right` | a number or `extra_large` \| `extra_small` \| `large` \| `medium` \| `none` \| `small` \| `full` | The radius of the bottom right corner. |
| `corner_radius.bottom_left` | a number or `extra_large` \| `extra_small` \| `large` \| `medium` \| `none` \| `small` \| `full` | The radius of the bottom left corner. |
| `corner_radius.top` | a number or `extra_large` \| `extra_small` \| `large` \| `medium` \| `none` \| `small` \| `full` | The radius of both top corners. |
| `corner_radius.right` | a number or `extra_large` \| `extra_small` \| `large` \| `medium` \| `none` \| `small` \| `full` | The radius of both right corners. |
| `corner_radius.bottom` | a number or `extra_large` \| `extra_small` \| `large` \| `medium` \| `none` \| `small` \| `full` | The radius of both bottom corners. |
| `corner_radius.left` | a number or `extra_large` \| `extra_small` \| `large` \| `medium` \| `none` \| `small` \| `full` | The radius of both left corners. |
| `cursor` | one of 23 names or a mapping | The pointer over it: a name, or `{src: cursor.png, hotspot: [x, y]}` (a picture next to the view, at most 256 pixels a side; only in a node's own `style:`). |
| `cursor.src` *(required)* | text | A PNG (or any picture Pillow reads) next to the view. |
| `cursor.hotspot` | a list | `[x, y]`: the pixel that is the pointer's place. |
| `elevation` | a number or `level_0` \| `level_1` \| `level_2` \| `level_3` \| `level_4` \| `level_5` | A shadow level, 0 to 5. |
| `filter` | a mapping | Colour filters over it and its children, as in CSS: `{grayscale: 1}`, `{saturate: 0.4, brightness: 0.9}` (`hue_rotate` is in degrees). |
| `filter.saturate` | a number | 1 is unchanged, 0 grey, above 1 more vivid. |
| `filter.brightness` | a number | 1 is unchanged, 0 black, above 1 brighter. |
| `filter.contrast` | a number | 1 is unchanged, 0 flat grey, above 1 harder. |
| `filter.grayscale` | a number | 0 is unchanged, 1 fully grey. |
| `filter.hue_rotate` | a number | Turns the hues, in degrees. |
| `filter.invert` | a number | 0 is unchanged, 1 inverted. |
| `filter.sepia` | a number | 0 is unchanged, 1 fully sepia. |
| `foreground` | a color or a gradient | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| `opacity` | a number | From 0 (clear) to 1 (opaque). |

## Colors

Any field that takes a color takes a theme role (such as `surface` or `on_primary`), `#RGB`, `#RRGGBB`, `#RRGGBBAA`, `transparent`, a CSS colour name, or a CSS function such as `rgb(...)` or `oklch(...)`. End any of them with `@N%` to scale its alpha: `primary@12%`.

## Gradients

`background`, `foreground` and `border_color` take a gradient where they take a color: a CSS-like string (`linear-gradient(90deg, primary, tertiary)`, `radial-gradient(at 30% 30%, primary_container, surface)`, `conic-gradient(from 90deg, primary, secondary, primary)`; `to right` and the like name a direction; a stop may have a place, `primary 40%`) or a mapping (`{gradient: linear, angle: 90, stops: [primary, [0.6, secondary], tertiary]}`). Stops are theme roles or colors. A control's color (a `Switch`, a `Slider`) takes a plain color only.

## The text

`text:` on a Text, Link or TextField.

```yaml
content: <text>
typography_role: <one of 15 names>
font_family: <text>
font_size: <a number>
font_weight: <a number>
line_height: <a number>
text_align: <start | center | end>
wrap: <word | none>
selectable: <true or false>
runs: <a list>
overflow: <clip | ellipsis>
max_lines: <an integer>
letter_spacing: <a number>
```

| Key | Values | What it does |
| --- | --- | --- |
| `content` | text | The text. |
| `typography_role` | one of 15 names | A Material 3 type style: it sets the font, size, weight and line height. |
| `font_family` | text | A font family, such as `Roboto`. |
| `font_size` | a number | Pixels. |
| `font_weight` | a number | 1 to 1000; 400 is regular, 700 bold. |
| `line_height` | a number | A multiple of the size. |
| `text_align` | `start` \| `center` \| `end` | Where the text sits in its node's width; a `center` or `end` Text with no width fills its parent's. Not for a TextField. |
| `wrap` | `word` \| `none` | `word` (the default) breaks a line that is too long for its node onto the next; `none` keeps one line. Not for a TextField. |
| `selectable` | `true` or `false` | A Text only: the user can select it with the pointer and copy it (Ctrl+C). |
| `runs` | a list | A Text only: the text as styled pieces, instead of `content`. A piece is a string, or `{text, color, weight, italic, underline, strikethrough, font_size, font_family, link}`. A piece with a `link` is `primary` and underlined, and a click on it calls `on_link` with `event.href`. |
| `overflow` | `clip` \| `ellipsis` | What happens to a line that doesn't fit its node: `clip` (the default) cuts it off, `ellipsis` ends it with an ellipsis. Not for a TextField. |
| `max_lines` | an integer | The most lines shown; a longer text is cut there (with `overflow: ellipsis`, the last line ends with an ellipsis). A Text with a width and no height is as tall as these lines. Not for a TextField. |
| `letter_spacing` | a number | Extra space between letters, in pixels (tracking); negative tightens. Not for a TextField. |

## Handlers

`handlers:` names what an event calls: a ViewModel method, or one of `window.minimize`, `window.maximize`, `window.restore`, `window.toggle_maximized`, `window.close`, `surface.dismiss`, `navigate.<Screen>`, `navigate.back`, `navigate.forward`.

| Event | Values | What it does |
| --- | --- | --- |
| `<name>` | a method name | One for each of 18 names, such as `on_click`, `on_hover_enter`, `on_hover_exit`, `on_change`.. |

## Accessibility

`a11y:` on any node.

| Key | Values | What it does |
| --- | --- | --- |
| `label` | text | The name a screen reader says. |
| `role` | one of 24 names | What kind of thing it is. |
| `hidden` | `true` or `false` | Hide it from assistive technology. |
| `live` | `assertive` \| `off` \| `polite` | How changes to it are announced. |
| `level` | an integer | A heading's level. |
| `expanded` | `true` or `false` or any value or text | Open or closed, on something that opens and closes. |
| `selected` | `true` or `false` or any value or text | One of a set, chosen. |
| `checked` | `true` or `false` or any value or text | On or off. |
| `value` | a number or any value or text | A number the node holds. |
| `value_min` | a number or any value or text | Its least. |
| `value_max` | a number or any value or text | Its most. |
| `value_step` | a number or any value or text | One step. |
| `pressed` | `true` or `false` or `mixed` or any value or text | A toggle button's state: true, false or `mixed`. |
| `invalid` | `true` or `false` or any value or text | The value is not acceptable. |
| `description` | text or any value | A longer description than the label. |
| `describedby` | text or a list | The `name:` of a node in this view that describes this one, or a list. |
| `controls` | text or a list | The `name:` of a node in this view that this one controls, or a list. |
| `current` | `true` or `false` or `date` \| `location` \| `page` \| `step` \| `time` or any value or text | The current item of a set: `page`, `step`, `location`, `date`, `time` or true. |
| `value_now` | a number or any value or text | The value of a range. |
| `value_text` | text or any value | How a range's value is said. |
| `busy` | `true` or `false` or any value or text | The node is updating. |

## The title bar

`kind: TitleBar`, for an app that draws its own window frame.

```yaml
id: <text>
kind: <TitleBar>
title: <text>
icon: <one of 164 names>
buttons: <a list>
children: <a list>
style: <a style mapping or text>
classes: <a list>
a11y: <a mapping>
```

| Key | Values | What it does |
| --- | --- | --- |
| `id` *(required)* | text | A name for this node, unique in the view. Handlers, bindings and `view.node(id)` use it. |
| `kind` *(required)* | `TitleBar` | Always `TitleBar`. |
| `title` | text | The window's title. |
| `icon` | one of 164 names | An icon name, shown before the title. |
| `buttons` | a list | Which window buttons, in order: minimize, maximize, close (all by default); or just `dismiss`, a button that closes the dialog or sheet the bar is in. |
| `children` | a list | The nodes inside this one. |
| `style` | a `style` mapping or text | How a node looks: a mapping, or the name of a `*_Style.yaml` file. |
| `classes` | a list | Style classes a theme or stylesheet rule can match. |
| `a11y` | a mapping | What assistive technology is told about this node. |

## Components

`component: Name` puts a fragment in place, filling its `{{ parameters }}` from `with:`. [Every built-in one](../components/index.md) has a page.

**Using one**

```yaml
handlers: <a mapping>
bindings: <a mapping>
two_way: <text>
a11y: <a mapping>
interaction:
  color: <a color>
classes: <a list>
window_region: <drag | none>
id: <text>
component: <one of 79 names or text>
with: <a mapping>
repeat: <a list>
```

| Key | Values | What it does |
| --- | --- | --- |
| `handlers` | a mapping | What a user's action calls: the name of a ViewModel method, or `window.<action>`. |
| `bindings` | a mapping | Properties kept live from the ViewModel: `{{ expression }}`. |
| `two_way` | text | The one bound property whose user edits write back to the ViewModel. |
| `a11y` | a mapping | What assistive technology is told about this node. |
| `interaction` | `true` or `false` or a mapping | A Rect or Container's hover, press and focus feedback: `true`, `false`, or `{color: ...}`. |
| `interaction.color` | a color | A color. |
| `classes` | a list | Style classes a theme or stylesheet rule can match. |
| `window_region` | `drag` \| `none` | `drag`: a press here moves the window (a title bar); `none`: it does not. |
| `id` | text | A name for this node, unique in the view. Handlers, bindings and `view.node(id)` use it. |
| `component` *(required)* | one of 79 names or text | A fragment: one of Tesserae's, or one of your own `<Name>_Component.yaml`. |
| `with` | a mapping | The fragment's parameters. |
| `repeat` | a list | One call per entry, each merged over `with:`. |

**Writing one**: a `*_Component.yaml` is a node, plus

| Key | Values | What it does |
| --- | --- | --- |
| `params` | a list | The parameters this fragment takes: each `{{ name }}` is filled from `with:`. A name is required; `{name: default}` is optional. |
| `when` | any value | Keeps this child only when the value is true. |

Inside a fragment, any value can also be a `{{ parameter }}`, or chosen by one with `{if: "{{ flag }}", then: a, else: b}`.

## The window

`kind: Window` is the root of a view that is the whole OS window (there is one per app, and it is not embedded or nested). Load it with `app.load("Window")` (or `App(window_view="Window")`). Its `title_bar:` takes a `TitleBar`'s keys and is the window's title bar when the window is `borderless`; its `children` are the content under it; `style:`'s `width` and `height` are the window's size and its `background` the window's.

```yaml
id: <text>
kind: <Window>
title: <text>
borderless: <true or false>
min_width: <a number>
min_height: <a number>
title_bar:
  id: <text>
  title: <text>
  icon: <one of 164 names>
  buttons: <a list>
  children: <a list>
  style: <a style mapping or text>
  classes: <a list>
  a11y: <a mapping>
style: <a style mapping or text>
classes: <a list>
a11y: <a mapping>
children: <a list>
```

| Key | Values | What it does |
| --- | --- | --- |
| `id` | text | A name for this node, unique in the view. Handlers, bindings and `view.node(id)` use it. |
| `kind` *(required)* | `Window` | Always `Window`. |
| `title` | text | The window's title. |
| `borderless` | `true` or `false` | The OS window has no title bar or borders of its own: the `title_bar:` is the window's. |
| `min_width` | a number | The narrowest the user can resize the window to. |
| `min_height` | a number | The shortest the user can resize the window to. |
| `title_bar` | `true` or `false` or a mapping | The window's title bar, a `TitleBar`'s keys: its `title` is the window's by default, and it has the window buttons when the window is `borderless`. |
| `title_bar.id` | text | A name for this node, unique in the view. Handlers, bindings and `view.node(id)` use it. |
| `title_bar.title` | text | The window's title. |
| `title_bar.icon` | one of 164 names | An icon name, shown before the title. |
| `title_bar.buttons` | a list | Which window buttons, in order: minimize, maximize, close (all by default); or just `dismiss`, a button that closes the dialog or sheet the bar is in. |
| `title_bar.children` | a list | The nodes inside this one. |
| `title_bar.style` | a `style` mapping or text | How a node looks: a mapping, or the name of a `*_Style.yaml` file. |
| `title_bar.classes` | a list | Style classes a theme or stylesheet rule can match. |
| `title_bar.a11y` | a mapping | What assistive technology is told about this node. |
| `style` | a `style` mapping or text | How a node looks: a mapping, or the name of a `*_Style.yaml` file. |
| `classes` | a list | Style classes a theme or stylesheet rule can match. |
| `a11y` | a mapping | What assistive technology is told about this node. |
| `children` | a list | The nodes inside this one. |

## The dock

`kind: Dock` holds `kind: DockPanel`s; each says which zone it is in with `style: {zone: left|right|top|bottom|center}`. Panels in one zone are its tabs (titled by `title:`), which the user can drag to another zone; the size of a left or right zone is its panel's `width`, a top or bottom one's its `height`, and a handle between a zone and the middle resizes it. A `DockPanel` inside a `DockPanel` is a split of it, side by side (`flex_direction: horizontal`, the default) or top and bottom (`vertical`), with a handle between them. A panel has splits or content, not both. From Python, `view.dock_host("dock")` has `layout()`, `restore(layout)`, `size(side)` and `set_size(side, size)`.

```yaml
id: <text>
kind: <Dock>
style: <a style mapping or text>
classes: <a list>
a11y: <a mapping>
children: <a list>
```

| Key | Values | What it does |
| --- | --- | --- |
| `id` | text | A name for this node, unique in the view. Handlers, bindings and `view.node(id)` use it. |
| `kind` *(required)* | `Dock` | Always `Dock`. |
| `style` | a `style` mapping or text | How a node looks: a mapping, or the name of a `*_Style.yaml` file. |
| `classes` | a list | Style classes a theme or stylesheet rule can match. |
| `a11y` | a mapping | What assistive technology is told about this node. |
| `children` | a list | The nodes inside this one. |

```yaml
id: <text>
kind: <DockPanel>
title: <text>
style: <a style mapping or text>
classes: <a list>
a11y: <a mapping>
children: <a list>
```

| Key | Values | What it does |
| --- | --- | --- |
| `id` | text | A name for this node, unique in the view. Handlers, bindings and `view.node(id)` use it. |
| `kind` *(required)* | `DockPanel` | Always `DockPanel`. |
| `title` | text | The panel's tab (its id by default). |
| `style` | a `style` mapping or text | How a node looks: a mapping, or the name of a `*_Style.yaml` file. |
| `classes` | a list | Style classes a theme or stylesheet rule can match. |
| `a11y` | a mapping | What assistive technology is told about this node. |
| `children` | a list | The nodes inside this one. |

## Embedded views

`view: Left_View.yaml` shows another view in place (or a name found in the project: `view: Left`). It is a view of its own, so its ids don't clash with this one's, and it has its own ViewModel when `Left_ViewModel.py` is beside it or in the project; a view with none is static (no bindings, handlers or `two_way:`). `with:` is given to the ViewModel's constructor as keyword arguments. From the host, `view.embedded("left")` is the embedded view and its `.viewmodel` the ViewModel. A relative file is relative to the file that names it.

```yaml
id: <text>
view: <text>
with: <a mapping>
route: <text>
style: <a style mapping or text>
classes: <a list>
a11y: <a mapping>
group: <text>
window_region: <drag | none>
```

| Key | Values | What it does |
| --- | --- | --- |
| `id` | text | A name for this node, unique in the view. Handlers, bindings and `view.node(id)` use it. |
| `view` *(required)* | text | The view to show: a `*_View.yaml` next to this file, or a name found in the project. |
| `with` | a mapping | What the embedded view's ViewModel is given, as keyword arguments to its constructor. |
| `route` | text | In the window view, makes the view a screen of the app: its route, such as `""`, `settings` or `notes/{id}`. A view can be routed once. |
| `style` | a `style` mapping or text | How a node looks: a mapping, or the name of a `*_Style.yaml` file. |
| `classes` | a list | Style classes a theme or stylesheet rule can match. |
| `a11y` | a mapping | What assistive technology is told about this node. |
| `group` | text | A RadioButton's group: the ones with one name exclude each other. |
| `window_region` | `drag` \| `none` | `drag`: a press here moves the window (a title bar); `none`: it does not. |

## Theme and stylesheet

A stylesheet has only `styles:`; a theme has everything. See [Themes](../themes/index.md).

```yaml
seed: <a color>
dark: <true or false>
colors:
  <name>: <a color>
typography:
  <name>: <a mapping>
components: <a mapping>
styles:
  - kind: ..., classes: ..., id: ..., style: ...
```

| Key | Values | What it does |
| --- | --- | --- |
| `seed` | a color | The colour the theme's palette is made from. |
| `dark` | `true` or `false` | Whether it is the dark scheme. |
| `colors` | a mapping | Colour roles to replace: a role name and a colour. |
| `colors.<name>` | a color | One for each of 49 names, such as `background`, `error`, `error_container`, `inverse_on_surface`. |
| `typography` | a mapping | Changes to Material 3's type styles, by role. |
| `typography.<name>` | a mapping | One for each of 15 names, such as `body_large`, `body_medium`, `body_small`, `display_large`. |
| `typography.<name>.font_family` | text | A font family. |
| `typography.<name>.font_size` | a number | Pixels. |
| `typography.<name>.font_weight` | a number | 1 to 1000. |
| `typography.<name>.line_height` | a number | A multiple of the size. |
| `typography.<name>.tracking` | a number | Extra space between letters, in pixels (Material 3's tracking: `tokens.MD3_TRACKING`). |
| `components` | a mapping | Per-component shape and elevation. |
| `styles` | a list | Style rules, in order. |
| `styles[].kind` | a [kind](#the-kinds) | Every node of this kind. |
| `styles[].classes` | a list | Nodes with all of these classes. |
| `styles[].id` | text | The node with this id. |
| `styles[].style` | a `style` mapping or text | How the matching nodes look: a mapping, or the name of a `*_Style.yaml` file. |

**A rule in `styles:`**

| Key | Values | What it does |
| --- | --- | --- |
| `kind` | a [kind](#the-kinds) | Every node of this kind. |
| `classes` | a list | Nodes with all of these classes. |
| `id` | text | The node with this id. |
| `style` | a `style` mapping or text | How the matching nodes look: a mapping, or the name of a `*_Style.yaml` file. |
