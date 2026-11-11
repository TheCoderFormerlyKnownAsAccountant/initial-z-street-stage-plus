# M46 CARS — Wangan Midnight cars, batch 1 (build 46)

## WMP car inventory (BUILD.DAT, model + 2 texture sheets per car)
- **20 player models** (high poly, 9.7k–13.5k tris, 00284…00721 step 23): FD3S, FC3S, SE3P, CT9A, CP9A, Z15A GTO, BNR34, R32, Z33, Z32,
  S15, RPS13, GDB, GC8, BL5 Legacy, JZA80 Supra, GRS182 Crown, SXE10, ZZT231 Celica, ZZW30.
- **26 rival/traffic models** (low poly, 1.7k–4k tris, 00744…00819 step 3, sheets +1/+2): S30 Akio (Devil Z, done in build 2/26),
  Z31 Harada, Z32 Yamashita, Z32 Makoto, R32 Reina/Hiramoto/Tomoya, R33 ×6 (Taka, Sonoda, Ryou, Motoki, Yamanaka, Yamamoto),
  R34 Goto, FC Kijima, FD Masaki/Ota/Oki, JZA80 Kei, UCF11 Celsior Gacchan, Evo V Eiji, Evo VI Maki, 964 Shima,
  JZX90 Mark II, KR42V van, E39A Galant (+ 00822 truck).
- **Initial D lacks:** R33, JZA80, Z32, Z31, Z33, 964, Celsior, Mark II, GTO, Legacy BL5, Crown GRS182, Celica ZZT231
  (+ traffic vans). It already has BNR32/BNR34/ER34, S13/S14/S15/180SX, FC/FD/RX-8, Evo III/IV/V-VI/VII, GC8/GDB, MR-S, Altezza.

## Batch 1 (ids 36–42; built from the low-poly rival models)
| id | code (disc file) | model | physics donor | engine sound | who drives it |
|---|---|---|---|---|---|
| 36 | nissan_bcnr33 | 00765 R33 | 7 BNR32 | 7 (GT-R) | Kuroki (page 2 + Wangan lineup) |
| 37 | toyota_jza80 | 00798 Supra | 31 ER34 | 7 | Kei; **buyable: New Car > TOYOTA** |
| 38 | nissan_z32 | 00750 Z32 | 11 S14 | 11 | Makoto |
| 39 | nissan_z31 | 00747 Z31 | 9 S13 | 11 | Harada |
| 40 | porsche_964 | 00810 964 "Blackbird" | 35 Devil Z | 5 | Shima (page 2 + Wangan lineup) |
| 41 | toyota_ucf11 | 00801 Celsior | 31 ER34 | 9 | Gacchan; **buyable** |
| 42 | toyota_jzx90 | 00813 Mark II | 10 S14 | 11 | **buyable** |
Goto keeps the R32: no stock enemy drives the BNR34, so there is no parts-row donor for it.

## BOOT46C (tools/m46_cars_boot.py, md5 f27501ef19fd5e335e9aafb64f53aa37)
- Input BOOT45PRH (73311b21). Run **last** in the build-46 chain (after TALK 0x594250… and AURA 0x5a5200…); it asserts memsz ≤ 0x5aa000
  and that 0x598940–0x59efff is empty. Uses 0x598940–0x59efa8 and 0x5aa000–0x5adc40 (memsz 0x5adc40). 252 patched words, 668 new relocs.
- **Physics alias:** the physics car index 0x4b130c (and rival copy 0x4b1308) is written in one place (0xff428–0xff470, clamp of obj+0x10/+0x14).
  The hook maps cars 36–47 to their physics donor (table PDTAB), so the 36-stride SoA block, AOS44/AOS8, TS20, BOX/ENG*, RIV44, aurastat
  and the Akio cap all read the donor's rows. No 2-D table moved.
- **Stock '< 36' accessors** (paint RGB 0x109dac, 0x109ec4, 0x109f18, 0x109f6c, 0x109f9c, 0x10a6bc, 0x10a6ec): entry stubs map 36–47 → 12
  (every new car is built in the S15 container, so the S15 paints/finishes fit).
