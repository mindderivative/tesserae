# YAML Reference

Every key Tesserae's YAML files take, with the values it accepts and what it does. This page is written from the same schemas your editor uses (`tesserae schema`), so it can't fall behind the code. For how the pieces fit, see the [guide](../guide/layout.md).

## The files

| File | What it is | Reference |
| --- | --- | --- |
| `<Name>_View.yaml` | A screen: one node with its children. | [The node](#the-node) |
| `<Name>_Component.yaml` | A reusable fragment with `params:`. | [Components](#components) |
| `<Name>_Shell.yaml` | The frame around the screens: bars, navigation, zones. | [Shell file](#shell-file) |
| `<Name>_Theme.yaml` | A theme: colours, type, shapes and style rules. | [Theme and stylesheet](#theme-and-stylesheet) |
| `<Name>_Stylesheet.yaml` | Style rules for a view. | [Theme and stylesheet](#theme-and-stylesheet) |
| `<Name>_Style.yaml` | One node's `style:`, shared. | [The style](#the-style) |

## The node

A view is one node, with its children inside it. A node is a widget (`kind:`), a fragment used in place (`component:`), or a file put in place (`include:`).

```yaml
id: <text>
kind: <one of 20 names>
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
image:
  src: <text>
  fit: <text>
svg:
  src: <text>
  content: <text>
icon:
  name: <one of 15 names>
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
| `image` | a mapping | An Image's source and fit. |
| `image.src` | text | An image file, relative to this one. |
| `image.fit` | text | How it fills its box: `cover` (the default), `contain`, ... |
| `svg` | a mapping | An Svg's document: a file, or its text. |
| `svg.src` | text | An SVG file (`.svg` or `.svgz`), relative to this view. The pictures it refers to are decoded and found next to it. |
| `svg.content` | text | The SVG document itself, as text. |
| `icon` | a mapping | An Icon's glyph. |
| `icon.name` *(required)* | one of 15 names | An icon in Tesserae's set. |
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
| `Icon` | A glyph from Tesserae's icon set, coloured by `style.foreground`. | `icon:` |
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
| `TitleBar` | The window's own title bar: an icon, a title, your content and the window's buttons. Needs `App(decorations=False)`. | `title:`, `icon:`, `buttons:` |

## The style

A node's `style:` is a mapping of these fields, or the name of a `*_Style.yaml` file. The same fields go in a stylesheet's or theme's rules, and in a shell file's parts.

| Field | Values | What it does |
| --- | --- | --- |
| `align_cells` | `top_left` \| `top` \| `top_right` \| `left` \| `center` \| `right` \| `bottom_left` \| `bottom` \| `bottom_right` | In a grid: where each item sits in its cell. |
| `align_content` | `top_left` \| `top` \| `top_right` \| `left` \| `center` \| `right` \| `bottom_left` \| `bottom` \| `bottom_right` | Where its children sit: `top_left`, `top`, `top_right`, `left`, `center`, `right`, `bottom_left`, `bottom` or `bottom_right`. Not set, they fill the space across the layout. |
| `align_self` | `top_left` \| `top` \| `top_right` \| `left` \| `center` \| `right` \| `bottom_left` \| `bottom` \| `bottom_right` | Its own place in its parent, over the parent's `align_content`. |
| `align_tracks` | `start` \| `center` \| `end` \| `stretch` \| `between` \| `around` \| `evenly` | In a grid: how the tracks share the room left over. |
| `align_wrapped` | `start` \| `center` \| `end` \| `stretch` \| `between` \| `around` \| `evenly` | With `flex_wrap: wrap`: how the lines share the room left over. |
| `aspect_ratio` | a number | Width over height: gives the missing side from the one set. |
| `backdrop_blur` | a number | Blurs what is behind it, by this many pixels: with a translucent `background`, a frosted surface. |
| `background` | a color or a gradient | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| `blend_mode` | one of 16 names | How it is drawn over what is behind it, as CSS `mix-blend-mode`. |
| `blur` | a number | Blurs the node and what it draws, by this many pixels. |
| `border_color` | a color or a gradient | The colour of its border: a colour or a gradient. |
| `border_width` | a number | The width of its border, in pixels. |
| `clip_children` | `true` or `false` | Whether children are cut off at its edge. |
| `column_gap` | a number | Space between columns (defaults to `gap`). |
| `corner_radius` | a number or `extra_large` \| `extra_small` \| `large` \| `medium` \| `none` \| `small` | Pixels, or a shape token (`none` to `extra_large`). |
| `cursor` | one of 23 names or a mapping | The pointer over it: a name, or `{src: cursor.png, hotspot: [x, y]}` (a picture next to the view, at most 256 pixels a side; only in a node's own `style:`). |
| `cursor.src` *(required)* | text | A PNG (or any picture Pillow reads) next to the view. |
| `cursor.hotspot` | a list | `[x, y]`: the pixel that is the pointer's place. |
| `display` | `flex` \| `grid` | `flex` (the default) or `grid`. |
| `elevation` | a number or `level_0` \| `level_1` \| `level_2` \| `level_3` \| `level_4` \| `level_5` | A shadow level, 0 to 5. |
| `filter` | a mapping | Colour filters over it and its children, as in CSS: `{grayscale: 1}`, `{saturate: 0.4, brightness: 0.9}` (`hue_rotate` is in degrees). |
| `filter.saturate` | a number | 1 is unchanged, 0 grey, above 1 more vivid. |
| `filter.brightness` | a number | 1 is unchanged, 0 black, above 1 brighter. |
| `filter.contrast` | a number | 1 is unchanged, 0 flat grey, above 1 harder. |
| `filter.grayscale` | a number | 0 is unchanged, 1 fully grey. |
| `filter.hue_rotate` | a number | Turns the hues, in degrees. |
| `filter.invert` | a number | 0 is unchanged, 1 inverted. |
| `filter.sepia` | a number | 0 is unchanged, 1 fully sepia. |
| `flex` | `none` \| `expand_horizontal` \| `expand_vertical` \| `fill` | How it takes room in its parent: `none` (the default) is as big as its content and never squeezed, `expand_horizontal` and `expand_vertical` take the room left over in that direction, `fill` both. |
| `flex_direction` | `horizontal` \| `vertical` | How its children are laid out: `horizontal` (the default) or `vertical`. |
| `flex_wrap` | `no_wrap` \| `wrap` | `wrap` lets children flow onto more lines; `no_wrap` keeps one. |
| `foreground` | a color or a gradient | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| `gap` | a number | Space between its children. |
| `grid_auto_columns` | text | The size of columns the template doesn't name. |
| `grid_auto_flow` | `row` \| `column` \| `row dense` \| `column dense` \| `dense` | How grid children fill the cells. |
| `grid_auto_rows` | text | The size of rows the template doesn't name. |
| `grid_column` | text or an integer | Which grid column it takes: `2`, or `1 / 3`. |
| `grid_row` | text or an integer | Which grid row it takes: `2`, or `1 / 3`. |
| `grid_template_columns` | text | The grid's columns, as in CSS: `1fr 2fr 100px`. |
| `grid_template_rows` | text | The grid's rows, as in CSS. |
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
| `opacity` | a number | From 0 (clear) to 1 (opaque). |
| `padding` | a number or a mapping | Space inside it: one number, or `{left, right, top, bottom}`. |
| `padding.top` | a number | Space on the top side. |
| `padding.right` | a number | Space on the right side. |
| `padding.bottom` | a number | Space on the bottom side. |
| `padding.left` | a number | Space on the left side. |
| `position` | `relative` \| `absolute` | `absolute` takes it out of the flow and places it at `x` and `y`. |
| `row_gap` | a number | Space between rows (defaults to `gap`). |
| `spread` | `none` \| `between` \| `around` \| `evenly` | Spreads its children along the layout: `between` (the space goes between them), `around` or `evenly`. |
| `sticky` | a number | In a scroll view, it sticks this many pixels from the top edge as its siblings scroll past. |
| `width` | a number or `auto` or a percentage such as `50%` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `x` | a number or `auto` | Where an `absolute` node sits from the left. |
| `y` | a number or `auto` | Where an `absolute` node sits from the top. |
| `z_index` | an integer | Stacking order: higher is in front. |

## Colors

Any field that takes a color takes a theme role (such as `surface` or `on_primary`), `#RGB`, `#RRGGBB`, `#RRGGBBAA`, `transparent`, a CSS colour name, or a CSS function such as `rgb(...)` or `oklch(...)`.

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
overflow: <clip | ellipsis>
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
| `overflow` | `clip` \| `ellipsis` | What happens to a line that doesn't fit its node: `clip` (the default) cuts it off, `ellipsis` ends it with an ellipsis. Not for a TextField. |

## Handlers

`handlers:` names what an event calls: a ViewModel method, or one of `window.minimize`, `window.maximize`, `window.restore`, `window.toggle_maximized`, `window.close`.

| Event | Values | What it does |
| --- | --- | --- |
| `on_click` | a method name | Runs on `click`. |
| `on_hover_enter` | a method name | Runs on `pointer_enter`. |
| `on_hover_exit` | a method name | Runs on `pointer_leave`. |
| `on_change` | a method name | Runs on `change`. |
| `on_focus_enter` | a method name | Runs on `focus`. |
| `on_focus_exit` | a method name | Runs on `unfocus`. |

## Accessibility

`a11y:` on any node.

| Key | Values | What it does |
| --- | --- | --- |
| `label` | text | The name a screen reader says. |
| `role` | one of 23 names | What kind of thing it is. |
| `hidden` | `true` or `false` | Hide it from assistive technology. |
| `live` | `assertive` \| `off` \| `polite` | How changes to it are announced. |
| `level` | an integer | A heading's level. |

## The title bar

`kind: TitleBar`, for an app that draws its own window frame.

```yaml
id: <text>
kind: <TitleBar>
title: <text>
icon: <one of 15 names>
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
| `icon` | one of 15 names | An icon name, shown before the title. |
| `buttons` | a list | Which window buttons, in order: minimize, maximize, close (all by default). |
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
component: <one of 77 names or text>
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
| `component` *(required)* | one of 77 names or text | A fragment: one of Tesserae's, or one of your own `<Name>_Component.yaml`. |
| `with` | a mapping | The fragment's parameters. |
| `repeat` | a list | One call per entry, each merged over `with:`. |

**Writing one**: a `*_Component.yaml` is a node, plus

| Key | Values | What it does |
| --- | --- | --- |
| `params` | a list | The parameters this fragment takes: each `{{ name }}` is filled from `with:`. A name is required; `{name: default}` is optional. |
| `when` | any value | Keeps this child only when the value is true. |

Inside a fragment, any value can also be a `{{ parameter }}`, or chosen by one with `{if: "{{ flag }}", then: a, else: b}`.

## Shell file

`*_Shell.yaml`: [App Shell & Docking](../guide/app-shell.md).

```yaml
style: <a style mapping>
top_bar:
  title: <text>
  leading_icon: <one of 15 names>
  trailing_icons: <a list>
  style: <a style mapping>
navigation:
  items: <a list>
  on_navigate: <text>
  style: <a style mapping>
status_bar:
  text: <text>
  style: <a style mapping>
content:
  style: <a style mapping>
zones:
  left: <a number or a mapping>
  right: <a number or a mapping>
  top: <a number or a mapping>
  bottom: <a number or a mapping>
center: <true or false>
panels:
  left: <a list>
  right: <a list>
  top: <a list>
  bottom: <a list>
  center: <a list>
```

| Key | Values | What it does |
| --- | --- | --- |
| `style` | a `style` mapping | The whole shell's style. |
| `top_bar` | a mapping | The bar across the top. |
| `top_bar.title` *(required)* | text | The title shown in the bar. |
| `top_bar.leading_icon` | one of 15 names | An icon before the title, such as a menu. |
| `top_bar.trailing_icons` | a list | Icons after the title, as icon buttons. |
| `top_bar.style` | a `style` mapping | A node's `style:`: `height`, `background`, `padding`, ... |
| `navigation` | a mapping | A navigation rail of screens. |
| `navigation.items` *(required)* | a list | The screens, in order. |
| `navigation.items[].screen` *(required)* | text | A registered screen's name. |
| `navigation.items[].icon` *(required)* | one of 15 names | An icon name. |
| `navigation.on_navigate` | text | A ViewModel method to call instead of showing the screen. |
| `navigation.style` | a `style` mapping | A node's `style:`: `height`, `background`, `padding`, ... |
| `status_bar` | a mapping | The bar across the bottom. |
| `status_bar.text` *(required)* | text | The text shown in the bar. |
| `status_bar.style` | a `style` mapping | A node's `style:`: `height`, `background`, `padding`, ... |
| `content` | a mapping | Where the screens show. |
| `content.style` | a `style` mapping | A node's `style:`: `height`, `background`, `padding`, ... |
| `zones` | a mapping | Docked areas around the content: a size in pixels, or `{size, style}`. |
| `zones.left` | a number or a mapping | The left zone: its size in pixels, or `{size, style}`. |
| `zones.left.size` *(required)* | a number | The zone's size in pixels. |
| `zones.left.style` | a `style` mapping | How a node looks and lays out its children. |
| `zones.right` | a number or a mapping | The right zone: its size in pixels, or `{size, style}`. |
| `zones.right.size` *(required)* | a number | The zone's size in pixels. |
| `zones.right.style` | a `style` mapping | How a node looks and lays out its children. |
| `zones.top` | a number or a mapping | The top zone: its size in pixels, or `{size, style}`. |
| `zones.top.size` *(required)* | a number | The zone's size in pixels. |
| `zones.top.style` | a `style` mapping | How a node looks and lays out its children. |
| `zones.bottom` | a number or a mapping | The bottom zone: its size in pixels, or `{size, style}`. |
| `zones.bottom.size` *(required)* | a number | The zone's size in pixels. |
| `zones.bottom.style` | a `style` mapping | How a node looks and lays out its children. |
| `center` | `true` or `false` | Whether the middle is a dock zone too, with the screens as its tabs. |
| `panels` | a mapping | Which panels (screens) sit in which zone. |
| `panels.left` | a list | The panels docked on the left, in tab order. |
| `panels.right` | a list | The panels docked on the right, in tab order. |
| `panels.top` | a list | The panels docked on the top, in tab order. |
| `panels.bottom` | a list | The panels docked on the bottom, in tab order. |
| `panels.center` | a list | The panels docked in the middle, in tab order. |

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
