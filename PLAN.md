# PLAN — M7: Bootstrap Documentation Infrastructure

*(First real entry in this file — `tesserae` didn't have a `PLAN.md`
before this milestone. Adopts `tre`'s own already-corrected convention
directly: overwritten per phase, `BUILD_TRACKER.md` is the durable
record, no per-step archiving.)*

## Goal
Give `tesserae` the same real documentation infrastructure `tre`
already has -- a `BUILD_TRACKER.md`, a real MkDocs site, and
`PLAN.md`/`LOG.md` -- before the real widget-catalog/YAML-macro work
(Milestones 8+) starts, so that work has a real place to be tracked
from the beginning. User's own direct instruction: "Tesserae as a new
project and git/github repo should have its own documentation to
include build tracker and MkDocs, along with everything else. If it is
Tesserae scoped it goes in the Tesserae project."

## Design (1 milestone, 3 phases)
1. `BUILD_TRACKER.md`, seeded with real history (Milestones 1-6,
   reconstructed honestly from the 6 real commits already shipped).
2. MkDocs site (`docs/`, `mkdocs.yml`, `docs.yml` workflow).
3. `PLAN.md`/`LOG.md` (this file and its sibling).

## Status

**Complete, all three phases.**

`BUILD_TRACKER.md` created at the repo root: Top Metrics table,
Known/Fixed gaps, Milestones 1-6 each with a real writeup drawn
directly from their own commit messages, Milestone 7 (this one) tracked
live. `tools/generate_tracker_artifact.py` copied verbatim from `tre`
(confirmed genuinely project-agnostic -- ran clean against this repo's
own `BUILD_TRACKER.md` with zero changes needed: 7 milestones, 13
phases, 29 items, 3 known gaps parsed correctly). Tracker artifact
published as a new Claude artifact (title "Tesserae Build Tracker").

MkDocs site: `mkdocs.yml` (same real Material theme/nav shape `tre`
uses, scoped to Tesserae's own real surface: `App`, `instantiate`,
`Repeater`, cross-linking to `tre`'s own published docs for anything
merely re-exported rather than re-documenting `Signal`/`Computed`/
`Effect` a second time) plus 11 real content pages (`index.md`,
`installation.md`, `getting-started.md`, 5 guide pages, 4 API reference
pages, `architecture.md`). `mkdocs build --strict` clean, 0 warnings.
`.github/workflows/docs.yml` added, mirroring `tre`'s own real
workflow -- real, stated manual step before its first run will
actually deploy: GitHub Pages needs "Build and deployment: GitHub
Actions" enabled once in this repo's own Settings, confirmed not yet
enabled (`gh api repos/mindderivative/tesserae/pages` returned 404).
`.gitignore` updated (`/site/`, the generated tracker artifact HTML).

`PLAN.md`/`LOG.md` (this pair) adopted.

Committing locally now; push deferred pending explicit user
confirmation, mirroring `tre`'s own standing policy applied here too.

Next: the real widget/component catalog (Milestone 8, `tre`-side theme
API first) and the YAML component macro-expansion layer (Milestone 9),
per the approved plan.
