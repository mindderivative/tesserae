# LOG — M7: Bootstrap Documentation Infrastructure

- User-directed, as part of shifting real development focus to
  Tesserae: "Tesserae as a new project and git/github repo should have
  its own documentation to include build tracker and MkDocs, along
  with everything else. If it is Tesserae scoped it goes in the
  Tesserae project." A direct correction of an earlier draft plan that
  had folded Tesserae-scoped tracking into `tre`'s own
  `BUILD_TRACKER.md`.

## What shipped

1. `BUILD_TRACKER.md` created at the repo root -- Top Metrics table,
   Known/Fixed gaps, and Milestones 1-6 each written as real, honest,
   after-the-fact history reconstructed directly from the 6 real
   commits already shipped (`fdd523b` initial `App`+counter slice
   through `2c60390`'s `flex_direction` sync), not presented as if
   this tracker had been running from day one. Milestone 7 (this one)
   tracked live as it happened.
2. `tools/generate_tracker_artifact.py` copied verbatim from `tre` --
   its own header states it's project-agnostic, meant to be copied
   into any repo with a `BUILD_TRACKER.md` at its root; ran clean
   against this repo's own file with zero script changes needed (7
   milestones, 13 phases, 29 items, 3 known gaps parsed correctly).
   Tracker artifact published fresh (title "Tesserae Build Tracker",
   favicon 🧩).
3. A real MkDocs site: `mkdocs.yml` (the same Material theme/nav shape
   `tre` uses) plus 11 content pages -- `index.md`, `installation.md`,
   `getting-started.md`, five guide pages (`apps-and-screens.md`,
   `components.md`, `repeater.md`, `reactivity.md`,
   `naming-convention.md`), four API reference pages (`api/index.md`,
   `api/app.md`, `api/instantiate.md`, `api/repeater.md`), and
   `architecture.md`. Scoped to what Tesserae itself provides --
   `Signal`/`View`/`ViewModel`/`Component`/`Computed`/`Effect`/`batch`/
   `untrack` are `tre`'s own classes, re-exported unmodified, so the
   docs link to `tre`'s own published reference for those instead of
   re-documenting them a second time.
4. `.github/workflows/docs.yml` added, mirroring `tre`'s own real
   workflow closely -- simpler here since this repo's own docs never
   import `tesserae`/`tre` at all (pure prose + links), so no Rust
   toolchain or editable install step is needed, unlike `tre`'s own
   version.
5. `.gitignore` updated: `/site/` (the `mkdocs build` output),
   `/tools/build-tracker-artifact.generated.html`.
6. `PLAN.md`/`LOG.md` (this pair) adopted, matching `tre`'s own
   already-corrected convention (overwritten per phase,
   `BUILD_TRACKER.md` is the durable record).
- Verification: `mkdocs build --strict` clean, 0 warnings. The new
  `docs.yml` workflow YAML validated via `yaml.safe_load` (job graph
  parses correctly: `build`, `deploy`). `generate_tracker_artifact.py`
  run directly, confirmed correct parse counts, no script edits
  needed.
- **Real, stated manual step, not something this milestone could do
  for itself:** GitHub Pages needs "Build and deployment: GitHub
  Actions" enabled once in this repo's own Settings > Pages before the
  new `docs.yml` workflow's `deploy` job will actually succeed --
  confirmed not yet enabled (`gh api repos/mindderivative/tesserae/pages`
  returned a real 404 at the time this workflow was added), named
  directly in the workflow's own header comment rather than silently
  assumed to already be on.

## Status

**M7 is complete, all three phases.** Tesserae now has the same real
documentation infrastructure `tre` already has, in its own repo, as
its own scope -- ready for the real widget-catalog and YAML
macro-expansion milestones about to start to be tracked here from the
beginning. Committing locally now; push deferred pending explicit user
confirmation.

Next: `tre`-side Part 1 (the theme-resolution API + related small
additions the widget catalog depends on), then Tesserae's own
Milestone 8 (the widget catalog) and Milestone 9 (the YAML
macro-expansion layer), per the approved plan.
