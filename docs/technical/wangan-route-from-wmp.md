# M-HW — Wangan on a real WMP expressway route (multi-session status)

## Round 1 (2026-10-31, offline, no PPSSPP): research, route choice, first complete file set

### Chosen stretch
WMP Shuto lane ribbons **3526 + 3528 + 3530**: one carriageway, **6050 m**, point-to-point (Happogahara is 5976 m).
- It runs through WMP chunk runs 2844 → 2884 → 2926 (plus the edges of 2803 and 2971 for scenery).
- In order: a sweeping N→S run (~2.2 km, gentle S-bends), then a JCT corner with ramps and overpasses at ~2.9 km, then a ~3 km near-straight to the SW.
- Smoothed minimum radius is 204 m. Height is 950–975 m with grades ≤ 2.9 % (the carriageway level is tracked through the JCT; limit 4 %).
- Why this stretch: it has the longest straights in the decoded network, a real JCT, 3-lane width (ribbon 10.4 m, 17.9 m at the straight), and the length matches the stock 2080-point path.
- Research outputs:

| File | Contents |
|---|---|
| `fnig_runs.json` | 126 FNIG placements, 43 unique |
| `runs_topdown.png` | The 18 chunk runs with their own FNIG (two C1-style loops) |
| `ribbons_over_runs.png` | Lane ribbons (entries 3470–3634) over the runs |
| `ribbons.py` | Ribbon decoder: (left, right) vertex pairs, followed by an index list |

### Pipeline (`tools/`, copies of the M24c/M21 tools re-pointed at `m35/hw`)
- `hwline.py`: ribbons → 2080-point centre line, transformed to course space: x−6325, z+6523, y+944.2. The route centre sits at the sky-dome origin.
  - `s_vh_path_l/_r` edges at ±5 m.
  - AI lines `PATH_vhi_0` / `PATH_vho_0`: 606 points at 10 m, zero-terminated like stock (stock uses 574 of 1000). Racing line = centre ±3.5 m toward the inside of bends.
- `tools/width.py`: the same width/frame model on the new line. The route has no close legs, so the deck is the full 14 m.
- `tools/hw_build.py` (from m24_build): WMP chunks at their **true relative positions** (rigid transform, no bending).
  - Chunks are picked per section by FNIG rect overlap; each WMP triangle lands in exactly one section.
  - Our 14 m deck, barriers, ground skirt, lamps, gantries, towers and lane strips follow the new line.
  - **New per-section quantisation box** (uniform 0x8015 pos offset/scale) and model bbox; LOD models (vh_b/vh_c) too.
  - Gates are moved to the same path index on the new line.
  - Spectators sunk; lamp glows on lamp heads.
  - New path/edge/AI files written into the night data; sky dome scaled ×1.35 (the route reaches 2.49 km from the origin).
- `tools/colli_hw.py` + `fixcells_hw.py` (colli21 = M21 v6: flat wall bands, aprons/end caps, full aux cells): 6154 tris / 1258 cells per direction, nz 135 KB (stock 306 KB).

### Results
- Every file is exact stock size: 32 sections, 64 blk, LOD subs, start archives, night data.
- 31/32 sections carry full scenery. a28 (stock 90 KB) has no towers/lamps.
- Triangles: **121k vs stock 194k (0.62×)**, worst section 0.77×.
- Checks:
  - `m6_deckcheck`: 27,459 samples, 0 drops, deck vs path height ≤ 0.06 m. The 12 "off-road" hits are the pre-start run-off wall at ±9–11 m, as in earlier builds.
  - `m7_aicheck`: both AI lines on road and inside aux cells (0 misses, both directions).
  - `simcheck` (game ground-lookup model): 18,462 samples all ok.
  - `m7_wallcheck` reports the M20 flat wall bands as "low" (expected with the old metric).
- Previews:
  - `topdown_overlay.png`: centre line, both AI lines, section starts, moved gates.
  - `preview_drivercam.png`: driver camera at s = 120 / 1500 / 2950 (JCT ramps) / 4600 (straight), plus return at 5800 / 3300.
- **Manifest:** `manifest_hw.json` replaces the 131 Wangan disc ADD files of build 31 (wg_* / wangan_*), whose sources were m24c. Happogahara files and BOOT are untouched (BOOT34W).
- **Test autopilot:** `m35/ap/BOOT35AP.BIN` (BOOT34W + autopilot at 0x577b30–0x57f204) with the new line embedded. RW selects the Wangan line; Happogahara and Akina keep theirs. The unicorn sim drives the whole new route at up to 224 km/h in ~105 s. See `m35/ap/AP_README.md`.

