---
name: psp-remix-project
description: Orchestrates a PSP game remix project end to end — decompile one or more UMD ISOs, plan mixes (cars, courses, music, modes), translate, recompile and test. Use when the user says "remix", "mix these games", "decompile and recompile", "start a PSP project", "add X from game A to game B", or asks what to do next on an existing remix.
---

# PSP Remix Project

Coordinate the plugin's agents through a fixed pipeline. Run autonomously between milestones; stop only at the gates marked **CHECKPOINT** (the user tests in PPSSPP) unless the user asked for maximum autonomy, in which case batch the checkpoints into one test request at the end of a milestone.

## Project layout (create on first run)

```
<project>/
  PROJECT.md            # goals, games, milestone status, decisions (keep current)
  sources/              # user's ISOs or extracted folders (read-only)
  work/<game>/          # decompiler output: iso/, unpacked/, catalog.json, FORMATS.md
  work/mix/<asset>/     # asset-mixer output, PLAN.md per asset
  work/translation/     # glossary.csv, strings_*.json, report.md
  work/<game>/patches/  # code patches (.asm / .json), SPACE.md
  build/                # recompiler output: changed files, OUT.iso, remix.xdelta, BUILD_REPORT.md
```

All tools: `${CLAUDE_PLUGIN_ROOT}/scripts/` (see `references/tools.md`).

## Pipeline

1. **Fingerprint & decompile** every source game → `psp-decompiler` agent. Read `psp-game-notes` for known titles.
2. **Assess** each requested feature: classify as data-only / data + small code / new code. Write the plan to PROJECT.md with a difficulty and the riskiest unknown for each.
3. **Unknown formats** → `psp-format-reverser` until each needed container round-trips.
4. **Mix** → `psp-asset-mixer` (one asset at a time; slot replacement first).
5. **Code** → `psp-code-patcher` for new slots, modes, tables, text rendering.
6. **Translate** → `psp-translator` (can run in parallel with 4–5; it touches different files).
7. **Build** → `psp-recompiler`. **CHECKPOINT**: `psp-qa-tester` plan + user test.
8. Update PROJECT.md: what shipped in the build, what is next.

## Milestone template for a "new car + new challenge mode" request
- M1 Proof of pipeline: one translated or retextured file in a rebuilt ISO boots in PPSSPP.
- M2 Car in a replaced slot: model + textures load in car select and race.
- M3 Car data: tuning stages, physics feel, name/text, engine sound mapping.
- M4 Real new slot (code): car table + relocations + save-data impact checked.
- M5 Mode: clone the closest existing mode (e.g. Bunta challenge) and retarget rival/car/courses; then new menu entry art.
- M6 New course: reference geometry from source game, rebuilt in target's block format, table entry, AI line.
- M7 Music: replace → add songs → custom song loader/player UI.

## Rules
- Never write to the user's original ISO or extracted originals.
- Keep builds reproducible: every change is a file in `work/` plus a manifest line; the recompiler can rebuild from scratch.
- Distribute only as xdelta patches, and never package a third publisher's assets into a distributable patch; mixed builds are for the user's own discs.
- Be honest about difficulty: report what is proven (round-tripped, seen in game) versus assumed.
