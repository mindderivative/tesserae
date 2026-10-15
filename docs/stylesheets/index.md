# Component Stylesheets

Every shipped view keeps its look in a stylesheet, `<Name>_Stylesheet.yaml`, beside the view itself, `<Name>_View.yaml`. Each page here shows one stylesheet, how its rules reach the view, and what each part's rules do.

## How they work

A stylesheet is a list of rules. A rule names a widget (the view), may narrow it, and gives a `style`:

```yaml
styles:
  - widget: Button
    variant: filled
    style: {background: primary, foreground: on_primary}
  - widget: Button
    variant: filled
    state: disabled
    style: {background: "on_surface@12%"}
  - widget: Card
    part: heading
    style: {foreground: on_surface}
```

- A rule narrows by the properties the view declares (`variant`, `size`, `shape`), `classes`, a node `name`, a `part` (a named node inside the view) and a `state`.
- A value in `{{ }}` is an expression over the view's parameters, worked out where the view is used.
- The most specific rule wins; a node's own `style:` beats every rule for the fields it sets.
- The shipped rules are the lowest layer. Your app's stylesheet goes over them, and a `<Name>_Stylesheet.yaml` of the same name next to your views replaces the shipped one.
- Hot reload watches the stylesheets a view uses.

See [The View Language](../guide/view-language.md#style) for the rule syntax and [Themes](../themes/index.md) for colours, type and shape.

## Actions

- **Buttons**: [`Button`](buttons/button.md)
- **Icon buttons**: [`IconButton`](icon-buttons/icon-button.md)
- **Floating action buttons**: [`Fab`](fabs/fab.md)

## Communication

- **Badges**: [`Badge`](badges/badge.md)
- **Snackbars**: [`Snackbar`](snackbars/snackbar.md)

## Containment

- **Cards**: [`Card`](cards/card.md)
- **Dialogs**: [`Dialog`](dialogs/dialog.md)
- **Dividers**: [`Divider`](dividers/divider.md)
- **Lists**: [`ListItem`](lists/list-item.md)
- **Side sheets**: [`SideSheet`](side-sheets/side-sheet.md), [`SideSheetModal`](side-sheets/side-sheet-modal.md), [`SideSheetPanel`](side-sheets/side-sheet-panel.md)
- **Accordions**: [`Accordion`](accordions/accordion.md)
- **Trees**: [`TreeNode`](trees/tree-node.md)

## Navigation

- **Navigation rail**: [`NavigationRail`](navigation-rail/navigation-rail.md), [`NavigationRailItem`](navigation-rail/navigation-rail-item.md)
- **Navigation drawer**: [`NavigationDrawer`](navigation-drawer/navigation-drawer.md), [`NavigationDrawerItem`](navigation-drawer/navigation-drawer-item.md), [`NavigationDrawerModal`](navigation-drawer/navigation-drawer-modal.md), [`NavigationDrawerPanel`](navigation-drawer/navigation-drawer-panel.md), [`NavigationDrawerScreens`](navigation-drawer/navigation-drawer-screens.md)
- **Top app bar**: [`TopAppBar`](top-app-bar/top-app-bar.md)
- **Menus**: [`Menu`](menus/menu.md), [`MenuItem`](menus/menu-item.md)
- **Search**: [`SearchBar`](search/search-bar.md), [`SearchView`](search/search-view.md)
- **Toolbars**: [`Toolbar`](toolbars/toolbar.md)

## Selection and input

- **Chips**: [`Chip`](chips/chip.md)
- **Text fields**: [`TextField`](text-fields/text-field.md)
- **Spin box**: [`SpinBoxField`](spin-boxes/spin-box-field.md)
- **Date picker**: [`DatePicker`](date-pickers/date-picker.md), [`DatePickerDay`](date-pickers/date-picker-day.md)
- **Time picker**: [`TimePicker`](time-pickers/time-picker.md), [`PeriodSelector`](time-pickers/period-selector.md)
- **Time input**: [`TimeInput`](time-input/time-input.md)

## Content

- **Video**: [`VideoPlayer`](video/video-player.md)
- **Carousel**: [`Carousel`](carousel/carousel.md)
- **Pagination**: [`Pagination`](pagination/pagination.md)

## Beyond MD3

- **Status bar**: [`StatusBar`](status-bar/status-bar.md)
