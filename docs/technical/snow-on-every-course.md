# M39 SNOW — a SNOW weather option on every course (TA + Versus)

Chain: BOOT38M (01e90ba9) → m39/aurastat → BOOT39A (6989717d) → `m39_snow_boot.py` → **BOOT39S.BIN (85ff0742…)**, for BOOT and EBOOT.
- Region 0x57f240–0x57fa9f.
- 16 patched words.
- The script is region-independent of the aura work: built on BOOT38M, the region bytes are identical (verified).

Rebuild: `./rebuild.sh`. It runs the archive recolour, the contact sheets, the BOOT on both bases and the verify.

## How SNOW works (generalised from Akina: M27, M29-v4 and M31)

### SNOW = WET + SFLAG
- The rain manager draws the flake field.
- Tyre spray and wet tail-light streaks are skipped while SCUR (M29-v4).
- The flake GIM and mesh are reshaped (scalc).
- The [SNOW] intro tile is anim 30.

### Course gate
Each "Akina only" test now reads CMASK, with one bit per course id:

| Bit | Course |
|---|---|
| 0 | Myogi |
| 1 | Usui |
| 2 | Akagi |
| 3 | Akina |
| 4 | Happogahara / Wangan |
| 5 | Irohazaka |
| 6 | Shomaru |
| 7 | Tsuchisaka |

- The mode test is 0, 1 or 3. In mode 0, SFLAG is only ever set by Miki.
- The weather widget count (3rd option) is TA/VS only.
- The five gated sites: wcount, scond, scalc (SCUR), ssetup and hsnow.
- **CMASK = 0xff: all 9 courses (8 ids + Wangan).** It is set automatically from the archives that exist. Courses without archives keep 2 weather options and stock behaviour.

### Disc paths
- `sapply` runs after C-1 apply at every course load (factory and race setup, via the M31 wdec tail).
- It is stateless: it writes SNOW or stock bytes into 13 strings.
  - `<c>_rain_data.bin` → `<c>_snow_data.bin` (day: WET loads the rain set)
  - `<c>_night_data.bin` → `<c>_snown_data.bin`
- Same length, and only the switched bytes are written.
- Happogahara's "night" bytes (26–30) are disjoint from C-1's happou/wangan bytes (19–24):
  - Wangan SNOW = `wangan_snown_data.bin`
  - Happogahara SNOW = `happou_snown_data.bin`
- Only `*_data` switches. start_data1/2 and the blk bundles hold no GIMs (checked on Akina, Happogahara and the M35 Wangan set). Inner XBB names are unchanged.
- Akina keeps the M27 6-path switch.

### Grip
- `hgrip` wraps the physics-flag copy (jal 0x109730 at 0xfe7bc, inside race setup).
- When SNOW is on, the game's own snow-surface flag 0x4b1318 / 0x4afccc is set. Normally that flag means crsmdl ≥ 16.
- The flag feeds the surface index (wet + 2·snow, 0x108648) and the snow branches at 0x1032b0 / 0x103504.
- Each course keeps its own physics, AI and top-speed rows. Akina keeps crsmdl 16/17 (stock Akina Snow rows).

### Records
- SNOW commits weather 1, so on every course except Akina, SNOW times **share the WET slots**.
- The S layout has exactly 36 slots: 9 ids × 2 times × 2 weathers, S+0x1e0 + n·0x578 up to S+0xc6c0, where the laps table starts. The only unused slots are course 8 dry day/night (2 slots), so there is no room for 7 courses × 2.
- Akina keeps course 8 wet (hidxS).

### Versus
- Versus uses the same course-select class, so it gets the SNOW option through wcount (mode 3).
- Rule packet byte 0xfb (M28 Wangan 'W' 0x57) gets bit 7 = SNOW.
  - host `henc2` (jal 0x19f718) sets the bit from SFLAG;
  - guest `hdec2` (jal 0x19f208) sets SFLAG from the bit and strips it before M28 hdec.
