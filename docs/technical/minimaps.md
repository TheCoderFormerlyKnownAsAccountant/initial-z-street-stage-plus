# M53 MAP: Wangan and Hakone maps match the drive (build 53)

## Findings
- **Course-select / route maps** (TA `ta_crs_sel`, Versus `tushin_crs_sel`, SL `visit_crs_sel`, Bunta/DZC `bunta_crs_sel`, and the
  TA route screen, which shows the same texture): Wangan (texture 8) and Hakone (texture 9) were already drawn from the shipped
  paths (M35 r4 `make_map.py`, M45 `hk_assets.py`; path md5 c41565f5 / f2843362 = the ones inside the course archives). The real
  path overlays them exactly in all 4 files (`course_select_maps_vs_real_path.png`), with the same handedness as Sega's own
  Happogahara map (checked by fitting the stock path to stock texture 5). **No change.**
- **In-race minimap (HUD) was wrong**: engine course 4 always loaded Happogahara's navi
  (`game2d.bin` → `navi.bin` → `PSP_navi_happo.ana.gz` + `navi_vh_path.bin.gz`), so Wangan/Hakone showed Happogahara's shape and
  roads. The dot moved along it by race progress.

## How the stock minimap works (BOOT)
- ctor 0xb572c (called from the race scene, 0x851f0) with crsmdl; table 0x1f6c30 (stride 20: short name, navi path name, int,
  2 floats). `sprintf("PSP_navi_%s.ana.gz")` at 0xb5790; 0xb5820 loads the ana and the path from the resident game2d XBB
  (scene+0x758), copies the path into its own buffer (obj+4), frees the temp (0xb5a7c), builds a cumulative 2-D arc table.
- navi path = 2080 × 5 floats = the race path uniformly scaled: col0 = s·x+ox, col1 = −s·z+oz, col2 = s·y+oy, col3/4 const.
- frame 0xb5e20: each car's dot = interpolation along the navi polyline at the car's progress fraction (1−f for returns).
- **The ana texture IS the course line** (dark, soft alpha), cut into 7 sprites: record = uv rect, centre (x, y) drawn at (x, −y),
  half-size; map px = (512·col0 − 256, 512·col1 + 256). The HUD draws only the dots in code. (Round 1 got this wrong.)

## Fix
- `gen_navi.py`: navi for each course from its shipped path, rotated/scaled to fill the unit square (Wangan θ 22°, 0.000263/m;
  Hakone θ 85°, 0.000288/m; stock Happogahara 0.000462/m, so the minimap shows ~1.7× more road), height compressed to the stock
  col2 range. Stored as a compact table (every 8th point, int16) → `tab_wangan.bin` / `tab_hakone.bin`; expander error ≤ 2.5 m.
  Texture (r2): the course line itself, 2 px at 256, stock palette; the ANA's record 0 shows the whole 256 texture at 2×
  (uv 0–256, half-size 256, centre 0,0 — same scaled-sprite trick as the shipped M35 SL maps), records 1–6 zero-size.
  So texel (u, v) = (256·col0, −256·col1). Model check: alpha under every navi point ≥ 160 (stock 184 mean).
- `build_assets.py`: `PSP_navi_wangan.ana.gz`, `PSP_navi_hakone.ana.gz` added to `navi.bin` inside game2d (base m46/cars
  game2d = the build 52 file). game2d raw 0x187d00 → 0x188c00 (buffer 0x190000, 0x7400 spare).
- `m53_map_boot.py` → **BOOT53M** (on BOOT52 a85c3ca4), region 0x5a8000–0x5a8e4f, 2 hook words, +33 relocs:
  - 0xb5790 `jal sprintf` → HSPR: WFLAG (0x56c740) && crsmdl 8/9 → name `wangan`/`hakone` (HK 0x5a0010), NSEL = 1/2.
  - 0xb5a7c `jal free` → HREG: free, then if NSEL: rewrite col0–2 of the loaded 2080×5 buffer from the table (header must be
    2080×5); cols 3/4 untouched. NDONE (0x5a8014) counts rewrites (debug).

## Verify (`verify53m.py`, log `verify53m.log`): ALL OK
diff only region + hooks; relocs old unchanged, new inside region; relocation sim at 0x08804000; unicorn HSPR (12 cases) and
HREG (bit-exact vs the python model for both courses, untouched for NSEL 0 / bad header); dot model on the stock HUD math:
dot within 0.35 m (Wangan) / 2.3 m (Hakone) of the car for every path point. If the game used index fraction instead of arc
fraction, the along-line offset is up to 182 m on Hakone vs 167 m on stock Happogahara (same spacing pattern), still on the line.

## Not changed
- TA lecture ("street theory") screen: loads `timeattack/lecmap/lecmap_%02d.bin` by G+4 (0x9d9d0), so course 4 → Happogahara's
  lecture maps + tips. Not touched (needs per-course lecture content); visible only if that screen can be opened for Wangan/Hakone.

## QA
1. TA Wangan OUT and RETURN: HUD minimap shows the expressway (L-shaped route), dot on the line all the way; no Happogahara roads.
2. TA Hakone both ways: the Turnpike line with real side roads; dot follows through the U-bend.
3. TA Happogahara: stock minimap unchanged (regression).
4. SL Wangan/Hakone race with a rival: rival dot also on the line.
5. Memory: game2d +3.8 KB (no error with "Ignore illegal reads/writes" off).

## Round 2 (QA b53: dots but no line on Wangan/Hakone)
Cause: r1 assumed the texture held side roads and the HUD drew the line; in fact the texture is the line. Fixed in game2d only
(md5 in manifest53m.json); BOOT53M unchanged (f99f1247).