### Risks / not done (next rounds)
1. **Quantisation boxes moved** (first time). If the engine culls or streams sections by stock positions, sections could vanish. The model and part bboxes are consistent. *PPSSPP first check: does every section draw along the route?*
2. **Checkpoint/start/finish triggers** are assumed to be path-index based. Gates were moved by index (start ≈ idx 63, checks 561/1016/1498, finish 2022). If triggers are world-space tables in the BOOT course descriptor, checkpoints won't fire.
3. **Intro/replay camera paths** (`/driveA/env/s_vh1_path_env0/1.bin`, shared disc files) and **minimap/navi/lecmap/course-select map** still show Happogahara. They need Wangan copies + the c2p1 path switch, or a navi rebuild from the new line.
4. **Draw distance / fog:** straights are 2–3 km long. Sky dome scaled; fog curve not tuned.
5. **Rivals:** generated AI lines (centre + inside offset) are untuned at 200+ km/h.
6. **Visual:** WMP geometry uses ID stock textures by category (as in M17–M24). The JCT ramps and overpasses are kept as scenery (walled off). Our 14 m deck is wider than the 10.4 m WMP carriageway, so the barriers stand ~1.8 m outside the WMP lane edge.

### Rebuild
```
python3 hwline.py
cd tools && python3 colli_hw.py && python3 fixcells_hw.py && BUILD_DIR=vis M_SECTIONS=all python3 hw_build.py
cd .. && python3 tools/m6_deckcheck.py colli_out/s_vh_colli_0.bin && python3 tools/m7_aicheck.py colli_out/s_vh_colli_0.bin && python3 shots_hw.py && python3 topdown_hw.py
```

## Round 2 (2026-10-31): build35t QA fix — nothing drew, WRONG WAY, falling
### Cause (static trace of BOOT34W)
- The **start grid is a BOOT table**, not course data. The course object at 0x73e0c / 0x73e5c calls:
  - `GetStartPos 0x10a244(out, course, dir, car)`, table 0x1e5b70: 9 courses × 2 dirs × 2 cars × xyz;
  - `GetStartDir 0x10a2e0`, table 0x1e5d20: unit headings.
- So Wangan (course 4) spawned at Happogahara's grid (−1586, 1017, 315), 1.65 km from the new route, over nothing. It fell (QA: y = 196 at the countdown), WRONG WAY showed, and no streamed section was ever near → no `wg_blk` opened.
- **Section selection is by path index, not world position:**
  - `0x73b30` compares the car's path progress with a per-course boundary list (`0x10a37c[course]` → 0x1e6058 for course 4: 77, 164, …, 2070, −1).
  - The streamer `0x131fe4` / `0x132410` keeps sections cur±1 and ±2 and builds `%s%s_blk_%02d_%d.bin` at 0x130b00.
  - So the new world positions and bounding boxes are fine once the car is on the line.

### Fix
- **`boot/m35_grid_boot.py` → `boot/BOOT35G.BIN`** (release; BOOT34W + region 0x577b30–0x577c9f, md5 8653d41a…).
  - The two `jal` sites now go to HPOS / HDIR, which return Wangan rows when course == 4 and RW.
  - Wangan rows: outbound path idx 64 at lateral ±1.87 m with heading = tangent; return idx 2022 with heading = −tangent. These are the same indices and offsets as Happogahara's stock rows.
  - Everything else (Happogahara, other courses) tail-jumps to the stock functions.
  - `verify_grid.py`: ALL OK (Wangan rows for course 4 + RW; stock Happogahara rows with RW = 0; course 3 untouched). Relocation sim OK; only the 2 new `j` get relocs.
- **Sections rebuilt on the ENGINE boundaries** (`engine_sections.json`; `m5_ranges.json` now = engine section k ± 8 points). Before, sections 11–13 (a11 / a12b / a12c) were offset by one section versus the engine (inherited from the stock-geometry ranges).
- **`streamer_sim.py`** (model of 0x73b30 + streamer window), every 5 m both directions (2422 samples, 63 section changes):
  - the car is inside the current section's model bbox;
  - road is under the car in the current section;
  - road is drawn ≥150 m ahead within the loaded k±2 set.
  - Result: **0 fails**. Spawns: outbound idx 64 → section 0, return idx 2022 → section 31; both sections are in their start archives, with road under the spawn.