- **30 per-car tables relocated to 48 entries** (all of M26's plus TACH 0x577d50, WV 0x572610, CRSVT, CARVT): rows 36–47 = donor rows
  ('M' tables from car 12 = container, 'P' from the physics donor); CODE/NAMES/NAMES2/FULL/NENTRY point at new strings; DRIVER −1; SOUND/TACH per car.
  110 references retargeted; pointer words keep R_32 relocs.
- **Bounds:** CAR DATA + aura panel: 43 cars; switch(car) 0x62ad0: 48 cases.
- **Records:** the 4 TA record accessors map 35→12 and 36–47 → their record donor (= physics donor), so no record overruns the next course.
- **Name anims** (car_select_00, anim car+13): 48→74 (Devil Z), 49–60→75–86.
- **New Car > TOYOTA:** list [AE86T, AE86L, AE85, SW20, ZZW30, SXE10, **Supra, Celsior, Mark II**, ST205] (10; ST205 stays last because New Car hides a maker's last car). Pairs updated (ST205 → (0,9)).
- **Rivals:** BOOT45R ID_CAR/ID_PD bytes (0x597160/0x597170) for Harada, Gacchan, Makoto, Kei, Kuroki, Shima → new cars, parts rows from enemy 6 (S15 container);
  M40 h_se40 (0x58049c) → Wangan lineup Kuroki R33, Shima 964, Reina R32.
- `tools/verify46c.py IN OUT patch46c.json` → **177156/177156 ALL OK** (byte diff, reloc types, no ref left into an old table span, every table row,
  unicorn: physics index for 12 car/rival cases vs stock, 7 accessors ×3 paints ×9 cars vs stock/car 12, GetCar/SetMaker/pairs, driver map, 4 record hooks ×10 cars,
  name hook, Wangan SetEnemy, rivals bytes).

## Assets (tools/build_cars.py, tools/assets46.py → files/, manifest46c.json)
- 14 car files (+ .gz): race ≤ 557,696 (the shipped Devil Z size), select ≤ 820,224. Slimming: race env meshes stubbed, 4bpp textures,
  interior dropped only if still over (level in files/cars_report.json). Roles from texture names + material (paint/glass/dark/trim/skip).
- UI: game2d vs/HUD tags (new 64×128 texture), car_select_01 pictures (sel_car + tushin_garage: the 3 Toyotas, 4bpp, sel_car 0x12fb80 ≤ 0x130000;
  garage_car: all 7), car_select_00 name anims 75–86, TA record names (new texture), tushin_record clones. Spare ids 43–47 clone the S15 everywhere.
- **Base files** (newest copies in the work tree; the integrator should confirm they match the build-45 ISO): game2d = m45/rivals, ta_crs_sel = m45/hakone/art,
  sel_car + tushin_garage = m26/files26d, garage_car = m31/ui, tushin_record = m27/crs9.

## Not covered / risks
- Maker-select thumbnails for Toyota slots 6–8 (sel_maker makerselect_00) not drawn: may show another car's thumbnail.
- Nissan list stays 10 (its grid object is [10]): R33, Z32, Z31 and the 964 aren't buyable yet; they are rival cars (garage only via cheat).
- New cars drive exactly like their donor (no per-car power/grip yet); no car card (driver −1); Project D Web rankings (hp_data_02) not extended.
- Per-car tables reached only through register copies (the way the tach table was missed in M26) could still read past 36 for ids 36+.
- Rival paint for the new cars comes from the donor enemy's paint row (S15 palette index) — check the colour in QA.
- Intro renderer note: m45/intro/carrender.py skips every `*etc.gmo`, so the Devil Z's 099bodyetc trim (bumpers, grille) is missing in the intro.

## Later batches (data only up to id 47)
Add a CARS entry (build_cars.py), a NEW entry (m46_cars_boot.py) and TAG/NAME (assets46.py); rerun the three scripts and verify46c.py.
Low-poly WMP cars: ~1–2 h each incl. preview review. High-poly-only cars (Z33, GTO, Legacy, Crown, Celica) need a decimation step first (~+1 round).
More than 48 cars: raise NC (tables re-relocate automatically, ~0.9 KB per car). Nissan purchases need the maker-grid object widened (one QA round).

## QA checklist
1. New Car > TOYOTA: 10 cars, Supra/Celsior/Mark II with picture + name; buy one; ST205 still at the end/hidden as stock.
2. Garage/Change Car: name, picture, CAR DATA (UP/DOWN cycles 43 cars; new cars show donor values), paint strip, AURA TUNE panel name.
3. Time Attack with each bought car: model, wheels at the arches, no missing panels, engine sound, tach dial, HUD tag, record saved under the donor's slot
   (and the next course's AE86 record unchanged).
4. Street Legends page 2: Harada (Z31), Gacchan (Celsior), Makoto (Z32), Kei (Supra), Kuroki (R33), Shima (964): model, paint colour, start card, HUD tag; no crash at load.
5. Wangan lineup: Kuroki R33, Shima 964, Reina R32.
6. Regression: stock S15 and Devil Z (model, paint, Akio), Devil Z Challenge, Versus garage list, memory errors with "Ignore illegal reads/writes" OFF
   (garage_car has 7 extra textures).
QA garage test cheat (slot 0 → car id N, clears that byte's flag bits): `_L 0x004A7478 0x000000NN` (N = 0x24…0x2A).
