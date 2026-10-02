# Component Stylesheets

Every built-in component keeps its look in a stylesheet, `<Name>_Stylesheet.yaml`, beside its structure, `<Name>_Component.yaml`. Each page here shows one stylesheet, how it is tied to its component, and what it makes.

## How they work

A stylesheet is a list of rules. Each names a part of the component by its `id` and gives that part's `style`:

```yaml
styles:
  - id: root
    style: {background: primary, width: "{{ width }}"}
  - id: label
    style: {foreground: on_primary}
```

- A value in `{{ }}` is one of the component's parameters, filled in where the component is used.
- A value can be `{if: "{{ selected }}", then: primary, else: on_surface}`, chosen by a parameter.
- A part's own `style:` in the fragment is kept, and wins over its stylesheet.
- Your own `<Name>_Stylesheet.yaml` next to your views goes over the built-in one, field by field. A fragment of your own with the same name as a built-in one replaces it, and the built-in stylesheet with it.
- Hot reload watches the stylesheets a view uses.

This is a different thing from a view's stylesheet (`App(stylesheet=)`), whose rules match many nodes by `kind`, `classes` or `id`: see [Themes](../themes/index.md). A component's stylesheet styles one component's parts.

## Actions

- **Buttons**: [`ButtonFilled`](buttons/button-filled.md), [`ButtonFilledTonal`](buttons/button-filled-tonal.md), [`ButtonElevated`](buttons/button-elevated.md), [`ButtonOutlined`](buttons/button-outlined.md), [`ButtonText`](buttons/button-text.md)
- **Button groups**: [`ButtonGroup`](button-groups/button-group.md)
- **Split buttons**: [`SplitButtonFilled`](split-buttons/split-button-filled.md), [`SplitButtonFilledTonal`](split-buttons/split-button-filled-tonal.md), [`SplitButtonElevated`](split-buttons/split-button-elevated.md), [`SplitButtonOutlined`](split-buttons/split-button-outlined.md), [`SplitButtonText`](split-buttons/split-button-text.md)
- **Icon buttons**: [`IconButtonStandard`](icon-buttons/icon-button-standard.md), [`IconButtonFilled`](icon-buttons/icon-button-filled.md), [`IconButtonFilledTonal`](icon-buttons/icon-button-filled-tonal.md), [`IconButtonOutlined`](icon-buttons/icon-button-outlined.md)
- **Floating action buttons**: [`FabPrimary`](fabs/fab-primary.md), [`FabSecondary`](fabs/fab-secondary.md), [`FabTertiary`](fabs/fab-tertiary.md), [`FabSurface`](fabs/fab-surface.md)
- **Extended FABs**: [`ExtendedFabPrimary`](extended-fabs/extended-fab-primary.md), [`ExtendedFabSecondary`](extended-fabs/extended-fab-secondary.md), [`ExtendedFabTertiary`](extended-fabs/extended-fab-tertiary.md), [`ExtendedFabSurface`](extended-fabs/extended-fab-surface.md)

## Communication

- **Badges**: [`BadgeDot`](badges/badge-dot.md), [`BadgeLabeled`](badges/badge-labeled.md)
- **Progress indicators**: [`LinearProgress`](progress-indicators/linear-progress.md), [`CircularProgress`](progress-indicators/circular-progress.md), [`LoadingIndicator`](progress-indicators/loading-indicator.md)
- **Snackbars**: [`Snackbar`](snackbars/snackbar.md)
- **Tooltips**: [`Tooltip`](tooltips/tooltip.md)

## Containment

- **Cards**: [`CardElevated`](cards/card-elevated.md), [`CardFilled`](cards/card-filled.md), [`CardOutlined`](cards/card-outlined.md)
- **Dialogs**: [`Dialog`](dialogs/dialog.md)
- **Dividers**: [`Divider`](dividers/divider.md)
- **Lists**: [`ListItem`](lists/list-item.md)
- **Side sheets**: [`SideSheetStandard`](side-sheets/side-sheet-standard.md), [`SideSheetModal`](side-sheets/side-sheet-modal.md)
- **Accordions**: [`AccordionHeader`](accordions/accordion-header.md)
- **Trees**: [`TreeNodeBranch`](trees/tree-node-branch.md), [`TreeNodeLeaf`](trees/tree-node-leaf.md)

## Navigation

- **Navigation rail**: [`NavigationRail`](navigation-rail/navigation-rail.md), [`NavigationRailItem`](navigation-rail/navigation-rail-item.md)
- **Navigation drawer**: [`NavigationDrawer`](navigation-drawer/navigation-drawer.md), [`NavigationDrawerItem`](navigation-drawer/navigation-drawer-item.md)
- **Top app bar**: [`TopAppBar`](top-app-bar/top-app-bar.md)
- **Tabs**: [`Tabs`](tabs/tabs.md), [`TabsItem`](tabs/tabs-item.md)
- **Menus**: [`Menu`](menus/menu.md), [`MenuItem`](menus/menu-item.md)
- **Search**: [`SearchBar`](search/search-bar.md), [`SearchView`](search/search-view.md)
- **Toolbars**: [`ToolbarDocked`](toolbars/toolbar-docked.md), [`ToolbarFloating`](toolbars/toolbar-floating.md)
- **Links**: [`Link`](links/link.md)

## Selection and input

- **Checkbox**: [`Checkbox`](checkboxes/checkbox.md)
- **Radio button**: [`RadioButton`](radio-buttons/radio-button.md)
- **Switch**: [`Switch`](switches/switch.md)
- **Slider**: [`Slider`](sliders/slider.md)
- **Chips**: [`ChipAssist`](chips/chip-assist.md), [`ChipFilter`](chips/chip-filter.md), [`ChipFilterSelected`](chips/chip-filter-selected.md), [`ChipInput`](chips/chip-input.md), [`ChipSuggestion`](chips/chip-suggestion.md)
- **Date picker**: [`DatePickerDay`](date-pickers/date-picker-day.md), [`DatePickerDayToday`](date-pickers/date-picker-day-today.md), [`DatePickerDaySelected`](date-pickers/date-picker-day-selected.md), [`DatePickerDayOutsideMonth`](date-pickers/date-picker-day-outside-month.md)
- **Time picker**: [`TimePickerDial`](time-pickers/time-picker-dial.md), [`PeriodSelectorAM`](time-pickers/period-selector-am.md), [`PeriodSelectorPM`](time-pickers/period-selector-pm.md)

## Content

- **Text**: [`Text`](text/text.md)
- **Images**: [`Image`](images/image.md)
- **Video**: [`Video`](video/video.md)

## Beyond MD3

- **Status bar**: [`StatusBar`](status-bar/status-bar.md)
- **Node graph**: [`NodeGraph`](node-graph/node-graph.md)
