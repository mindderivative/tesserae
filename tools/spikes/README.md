# Spikes

Throwaway prototypes from M34 (the building-block program's design gate),
kept as references for the milestones that build the real thing. They
aren't product code, aren't imported by Tesserae, and aren't tested.

| Script | Question | Answer (2026-09-25, `tre` 0.3.4) | Feeds |
|---|---|---|---|
| `cascade_cost.py` | What do Tesserae's own cascade, role colours and bindings cost in Python? | 2,000 boxes + 2,000 texts, a 4-rule stylesheet, 500 bound texts: build 20.7 ms vs `tre` `View` 11.0 ms; theme switch 2.8 vs 3.1 ms; one `Signal.set` reaching 500 nodes 0.7 vs 0.5 ms. Half the build is the naive cascade scanning every rule per node; index rules by kind/class/id | M36, M37 |
| `color_parity.py` | Does `materialyoucolor` reproduce `tre`'s MD3 schemes? | 784/784 with `spec_version="2021"` and tone 10 for the four light `on_*_container` roles | M38 |
| `checkbox_on_primitives.py` | Do the building blocks suffice for an MD3 control? | Yes: a full checkbox in ~70 lines — state layers, ripple, keyboard focus ring, `trim_end` check animation, a11y role/label/checked, Space/Enter — 12/12 headless checks | M39, M40 |

Run with `.venv/bin/python tools/spikes/<script>.py` (the colour one
needs `materialyoucolor` installed).