- Weather byte 0x101 already carries WET. Both PSPs need build 39: an older guest reads 0xd7 as "not Wangan".

## Archives (snow_course39.py → files/course/…, contact sheets in prev/)
- Built from `<c>_rain_data` (day) and `<c>_night_data`. Every archive keeps its raw size, with gzip repacked using the stock header. Transparent texels are untouched.
- Happogahara: packed-snow road with tyre tracks. Verges, trees, ground and roofs are snowy; signs, spectators and tunnels stay natural.
- Wangan (M35 night data): snow on barriers, walls and verges. The deck is wet-dark with darker tracks and edge slush. The tree1/tree4 textures hold the WANGAN LINE signs and are left natural.
- Built: 14 archives, 8.7 MB in total. Myogi, Usui, Akagi, Irohazaka, Shomaru and Tsuchisaka each get _snow_data (from rain) and _snown_data (from night); Happogahara and Wangan get _snown_data. Tunnels (tonnel/tnl) stay bare.

## verify_snow39.py (0 fails, unicorn on the relocated image)
- The 5 gates × modes 0–5 × courses 0–9 × SFLAG all match TA/VS/SL + CMASK.
- Real chain runs (hcrs2, wcount, wcommit, factory + scalc + wdec + apply + sapply, setup), checking disc paths after every load:
  - TA Happogahara SNOW + Retry, TA Wangan SNOW + Retry (crsmdl 9), Wangan WET, Akina SNOW, Happogahara DRY;
  - VS Happogahara and Wangan SNOW;
  - Myogi and Iroha (disabled: 2 options, stock paths);
  - Bunta with a stale SFLAG (stock).
- Grip flag tested per mode/course/SFLAG.
- Versus packet tested for SNOW × Wangan, host to guest.
- Not run in PPSSPP.

## QA list (PPSSPP)
1. TA Happogahara and Wangan: the weather select shows DRY / WET / SNOW. SNOW gives:
   - flakes, no tyre spray or tail-light streaks;
   - a snowy course;
   - the [SNOW] intro tile;
   - snow grip (slower cornering than DRY);
   - FPS like Akina SNOW (~26–30).
2. WET on the same courses is still stock rain. Akina SNOW is unchanged (course-8 records). Miki's SL race is still snow.
3. Records: a Happogahara/Wangan SNOW time shows in the WET record line (shared, by design).
4. Versus Happogahara/Wangan SNOW on two PSPs (or two PPSSPP instances): the guest gets the snow paths, flakes and grip. Wangan + SNOW together.
5. A course without archives (e.g. Myogi) has only DRY/WET.
6. Street Legends and Bunta: no snow on non-Miki races.

## Build 39 QA fix: rain streaks instead of flakes (Tsuchisaka, Myogi, Akina night)
- **Cause:** M27 scalc found psp_rain.gim/gmo by scanning *0x505cf8 + up to 0x1c0000 for a signature, and reshaped only that copy, only when SCUR changed.
  - The rain object takes its data from a different pointer: pack *(*(0x4e2e78)+4), looked up by name with 0x13e8b0.
  - Its address and the scan reach depend on what the course loaded. When the scan missed, or hit another copy, the layers were built from the stock mesh and texture, giving long streaks.
- **Fix (hrain, jal 0x1372b8 at 0xf4b34, the only rain-object creation):**
  1. Look up psp_rain.gim and psp_rain.gmo in the same pack the init uses.
  2. Read their state from the data itself: GIM == snow copy, and drop height |dy| < 1500 (stock 4172, snow 261).
  3. Reshape or restore to the wanted state: SFLAG && TA/VS/SL && CMASK[course]. The mesh change is per triangle relative to vertex 0: x/4, y/16, z/4, or ×4/×16/×4 with clamp.
  4. Run the stock init.
  5. While SNOW, colour all 3 layers white (alpha 0.75) whatever the init's creation flag.
  - Because state comes from the data, there is no double reshape, a reloaded pack is handled and WET restores.
