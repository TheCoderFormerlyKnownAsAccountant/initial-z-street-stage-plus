# M24 W — Wangan as a Tokyo expressway at night (course delta on top of build 23)

Apply `manifest.json` after all build-23 files. It has 131 files, paths relative to `PSP_GAME/USRDIR/data`, every file at its exact stock size. No BOOT change.
- **Base:** build 23 course = m17/f3/m9d + m20/h + m21/w.
- **Collision is not touched:** `make24.py` copies the build-23 `s_vh_colli_0/1.bin.nz` back into both start archives byte for byte (verified identical).
- **Builder:** `m24_build.py`, which is m21_build.py (M21 seam/overlap fixes included) plus the changes below. `make24.py` writes `files/` and `manifest.json`.

## 1. Distant city / skyline
- **Lit towers in every section** (replace the dim blocks):
  - one every 45 m on alternating sides, 26–120 m from the deck, as tall as the section's quantisation box allows;
  - faces mapped to a lit window-facade texture, vertex colour full white, normal forced up so they are lit like the deck;
  - dark roof, and a red aircraft-warning light on towers over 70 m.
  - Each tower is 10 triangles (22 with the light), cheaper than the old window-quad blocks.
- **Skyline ring on the sky dome (`vh_sky.gmo`):**
  - UVs rewritten so u follows azimuth (12 tiles around) and v follows ring height.
  - `k_ez_star.gim`: stars in the upper half; skyline in the lower half (silhouettes, yellow/white windows, red lights, a sea of city lights below).
  - This shows all along the course.
- **Mountains:** `s_vh_mt_lod.gmo` (the black mountain silhouette) is flattened to 730–815 m by changing only its y quantisation, so it sits below the course (900–1020 m) and no longer hides the skyline.

## 2. Sodium lamps
- Light pools are in the deck vertex colour: night asphalt blends to orange around each lamp foot (Gaussian, about 9 m).
- Lamp heads are bigger boxes in a full-bright warm colour. The 10 stock glow sprites stay on lamp heads from s=100.

## 3. Expressway signs
- Gantries now have two full-width boards back to back, a different sign each way. They are split 4 ways for the near plane.
- Board texts: B WANGAN LINE, DAIKOKU JCT 3 km, TATSUMI 1 km (blue), ARIAKE EXIT 11. EXIT 7 and B HANEDA are also in the texture but not used.
- Each gantry is moved up to ±100 m to a spot where it fits the section's quantisation box (pieces outside the box used to be dropped). 9 gantries, 18 boards.

## 4. Lane markings
- Deck texture: 14 m deck with 1 m shoulders, solid edge lines and two dashed lane lines (8 m dash / 12 m gap). One tile = deck width × 20 m.
- Deck v fix: the per-row v shift could land below the UV offset, so rows were clamped flat (the smeared asphalt seen in some sections). It now uses `ceil`.

## Textures (only textures no current geometry uses were overwritten; same size and format)
| texture | new use |
|---|---|
| `s_vh_tree4` (256²) | atlas: 6 signs, window facade, colour patches |
| `s_vh_road_tunnel2` (128×64) | lane deck |
| `k_ez_star` (128²) | stars + skyline |

- If a section GMO doesn't list these, a texture slot no converted geometry uses is renamed to them (the deck prefers a road-family slot).
- Previews of the encoded textures: `tex_*_gim.png`.

## Bug found and fixed (it also affects build 23)
- In vh_a10, a11, a12b, a12c, a14 and a15a the materials are not 1:1 with textures (there are extra materials). The builder used the texture index as the material index, so after the first duplicate those sections drew some parts with the neighbouring texture.
- `tex_mat()` now maps texture name to material index.

## Budget
- Every section fits its stock size with full scenery. a02, a04, a20 and a28 drop the imported WMP signs/poles to make room.
- Triangles (`tri_budget.json`): 88.4k vs build 23 86.8k vs stock 193.8k (0.46× stock, worst section a28 at 0.77×).
- Collision, AI lines and checkpoints are unchanged.

## Previews (software render)
These come from `m24_view.py`. Unlike the game it has no hardware lighting or fog curve, and it draws the dome world-fixed.
- `preview_m24.png`: driver camera at the outbound start gantry (s=165), the return city (s=1300), outbound mid (s=2330) and outbound late (s=4420).
- `preview_gantries.png`: TATSUMI / WANGAN LINE boards, both directions.

## QA asks
1. Do towers, windows and signs look bright in PPSSPP? The up-normal trick assumes the course's vertex lighting.
2. Is the dome skyline visible above the flattened mountains?
3. Is the lamp-pool tint visible?
4. FPS in sections 9–14.
5. Check sections 10–15a for textures changing on barriers/deck (the material-index fix).

## Rebuild
```
cd work/m24/w && BUILD_DIR=../../m24/w/vis M_SECTIONS=all python3 m24_build.py && python3 make24.py && python3 shots.py
```
