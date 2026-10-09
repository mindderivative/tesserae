# Request to tre: more accessibility states

*Drafted for Tesserae 0.5.0 (#232). Sent 2026-10-08 as mindderivative/tre#160.*

## What Tesserae needs

The states a screen reader hears about a control, which Material 3's components set: a toggle button that is **pressed**, a field that is **invalid** with a **description** of why (and what **describes** it), a button that **controls** a panel, the **current** page or step, a progress value with a **text** form, and a region that is **busy**.

## What exists today (tre 0.5.4)

Checked with `Node.get` on a `box`. Present: `role`, `label`, `live`, `level`, `a11y_hidden`, `expanded`, `selected`, `checked`, `value_min`, `value_max`, `value_step`, `tab_index`. Missing (each raises "unknown node property"): `pressed`, `invalid`, `description`, `describedby`, `controls`, `current`, `value_now`, `value_text`, `busy`. There is no `a11y_action` property either, though the `a11y_action` event exists.

## The ask

Node properties, applying to any node, mapped to the platform accessibility trees (AccessKit has them):

| Property | Type | Meaning |
| --- | --- | --- |
| `pressed` | `True`, `False` or `"mixed"` (or `None`) | a toggle button's state |
| `invalid` | bool | the value is not acceptable |
| `description` | text | a longer description than `label` |
| `describedby`, `controls` | a node, or a list of nodes | relations to other nodes |
| `current` | `"page"`, `"step"`, `"location"`, `"date"`, `"time"` or `True` | the current item in a set |
| `value_now`, `value_text` | number, text | the value of a range, and how to say it |
| `busy` | bool | the node is updating |

Each takes `None` to clear, as `expanded` does.

## How Tesserae uses it

The `a11y:` fields of a node (`pressed`, `invalid`, `description`, `describedby`, `controls`, `current`, `value_now`, `value_text`, `busy`), bindable like the ones already there; the components set them (Switch, Checkbox, TextField error, Tabs, Progress). Until tre has them they are accepted by the language and ignored by the renderer, said once by name. Tesserae's own `invalid` workaround for a field is the error text in its `label`.

## Questions for tre

- Relations: are they by node, or by an id the framework gives? Nodes are what Tesserae holds.
- Is `separator` going to be a `role`? Tesserae's Divider is `a11y_hidden` only because there is none.
