---
name: research-mode
description: 'Use when the user says the project is in "optimization, performance, efficiency, feature, and research mode" (or asks to research, baseline, audit or find better ways to do something in the framework). Sets the five goals and a measure-first method: baseline and inventory, ranked findings as Backlog issues, nothing built until the user approves.'
---

# Research mode

The user's own definition (2026-10-03, given in the tre project, which shares the maintainer), verbatim:

> I think we are in optimization, performance, efficiency, feature, and research mode.
>
> * Optimization: Looking for ways to optimize the code without the lose of functionality and features.
> * Performance: Looking for ways to increase performance ensuring a smooth and enjoyable experience while providing extensive functionality, expected and new features, with crisp and clean rendering.
> * Efficiency: Ensuring and expanding the efficiency of functionality and feature that will run great on all forms of desktop hardware.
> * Feature: looking for ways to expand the capabilities with expected and new features.
> * Research: Performing research to achieve optimization, performance, efficiency, and feature goals. This means identifying our current functionality and features, researching what would be expected, exploring new ideas and features that could be added, and working out ways to optimize the code, increase performance, expand efficiency, and implement/expand new and old features. If there is a better way to accomplish something, then we should be looking at it.

(The Feature line is shortened from "of the engine ... for a UI rendering engine"; the rest is unchanged.) Read the goals as one test for every idea: lose no functionality, keep rendering smooth and crisp, run well on all desktop hardware, widen what can be done. "If there is a better way, look at it" is a standing instruction: question the approach, not only the bugs.

## Method (worked in tre, Oct 2026)

Measure and survey first. Change no code until the user picks from ranked findings.

1. **Baseline.** Measure before optimizing: startup, build time of a view, frame cost for a static window, a large tree, scrolling, many text nodes, idle CPU. Reuse `tools/window_perf.py` and `window-perf/`. Say which hardware it ran on and which it did not.
2. **Inventory and gaps.** List what exists, checked against the source and `COMPONENT_LIST.md`, not recalled. Compare with what a UI framework is expected to have. Mark each gap with evidence; say when something was confirmed from code only.
3. **Test guesses against numbers**, by measuring or by a throwaway experiment that is reverted. Report what it showed and that it was reverted.
4. **Findings become Backlog issues**, one per idea (`python3 tools/board.py create TITLE --body ... --dry-run` first; issues are public), each with evidence, expected gain, effort and risk, ranked. Put the write-up in `design/` and link it from the issues.
5. **Report honestly:** headline numbers, the limits (one machine, one GPU, one display server), anything extra touched.
6. **Then wait.** Nothing leaves Backlog until the user approves it.

A second sweep is part of the mode: look for expected features the first inventory missed.

## Do not

- Optimize by intuition: every claimed gain needs a before and after.
- Trade a feature or visual quality for speed; offer the fast path as opt-in when output would differ.
- Push, merge or tag without the user's separate instruction.
