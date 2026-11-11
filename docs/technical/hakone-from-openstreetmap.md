# M45 HAKONE: an original Hakone course from real-world open data (build 45)

## Data sources and licences
- **Road:** OpenStreetMap, Hakone Turnpike ("アネスト岩田 ターンパイク箱根").
  - The two-way ways were fetched with the OSM API `/api/0.6/map` (24 tiles; Overpass refused connections) and chained into a 13.15 km line (`osm/`, `tools/chain.py`).
  - © OpenStreetMap contributors, ODbL 1.0 (https://www.openstreetmap.org/copyright). Credit them in the release README.
- **Elevation:** Copernicus GLO-30 DEM, tile N35 E139, from the AWS Open Data bucket `copernicus-dem-30m`.
  - © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018, provided under COPERNICUS by the European Union and ESA.
  - Free licence; credit "produced using Copernicus WorldDEM-30".
- No arcade or WMMT data, and no game rips other than the user's own Initial D disc, which supplies the native touge dressing.

## The course
- **Window:** Turnpike s = 3.6 → 9.6 km, which is the twisty middle section with the big U-bend at about 3.0 km of the course. Length 6000 m.
- **Direction:** outbound = uphill, from 900 m to 1419 m (mean grade 8.7 %, max 11 %). Return = downhill.
- **Geometry:** smoothed minimum radius 93 m. The legs never come closer than 167 m. Extent ±1.6 km.
- **Line (`hkline.py`):** 2080 points.
  - Spacing follows stock Happogahara's own spacing pattern, scaled ×1.006. Engine section index ranges, start grid indices (64 / 2022), gates and the race length therefore all keep their stock meaning.
  - `_l` / `_r` edges sit at −7.8 / +7.8 m (stock side convention).
  - AI lines are 10 m apart and cut up to 2.4 m to the inside of bends.
- **Dressing = "bend" (`tools/bend.py`, `tools/hk_build.py`):** every world-space Happogahara model is re-placed onto the Hakone line. That covers 32 sections, 64 LODs, 7 gates, vh19_ref and 4 slip-mark models.
  - Each vertex is mapped: fractional path index, lateral and height on the stock line → the same index, lateral and height on the Hakone line.
  - On the inside of bends, laterals past 0.55 R are compressed (no folds).
  - Real DEM slope beside the road fades in from 12 to 60 m: rises at 0.7×, drops at 0.3× capped at 10 m.
  - Normals are rotated by the heading change. Torn triangles are collapsed (1242 of 341k).
  - New uniform quantisation box per GMO; model and part bboxes are recomputed.
  - Every stock part, material, texture and vertex count is kept, and **every file stays at its exact stock size.**
  - vh_s11 (a slip mark modelled at the origin) is left stock.
- **Far terrain:** `s_vh_mt_lod` keeps its own mesh, stretched over the course box. Every vertex takes the real DEM height, pushed 3–25 m below the road near the line.
- **Sky:** sky domes ×1.30 in xz and lifted 200 m.
- **Collision (`tools/colli_hw.py` + `fixcells_hw.py`):** flat 10 m deck (±5.0 m, which is stock Happogahara's road width) plus M20 wall bands and end aprons. 6394 tris, 0 imperfect cells.
- **Spectators / lamp glows:** mapped with the same bend.
- **Replay cameras:** `h_camdata_40/41`, mapped with the same bend (`tools/camdata_hk.py`).
- **Rival pace:** `hspd.bin` (`hspd.py`) has the WSPD layout. Corner speed is √(0.95 g R), with braking and acceleration limits that include the grade, and per-slot tops and factors as in M37B.

## BOOT45H (`boot/m45_hakone_boot.py`, chainable; region 0x5a0000–0x5a51ff; run it LAST in the build-45 chain)
- **md5:** 565cc8373677b83326f1544a611374d1 when built on BOOT44V.
  - It also verifies ALL OK on polish BOOT45P and rivals BOOT45R as input.
  - 27 patched words, 145 new relocations, 363 code words.
- **HK byte:** 0x5a0010 (runtime 0x08DA4010, CWCheat 0x005A4010). HKCUR is at 0x5a0011.
- **Bank switch (`hkapply`):** sits in front of C-1's apply() at both call sites (0x56dda0 and 0x57f588).
  - HKE = HK && RW && mode ≠ Versus. When it changes, the switch exchanges the 4 disc-path strings (`wg`↔`hk`, `wangan`↔`hakone`), the 2 replay-cam strings, the grid pos/dir tables, WSPD↔HSPD and TS20 rows 18/19↔Happogahara rows 8/9.
  - Unicorn round trip: the data returns byte-identical to the input.
- **Menus:**

  | Mode | Changes |
  |---|---|
  | TA | Count 10 (Versus stays 9). CTAB[9] = 4. Commit WSEL = cursor 8/9, HK = cursor 9. Initial cursor and restore. Carousel anim 9. Sub-widget anim 9. Strip tiles 22/23. |
  | SL | Count 10, init, commit (WSEL = RW = cursor 8/9, HK = cursor 9), carousel/strip as TA, area clear → `PSP_area_seiha_10.ana`. |
  | Bunta / Devil Z Challenge | Count 10, initial cursor 9, BTAB[9] = 4, commit, carousel anim 9. bunta_crs_sel buffer raised 0x1d0000 → 0x1e0000 (0x9b91c). |
  | Race intro | "HAKONE NIGHT" = start2d anim 31. |

- **Records:** the 36-slot save layout has no free slot left (Wangan uses 16/17, Akina SNOW 34/35, and S+0x1a2..0x1cb is full). **Hakone uses Happogahara's WET slots 26/27**, so Happogahara WET/SNOW best times are shared with Hakone. The TA display aliases Hakone to (course 4, wet).
- **Verify:** `boot/verify45h.py IN BOOT45H.BIN patch45h.json` → **ALL OK**. It covers the exact diff, relocation sim, and unicorn runs of all 22 hooks plus the bank switch round trip.

## Assets (`art/hk_assets.py`, built from the newest disc versions)
| File | Hakone item | Raw size / limit |
|---|---|---|
| ta_crs_sel | name 256×128 4bpp, Happogahara's night photo, cyan 128 map, strip tile 64×64 | 0x2e7f00 / 0x300000 |
| visit_crs_sel | name, Happogahara photo, 128 map, strip tile | 0x1ce200 / 0x1d0000 |
| bunta_crs_sel | name, photo, map; AKIO offsets rebased | 0x1d2e80 / 0x1e0000 (needs BOOT45H) |
| start2d (on m45/rivals' file) | HAKONE NIGHT | 0x6ba80 / 0x80000 |
| seiha_10 (new) | AREA HAKONE | — |

## Verification (offline)
- `progress_sim`: 0 samples outside the quads, at lateral 0 and ±6.5 m, both directions.
- `game_sim` (built night data): 0 stuck, 0 WRONG WAY, all 32 sections visited, both directions.
- `streamer_sim`: spawns are in their start archives with road under them. Its "no road" hits are all before idx 64 or after 2022 (start/finish run-offs, where stock has big triangles); same as stock.
- Autopilot `ap/BOOT45HAP.BIN` (TEST ONLY; cheats `ap/ULJM05093_autopilot_b45h.ini`, APB 0x08D8F950):
  - unicorn picks the Hakone line when RW ≠ 0;
  - at S = 30 it reached idx 896/1040 uphill in 200 s at 65–108 km/h, worst 6.3 m off the line.
  - Happogahara and Akina lines are unchanged.

## Known gaps / risks
- **Versus:** no Hakone; the guest would load Wangan.
- **Bunta-mode top strip** for item 10 shows the wrong tile anim (Bunta class, no tiles 22/23).
- **Weather:** WET uses the rain effect on Hakone. SNOW may load Happogahara's snow archives (M39 snown paths are not in the C-1 table); this is the same as Wangan.
- **Collision is flat across the deck.** Stock Happogahara road camber is a few cm, and wheels may look a hair off on banked turns.
- **Intro/replay camera envs** (`s_vh1_path_env0/1`) are still Happogahara's, as on Wangan.
- **11 % grades:** check that low-power cars still climb in normal time.
- **SL lineup on Hakone** = the Wangan lineup unless RIVALS branches on HK.
- The scene-load memory for bunta_crs_sel is +64 KB.

## Rebuild
```
python3 hkline.py && cd tools && python3 colli_hw.py && python3 fixcells_hw.py && python3 hk_build.py && python3 camdata_hk.py && cd ..
python3 hspd.py && python3 progress_sim.py happou/ && python3 shots_hk.py && python3 game_sim.py && python3 renders.py
cd art && python3 hk_assets.py && cd ../boot && python3 m45_hakone_boot.py IN BOOT45H.BIN --json patch45h.json && python3 verify45h.py IN BOOT45H.BIN patch45h.json
cd ../ap && python3 ap_boot45hap.py ../boot/BOOT45H.BIN && python3 ap_sim45h.py
```

## QA r1 fixes (build 45 QA: SL hang, TA labels/strip, Bunta tile)
- **SL hang:** stock 0xd3ddc copies the 9-entry rival-count table 0x21179c into a 0x40-byte frame, then loops on count[cursor]. Cursor 9 read the caller's stack.
  - Fix: thunk 0xd4098 → `hd3` runs cursor 9 as 8 (Wangan, count 0) and then restores the cursor.
  - Audit of every course-select read of the cursor (+0x208) in SL, TA and Bunta found two more 9-item assumptions. Both are fixed: the TA BGM path `slti 9` at 0xe0c7c → 10, and the sub-widget special at 0x10ec40 (s0 == 9 → anim 8) is disabled.
- **TA strip stuck on MYOGI:** the carousel count vmethod (0x10f770 → 0x572f60) returned 9. It now returns 10 in TA/SL (Versus 9), and the Bunta class (0x10f0a0) returns 10.
- **Route/weather screens said WANGAN:** fixed by disabling the 0x10ec40 special.
- **Bunta strip:** bunta_crs_sel `_00` gets tiles 22/23. hs3h/hs11h now apply in modes 0–2. AKIO's texture offsets are remapped by index and checked to land on a 'MIG.' header.
- BOOT45PRH (on BOOT45PR c222d0f5) md5 4463d222d456e9e134ea4000576d2e2c. verify45h ALL OK, including unicorn 0xd3ddc for cursors 0–9 (returns, stock SlotToEnemy counts, cursor restored).

## QA r2 fixes
- **bunta_crs_sel memory:** the Bunta name goes into the empty (130,82)–(256,158) block of `_04` name atlas tex 0 (no new texture).
  - Raw is 0x1d1880. The buffer is now **0x1d2000**: hook `hbbuf` at 0x9b918 keeps the delay-slot `lui 0x1d` and adds `ori 0x2000`. Before this it was 0x1e0000.
  - DZC-path load buffers: bunta_crs_sel 0x1d2000 + rivaldemo 0x130000 (rivals back at stock) = 0x302000, which is +8 KB over build 44 (0x300000). Round 2 was +128 KB.
- **DZC (Akio-mode) strip:** `PSP_course_select_AKIO.ana` gets anims 22/23 plus a texture entry pointing at the new `_00` tile. akio_remap re-points every negative offset by texture index and checks for a 'MIG.' header.
- **SL rival-select header:** `hrv3` on 0x110cbc / 0x110ccc maps Hakone → anim 9.
  - visit_rival_sel (on the rivals file): `_04` anim 9 is HAKONE in the tex0 block; `_02` anim 9 is the Happogahara photo. Raw 0x255d80 of 0x260000.
- **Blank post-race talk:** not fixed. See the r2 report.

## Build 52 finishing (BOOT52H, on m52/cars/BOOT52C 093bb301)
- **md5 c470ba91d78baf57147ad94acd42306d.** New code at 0x5942c0–0x59435b plus in-place edits of M45H code. `verify52h.py` ALL OK (incl. 0xd3ddc cursors 0–9 and the Versus packet). Manifest: `manifest52h.json`.
- **Versus:** Hakone is item 10, and the TA hooks are widened to mode 3.
  - Rule byte 0xfb: low 7 bits 0x48 = Hakone, 0x57 = Wangan; bit 7 = SNOW. The host uses henc3 (0x19f718); the guest uses hdec3 (0x19f208), which sets HK and hands the byte on as 0x57.
  - Label: `tushin_crs_sel` gets anim 9 (name, photo, map) and tiles 22/23.
- **Records:** there is no unused save space.
  - Times end exactly where laps start (S+0xc6c0); laps end at the garage (S+0x11580).
  - S+0x116a8..0x11703 is used by about 40 code sites, and the card gap is taken by RIVALS (S+0x1c3..0x1ca).
  - Hakone keeps Happogahara's WET slots 26/27.
- **Weather:** WET = Hakone night data plus the rain effect (no file switch).
  - SNOW resolves to `hakone_snown_data.bin`, because the C-1 bytes 19–24 and the M39 bytes 26–30 compose. `hakone_snown_data.gz` is built with M39's touge rules (`tools/snow_hk.py`).
- **Camber (`tools/camber.py`):**
  - Stock collision crossfall follows curvature, c = −1.02·κ (r = −0.87, p97 |c| = 7 %).
  - Hakone has no hairpins, so I matched by severity: Hakone's p97 bend gets 7 %.
  - Collision deck y = path y + c·l. The bent visual road gets the same tilt (stock crossfall out, Hakone in, laterals clamped at 8 m). Grid rows are on the tilted deck.
  - Visual vs collision |dy|: p50 0.8 cm, p95 5.7 cm (stock 0.2 / 0.7 cm).
- **Sims:**
  - Progress: 0 misses. Game: 0 stuck, 0 wrong-way, 32/32 sections both ways.
  - Autopilot, whole course both directions at 69 and 108 km/h: worst offset 3.23 m (U-bend 2.79 m), 0 samples past the 5 m deck edge.

## Scenery assessment (not implemented)
The goal is a roadside that reads as Hakone Turnpike rather than bent Happogahara, using the user's own Initial D assets plus original geometry.
1. **Strip Happogahara landmarks:** billboards, houses, the start-area parking and shops. Use per-part triangle drops in the bend pass.
2. **Guard rails:** a continuous white W-beam on both sides, plus concrete on the drop side. Generate them along the line from the stock gard textures, as the Wangan barriers were.
3. **Forest:** dense cedar/cypress card walls on the uphill cut and treetops below on the drop side. Use the stock tree/forest cards, placed from the DEM side.
4. **Signs:** original km posts, curve chevrons and gradient signs in free texture slots. No real company names or logos.
5. **Rest areas:**
   - a toll-gate canopy near the bottom start;
   - the Daikanzan view lounge and car park at the top finish.
   Both as original low-poly geometry with stock textures, beyond the barriers (no collision change).
- **Constraint:** every file must stay at its stock size, so new geometry has to replace dropped stock parts. FPS needs watching.
- **Estimate:** 4–6 offline rounds (about 2 for 1–3, 1 for 4, 2 for 5), then PPSSPP QA per round.
