---
name: psp-course-porting
description: Method for building a new race course in a PSP racing game from another game's course or from scratch — reading course geometry and streaming blocks, collision and AI line data, rebuilding in the target's format, and registering it in course/mode tables. Use for requests like "add a Wangan-style highway course to Initial D".
---

# Course porting

## Target structure (Initial D Street Stage, per course folder `data/course/<name>/`)
- `<name>_{day,night,rain}_data.gz`, `_start_data1.gz`, `_start_data2.gz` — per-condition course packages.
- Variant folders (`df1`, `df1_rain`, `df2` …: direction/condition) containing:
  - `k_<v>_aNN.gmo` (~30 visual sections, 40–460 KB each)
  - `k_<v>_blk_NN_0.bin` / `_1.bin` (~34 streamed blocks — likely geometry/collision LODs per section)
  - `k_<v>_sub_NN.bin` (~30 sub-data files, likely per-section collision/path/props)
- Course id strings in BOOT.BIN (MYOGI, USUI, AKAGI, AKINA, HAPPOU, IROHA, SHOU…, TSUCHISAKA) and course select layouts in `data/select/`, `data/bunta/`, `data/timeattack/`.

## Source structure (Wangan Midnight Portable)
- BUILD.DAT entries 1813–8343: repeating groups of one texture pack followed by many GMO chunks — streamed highway sections (C1 loop, Wangan line, Yokohane, etc.). Use them as reference geometry and texture source.

## Plan (do in order)
1. Fully decode one target course: map `blk`/`sub` formats (psp-format-reverser), confirm which file holds collision triangles, road spline / AI line, checkpoints, start grid, camera data.
2. Prove a **content swap**: edit one GMO section of an existing course (e.g. Akina) and see it in game. Then swap a collision block.
3. Build the new course as a **replacement** for a short/rarely-used course (e.g. Happogahara has only 3 files) so all tables already exist.
4. Geometry: assemble WMP highway chunks into a continuous route (or model a new one inspired by it: long straights, wide multi-lane, joints, tunnels, sodium lights), re-section to the target's section count and size limits, re-texture to Initial D's palette/style, generate collision and AI line from the road mesh centreline.
5. Only then add a true new course id (psp-code-patcher): course table, select screen art, time-attack records, Bunta/Devil Z challenge lists, save data.

## Highway-specific design notes
- Initial D physics/AI are tuned for touge: expect AI to need a new racing line and speed caps; long straights expose top-speed limits — check gear ratios/rev limiter on fast cars.
- Keep draw distance budgets: highway sight lines are long; use fog and section LODs like the night touge courses.

## Adding a course (checklist from Initial D Wangan / Akina Snow, m17–m31)
- Distinguish course index (0..8) from course model id (crsmdl = course*2+dir, 0..17 + variants); factory jump tables bound crsmdl (0–15 stock). Many tables are indexed by crsmdl/2 — never let an out-of-range id reach them; prefer reusing an existing course id + a flag that switches files.
- Files: copy the course set under new names and rewrite only the DISC paths (archive/bundle names via lba.dat); inner XBB entry names stay stock (lookups are by basename). New disc files need ISO directory records + lba.dat (iso_tool add with dir-enlarge + post-verify).
- Records/save: find spare record slots (e.g. unused day slots of a night-only course) before changing the save layout.
- Menus: carousel item counts come from a count method (not the art); strip tiles, headers, photo/map anims, race intro name, area-clear screen each need the new entry.
- Geometry rules: keep all stock GMO parts/order/quantisation; vertex colours are 16-bit 5551 with the opacity bit (0xC631 = stock grey); renamed texture slots are ignored — reuse existing slot names; tessellate near the driving line (~3 m) for PSP near-plane rejection; the deck must cover the whole path range the camera can see.
- Collision: side-layer cells must cover every walkable triangle (deck + wall bands) or the car enters a lost-ground state; walls flat-banded, no folding on inside of tight bends; course ends = asphalt run-off + bevelled wall cap; ray tests along both AI lines (0 misses).
- Weather variants (snow): reuse an existing weather path (WET) and switch files + physics rows by flag; skip expensive per-weather effects when not needed.