- **Autopilot (QA):** `../ap/BOOT35GAP.BIN` = BOOT35G + autopilot at 0x577ca0–0x57f304. APB cheat is 0x0057C650 and the speed byte 0x0057C69C (`ULJM05093_autopilot_b35g.ini`). Relocation sim covers all 8 sites.
- **Manifest:** `manifest_hw.json` keeps the same 131 add_replace keys, with boot = BOOT35G.

### Still open
- Intro/replay camera paths (`/driveA/env/s_vh1_path_env0/1`) are world-space Happogahara data, not yet located.
- Course-select / route-select map and the minimap art still show Happogahara's shape.
- The TA record slot still holds the old-route time (8'27"). It needs a save edit or a one-time clear hook (not done).
- Rival AI pace is still untuned.

## Round 3 (2026-10-31): r2 QA: road vanished at ~10 s, WRONG WAY, no `wg_blk` opened
### Cause: progress index stuck at the start
- **Progress = quad containment.** The race progress index comes from the path object (class vtable 0x24eb78, ctor 0x10aa48). It loads `s_vh_path.bin`, `_l.bin` and `_r.bin`; update is vfunc 0xc = 0x10ac58.
  - The car is "in" segment i when it lies inside quad L[i], R[i], R[i+1], L[i+1].
  - Edge test 0x10b768 / 0x10b738: n = (e_z, 0, −e_x) of each edge, and dot(n, car − P) ≥ 0 for all 4 edges. Otherwise neighbouring quads are searched.
- **Stock side convention:** `_l` lies on the −left-normal side (median −4.8 m) and `_r` on the + side (+4.4 m).
- **What round 2 did:** `hwline.py` wrote them swapped (±5 m). Every quad had reversed winding, so the car was never inside one and progress stayed at 64. That means:
  - section 0 for ever → no block request → the road vanished past the start archive's sections;
  - the tangent at index 64 vs the car heading → WRONG WAY (0x89b30 counter 0x6d8 → 0x6a8 = 1).
- **Other progress sources checked:**
  - Start progress index: per-crsmdl table 0x1e53d8 (course 4: 64 / 57 / 57), same as our grid.
  - Race length: 1958 points (next table).
  - Section boundaries: 0x10a37c.
  - Collision: no path data in triangles or cells.

### Fix
- `hwline.py` now writes `_l` at −7.8 m and `_r` at +7.8 m, i.e. the stock sides, covering the whole 14 m deck. Centre line and AI lines are byte-identical. File set rebuilt (vis/, 131 files, same manifest keys, BOOT35G unchanged).
- `progress_sim.py` (model of 0x10ac58):
  - stock Happogahara, centre: reaches 2077 / 2079;
  - round-2 data: stuck at 0 (3021 / 3021 samples outside every quad), which reproduces the QA failure;
  - new data at lateral 0 / ±6.5 m: reaches 2077 with 0 misses.
- `game_sim.py` runs from the BUILT night data: progress → section → streamer window → road drawn → WRONG WAY test. Outbound and return at lateral 0 / ±6 m: 0 stuck, all 32 / 31 sections visited, 0 no-road samples, 0 wrong-way samples.
- Autopilot BOOT35GAP rebuilt, byte-identical (md5 d9987340…, APB 0x08D7C650).

## Round 4 (2026-11-01): r3 QA: SL crash, replay without road, shared TA record, old map
### 1. Street Legends Wangan crash (Bad Execution Address 0 at 0x130700) — FIXED (BOOT)
- **Cause: time of day, not the grid.** The race course object gets obj+0x20 = scene+0x6e8 = G+8 (TIME: 0 = day, 1 = night; race setup 0x82024).
  - Happogahara's load (0x134a74) opens `<course>_night_data` / `_start_data` only when obj+0x20 ≠ 0 (night-only course).
  - On a DAY race obj+0x88 stays NULL, and 0x130690 (s_vh_mt_lod.gmo holder, called from 0x134b74) jumps through a NULL vtable.
- WRIV's SetEnemy wrapper left G+8 = the enemy's own time (enemy table 0x5549e0 +0):
  - Nakazato (10) and Kyoko (24) are DAY rivals → 3/3 crashes.
  - Akio, EVO5/6, Sudo, Keisuke and Ryosuke are NIGHT, which is why r1 (Akio) loaded.
  - WRIV's panel accessor returned 0, which is DAY, not NIGHT (hence [·DAY·] on the panels).
- **Fix (boot/m35_r4_boot.py):**
  - h_se3's lineup path also sets G+8 = 1 (`jr ra` at 0x577540 → `j SE_T` 0x577ca0).
  - h_time returns 1, so the panels read NIGHT.
### 2. Replay shows no road — FIXED (BOOT + 2 ADD files)
- **Cause:** replay cameras come from `data/cam_data/y_camdata_<course><dir>.bin`.
  - Name table 0x21dce0, path built by 0x10a71c; r3 log shows y_camdata_40 opened at replay start.
  - Format: count, then (size, type, 0, 0, x, y, z, fov, …) records, then a tail of per-camera (end, start) course-progress windows.
  - Happogahara's positioned cameras sit at Happogahara WORLD positions, so the replay looked at the car from up to ~2 km away: black, lamps only.
- **Fix:**
  - `tools/camdata_hw.py` → `vis/files/w_camdata_40.bin` / `_41.bin`, same sizes as stock (33 + 37 positioned cameras).
    - Each camera is mapped by path index onto the new line (the gate method).
    - Lateral is clamped to 9–14 m (outside the 7.8 m barriers) and height to 4–12 m.
    - FOV, chase cameras and progress windows are unchanged.
  - BOOT hook HCAM: the `jal strcat` at 0x10a794 → for course 4 + RW, use `data/cam_data/w_camdata_4<dir>.bin`.
  - New disc ADDs: `cam_data/w_camdata_40.bin`, `cam_data/w_camdata_41.bin`.
### 3. TA record shared OUT/RETURN — FIXED (BOOT)
- The record index is course*2 + **DIR** + 18*weather (a1 = G+0xc / scene+0x6e4), not time.
- c2p1's hidx mapped (4, dir 1) → 8, so Wangan OUT, Wangan RETURN and Happogahara OUT all shared slot 8.
- **New hidx (0x56de30, in place):** course 4 + WFLAG → slot **16 + dir**.
  - These are course 8's DRY slots. Akina Snow is weather-forced wet (34/35), so nothing else writes 16/17.
  - Wangan ignores weather (only 2 free slots).
- **New hdisp (0x56de6c, in place; 2 relocs moved):** for course 4 + WSEL, TA shows the course-8 / weather-0 strings, which are the raw slots 16/17. Happogahara now shows its real direction; c2p1 forced dir 1.
- **Data caveat:** r1–r3 Wangan times were written into Happogahara's OUT slot 8 and stay there. Wangan starts with empty records.
### 4. Course-select maps from the new line — DONE (assets)
- `../r4/map/make_map.py` draws the new route in the stock style: light line, dark outline, OUT/RETURN labels and arrows in the travel direction, 1 km bar at 0.0442 px/m. It fits the stock map box (x 66–200, y 44–206).
- `../r4/map/m35_map_assets.py`:
  - **TA `ta_crs_sel` / Versus `tushin_crs_sel`:** `_03` anim 8 texture replaced in place with the cyan 256×256 4bpp map (same size).
  - **SL `visit_crs_sel` / Bunta `bunta_crs_sel`:** `_03` anim 8 gets its own 128×128 4bpp map drawn at 256 (UV 0,0,128,128).
    - Room comes from cutting the `_04` anim 8 WANGAN name texture 256×128 → 256×64 (lossless, rows 64+ were empty).
    - Sizes: 0x1bfd80 ≤ 0x1c0000 and 0x1ceb00 ≤ 0x1d0000. AKIO offsets rebased (−384) and verified.
  - Pixel check: only `_03` anim 8 changed in each file.
### Builds
- **BOOT35G (release)** = BOOT35G_grid (8653d41a) + r4 layer → md5 **481266bf0f4deee5d1cb07a5c8bd7ccb**, region 0x577ca0–0x577d37.
  - `verify_r4.py` ALL OK, covering:
    - record index for every course/dir/weather/WFLAG
    - hdisp
    - SE_T paths
    - HCAM for course 3/4/5 × RW × dir
    - HI16/LO16 pairs
  - `verify_grid.py` ALL OK.
- **BOOT35GAP (QA)** md5 **0c2003ee434d5fcec606e71116388413**: the AP region moved to 0x577d38–0x57f404, so **APB is now 0x08D7C750** (cheat 0x0057C750, speed 0x0057C79C). `ULJM05093_autopilot_b35g.ini` is updated. ap_sim / relocsim OK.
- **QA package:** `../build/files27a_5_r4.zip` (md5 e4e3950c…, 147 files) = r3 zip plus:
  - the 4 course-select files
  - BOOT/EBOOT = BOOT35GAP
  - the 2 cam files
  - `replace_list.txt` with the 2 `--add` lines
- Manifests: `../build/manifest_r4.json`, `manifest_hw.json` (133 add_replace keys, boot md5 updated).