- scalc's scan/swap is bypassed (0x5722b0 → b sk_spd). Its slow flake fall/spin values are kept.
- **Verify:**
  - 9 courses × day/night × TA/VS × SNOW/WET at rain init: snow GIM + dy 261 + 3 white layers only for SNOW.
  - Sequence Tsuchisaka SNOW → SNOW → WET (dy 4176) → SNOW on a reloaded pack → Akagi WET.
- QA: falling snow on every course, day and night, at a standstill: small flakes, no streaks. Check WET after SNOW (normal rain).

## Round 4: crash on DAY SNOW (f5d904c9, jump to 0 at 0x57f95c) + flakes too small
- **Cause:** the colouring loop used the init's return value v0 as the rain object. The init doesn't return the object; in daytime v0 = 0, so 0 + 4 gave a null layer, then the vtable was read as 0 and the code jumped to 0.
- **Fix:**
  - The loop now uses the object passed in a0 (saved on the stack).
  - Each layer must be non-null.
  - Each layer's +0x40 vtable must be the rain-layer class 0x251c30 (relocated); anything else is skipped.
  - The method pointer must be non-null.
  - The GIM is only touched if it starts with 'MIG' and the GMO only if it starts with 'OMG'.
- **Bigger flakes:** the drop is reshaped from 76 × 4172 to about 152 × 130 (x×2, y/32, z×2 relative to vertex 0), squarer and about 8× the area of the round-3 flakes. The layers are white with alpha 0.90. WET restore is ×½ / ×32 / ×½.
- **Verify model of the real init:** layers are stored into a0, and v0 is 0 for day or junk for night. Night has an empty slot and a foreign object whose method is null. 9 courses × day/night × TA/VS × SNOW/WET: no call through bad pointers, 3 colour calls by day and 1 by night, flakes only for SNOW. 0 fails.

## Round 5: flakes are 1–3 px dots everywhere, and no flakes in Miki's SL race
- **Draw path (static):**
  - Rain object update 0x1374d4. Per frame it moves each of the 3 layers down by fall 0x1e8804; layer y wraps from −4.5 to +4.5.
  - The whole field turns by spin 0x1e8800 around the camera (angle 0x4e2e7c).
  - The layer matrix is set through vtable +0x64, then 0x137748 submits each layer's GMO (0x1fd8c / 0x1fdb8, layer 5).
  - No per-particle size or point sprites: the drawn size is the mesh geometry itself, built at layer load (vtable +0x24) from the pack data that hrain reshapes beforehand.
  - Round 3 → 4 already changed streaks into dots, which confirms the reshape reaches the drawn mesh. Scale: a stock drop of 4171 units is a long streak, about 40 units per pixel at mid distance, so the 152 × 130 flakes of round 4 were about 3–4 px.
- **Size:** triangle relative to vertex 0, x×4, y/16, z×4 → about 304 × 261 units. That is about 2× linear and 4× area of round 4, roughly 5–8 px near and 3–5 px at mid distance. WET restore is exact for x/z and ±5 units for y.
- **Fall and drift:** snow fall 0.022 → 0.015 per frame (patched in M27's speed table at 0x57175c). Spin drift 0.05 is unchanged.
- **Miki (Street Legends):**
  - The rain field only exists when the effect root is built with weather = 1 (0xf4700). Its two builders pass the weather in t2: the race scene (0x892b4, from scene +0x6ec) and game2d (0xc4df4, from +0xf8).
  - `hroot` (jal at both sites) sets t2 = 1 whenever SNOW is active: SFLAG && mode 0/1/3 && CMASK. So Miki's race (mode 0, Akina, SFLAG from h_se) gets the field even if that path's weather value is 0.
  - All other registers and the caller's stack args are untouched.
- **Region end is now 0x57faa0** (code is sized exactly). It is past 0x57f8a0 because of hrain and hroot.
- **Verify:**
  - rain init on every course × day/night × mode: snow dy 261;
  - hroot cases: SL Miki, TA/VS, WET, Bunta;
  - fall speed 0.015.
  - 0 fails.
