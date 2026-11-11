# PSP Games Reconfigured: Initial D Street Stage × Wangan Midnight Portable

Updated 2026-10-28 (build 13 tested: English menus, messages, HUD, cards).

## Games
- **Initial D Street Stage**: ULJM05093 v1.01, Sega.
  - BOOT.BIN is a plain ELF; EBOOT.BIN = the same code plus a 0x150-byte ~PSP header.
  - Data chain: gzip → XBB\x01 → @ANA/GIM/GMO.
- **Wangan Midnight Portable**: ULJM05264, Genki/Namco. BUILD.TOC/DAT, UCL NRV2B-LE32, all 8354 entries decode.

## ⚠ lba.dat rule
Initial D reads files through `USRDIR/lba.dat` (3761 × {disc byte offset, size, 0, name hash}), not through the ISO directory.
- `iso_tool.py patch` updates the table automatically.
- Keep repacked gzips ≤ original size (zopfli).
- **Hash solved** (function at 0x140d6c, `work/m5/xbbhash.py`). It works for XBB names and for lba.dat paths (USRDIR-relative, backslashes), so new files can now be added.

## ⚠ Memory rule (learned 2026-10-17)
- Scene loader reserves a fixed max buffer per file (now tightened in M13). If a scene file grows past its max, raise it in work/m13/tools/m13_boot.py.
The PSP heap has very little headroom. Each scene loads its XBB through a fixed 1.5 MB (rivaldemo) or 2 MB temporary buffer while the previous scene's data is still resident.
- Never add full copies of large assets. An Akio variant should be an XBB **alias** (same offset/size as the original) when the content can be shared. The ANA loader skips relocation of a blob already marked `@ANM`.
- Budget: rivaldemo is +34 KB over stock and the Devil Z race model is +96 KB over the stock S15. Those are the next things to slim.

## Builds
- **Build 13 = latest tested** (`remix_build/build13`: MAKE_BUILD13.bat patches the build 12 ISO; TEST_RESULTS.md; source `work/m14`).
  - English system messages (~530 strings), 8px message fonts, ~300 re-lettered menu/HUD textures, full Card Collection text.
  - Akio-mode course hint fixed (own small AKIO ANA). Devil Z 6速 label fixed (6-speed flags cleared).
  - Devil Z race model slimmed to stock size (env mesh stubbed).
  - Still Japanese: course map labels, Project D Web, Versus screens, ending, name-entry labels, card art plates.
- **Build 12 = latest tested** (`remix_build/build12`: MAKE_BUILD12.bat patches the 11c ISO; TEST_RESULTS.md; dialogue_jp_en.csv; source `work/m13`).
  - All 826 rival talk scripts in English (4,891 lines), English speaker names and inserted car names; half-width 8x16 talk font via BOOT hook h_ascii.
  - Memory fix: scene-file load buffers tightened (16 sites) -> after-race backgrounds, Bunta race with the Devil Z, and Street Legends rival select now work.
  - Verified: Devil Z Challenge talk/race/after-race, Challenge Bunta, Street Legends Akio slot (4th on Myogi, blue Z) and Itsuki talk.
  - Open: menus/HUD/cards still Japanese; Akio-mode course hint reads 文太レベル変更; PPSSPP chat button covers speaker names (turn it off in PPSSPP).
- **Build 11c = latest tested** (`remix_build/build11b`: MAKE_BUILD11B.bat, then MAKE_BUILD11C.bat, both patching on top of the build 11 ISO; TEST_RESULTS.md; source in `work/m12`).
  - Menu freeze fix: the widget set-index stores at 0x1113c8/0x1113d8 are NOPed. They overran 8-entry arrays and zeroed the layer pointer at +0x230.
  - Memory fix: PSP_course_select_AKIO and PSP_demo_vs_rivalname_AKIO are now aliases.
  - Verified in PPSSPP:
    - 9-item menu wraps both ways
    - DEVIL Z CHALLENGE course select
    - Akio talk scene
    - race with the blue Devil Z, Akio pulling away
  - Open:
    - The after-race talk has a black background.
    - A Bunta race with the Devil Z as the player's car hangs while loading (memory).
    - The Street Legends Akio slot is untested.
    - In Akio mode the course-select hint reads 文太レベル変更 again.
- **Build 11** (`work/m11`): Akio as enemy 31 in an extra last Street Legends slot on all 8 courses, unlocked after beating Bunta. He drives the blue Devil Z with M10 difficulty and has his own talkTbl_AKIO00–23. A cheat ini sets the game-cleared state. Next free byte 0x555210.
- **Build 10** (`work/m10`): Devil Z Challenge has no levels, Akio uses rubber-band AI (tunables at 0x554470), and his car is always blue (paint 3). The Tokyo Devil Z (enemy 6) is also blue.
- **Build 9** (`work/m8`): build 8 + original Challenge Bunta restored + DEVIL Z CHALLENGE as a 9th main-menu item (mode 2 + flag byte 0x554180; hash-swap hook at 0x140dc8 swaps 50 Bunta asset hashes to Akio files). Progress is shared with Bunta.
- **Build 8** (`remix_build/build8`): build 7 + 8 WMP race tracks as course-select songs ♪20–27. BOOT.BIN grows to 6.46 MB (region appended at vaddr 0x553c80). New disc files use `iso_tool.py patch --add`.
- **Build 7** (`remix_build/build7`): DEVIL Z CHALLENGE replaces Challenge Bunta, with Akio Asakura throughout.
- Build 6: Akio portrait and name on car select; Devil Z engine records set to 5 gears (the car-select 6速 label comes from a table not found yet).
- Build 5: power +12%, collision box, course-record name.
- Build 4: English menu, S30 names, HUD, GT-R engine sound, patched EBOOT.

## Devil Z Challenge (M5)
- **Code:** SetEnemy(6) in Akio mode, the race loader uses G+0x14 (car 12), tuning record 30, rubber-band AI (M10).
- **Talk scripts:** `rivaldemo.bin.gz` talkTbl_AKIO_* (41 files) generated by `work/m5b/make_akio_talk.py`.
  - The speaker name is `*_30` (アキオ).
  - 14 glyphs were added to rivaltalkfont page 3.
- **Portrait:** `rivaldemo/char/PSP_akina07_akio.ana.gz` (loose disc file, added to lba.dat).
- **HUD/start card/course select:** Akio files picked by the hash swap.

## Key anchors (BOOT.BIN vaddr = file offset − 0x54; CWCheat = vaddr + 0x4000)
- Main menu: 9 items (cursor 0xd64f0, jump table bound 0xd6a50). The Bunta lock is save bit 0x4a35b4.0.
  - Widget: 0x110f80. set-index: 0x11131c.
- Game state 0x490f08: +0 mode (2 = Bunta/Akio), +0x14 opponent car, +0x18 enemy id. Enemy table relocated to ET32 in M11.
- Bunta sequences: 0x3b course select → 0x3c meet demo → 0x3e race → 0x41 win / 0x42 lose demos.
- Rivaldemo scene ctor 0xcfd58/0xcfecc. Background/rain loader 0xd07d8 (it crashes when the rivaldemo load fails).
- Car code table: 0x1f1218. Engine index: 0x1eb904. Physics: file 0x1d8048, stride 0x8c. Engine records: 0x1d1ff8, 0x1d2458, 0x1dc478.

## Roadmap
1. M1 English menu ✅
2. M2 Devil Z in a replaced slot ✅
3. M3 Devil Z data:
   - ✅ names, HUD, sound, power, box, portrait
   - ⏳ grip/drift
   - ⏳ tuning stages
   - ✅ gear label (build 13)
   - ✅ slimmed race model (build 13)
4. M5 Devil Z Challenge:
   - ✅ in-menu mode
   - ✅ blue car
   - ✅ hard AI
   - ✅ after-race background (build 12)
5. M11 Street Legends Akio slot: ✅ tested in build 12.
6. Aura card system (planned; blue prototype first).
7. M6: highway course.
8. M7 music:
   - ✅ 8 WMP tracks
   - Eurobeat waits on files Daniel owns.
9. Translation:
   - ✅ rival dialogue (build 12)
   - ✅ menus, rival/course select, HUD, cards (build 13)
   - ⏳ homepage, Versus, ending, course maps

## Logistics
- Each test ISO is 1.16 GB. Delete old ISOs to the Recycle Bin and have Daniel empty it.
- Distribute only as xdelta patches.
- Testing tip: if PPSSPP screenshots look frozen, run the window un-maximized. F12 opens PPSSPP's ImGui debugger (CPU, Callstacks); it does not take a screenshot.

## Build 14 / 14b — full Japanese conversion (2026-10-28)
- Device: remix_build\build14\ (Initial_D_DevilZ_build14.iso), build14b\ (homepage fixes; current build).
- Done: Versus (tushin) menus, Project D Web (text, font, toolbar, records), ending staff roll (romanized names, repacked atlas; untested in PPSSPP), seiha "AREA ALL CLEAR" screens, card art plates + thumbnails (card/pic now in base), TA course map labels, lecture screen, name-entry keys, garage/tunecrs leftovers.
- Bat now uses files.zip + @replace_list.txt (cmd line limit).
- Left on purpose: 頭文字D logos, kana grids/fonts, p_map screenshots, ending manga speech bubbles.
- Known cosmetic: records header has a bar glyph instead of a space; replay details AKINA/DOWN/FINE heavy and squeezed; NGT label tiny; TEAM outlined.
- Eurobeat: user's Downloads folder appears to have "SUPER EUROBEAT presents initial d special stage" tracks.

## Aura spec (Daniel, 2026-10-28)
- Look: arcade-style soft colored glow around/behind the car, always on while racing.
- Unlock: aura cards earned as race rewards (win count, beating Street Legends / Bunta / Akio), added to the Card Collection.
- Equip: fitted per garage car like a tuning/sticker card; shows whenever that car is driven.
- Colors: arcade set of 6 — Blue (prototype, Akio), Red, Yellow, Green, Purple, White/Gold.
- Work dir: work/m15.

## Build 15 — Aura cards (2026-10-28; source work/m15, device remix_build\build15\)
- Renderer: re-enabled the game's dormant arcade aura (effect_data.bin.gz, manager vtable 0x24e080); aura id byte vaddr 0x555370 (0 off, 1 blue..6 white, 7 rainbow, 8 crimson, 9 orange, 10 cyan), set from the garage car at race setup.
- Cards 186–191 (internal 185–190): Blue/Red/Yellow/Green/Purple/White Aura; Collection now 20 pages; not traded, not in collection %.
- Unlocks: Blue = beat Akio (Devil Z Challenge hook); Red = Keisuke@Akagi; Yellow = Keisuke@Tsuchisaka; Green = conquer Irohazaka; Purple = Sudo@Akina+Iroha; White = beat Bunta (Street Legends).
- Fit: Garage > Select Car, SELECT cycles owned auras / removed; stored in garage entry byte 7 bits 1–3.
- Verified in PPSSPP: viewer, garage cycle, per-car aura in TA, persistence after reload. Not verified: actual award on wins; save gap after the card table not watched for other writes.
- Caution screen wrap fixed.

## Build 16 — Super Eurobeat songs (2026-10-28; work/m16, device remix_build\build16\)
- 30 songs from the Music folder as race BGM ♪28..♪57 with English labels, always unlocked; own ATRAC3 encoder (at3enc.py).
- build16 ISO boots and the picker works, but full-length songs don't play (the game loads the whole BGM file into RAM; race hangs at RETIRE).
- **Build 16d = current** (remix_build\build16d\Initial_D_DevilZ_build16d.iso, patches build16c): 85 s seamless loops (~1.4 MB),
  PPSSPP-verified in Time Attack (♪28, ♪57 incl. loop), Devil Z Challenge (♪42) and Street Legends (♪28).
- Fixes: whole-file load limit -> loops; smpl loop start 0 ignored -> 2048; missing ISO dirents for ss_06..30 -> iso_tool adds them.
- Old test output to clean up: build16 (full songs, broken), build16b (+test_loop.iso), build16t, build16c ISO (needed only as 16d's base).

## Build 17 + release kit (2026-10-29; work/m17)
- Build 17 = 16d + Project D Web fixes (records header, replay details icons, TEAM label) + Versus song-id unsigned fix. Device remix_build\build17\ (md5 2ac0d966…). PPSSPP-verified except Versus.
- Release kit: remix_build\release\InitialD_Remix_v1_kit.zip (173 MB) = sector diff vs stock (md5 225f1f56…); APPLY_KIT.bat rebuilds build 17 byte-identically (verified). Personal use only.
- Highway M1 (build17h): files load without crash, but swapped section visuals don't show in TA — loader investigation needed.
- Music encoder upgrade blocked (atracdenc download denied; own encoder can't do better at 132 kbps stereo).

## Highway M1 (2026-10-29; work/m17/f3, test ISO remix_build\build17h, patched in place)
- v6 works: Wangan concrete deck + barriers render at the Happogahara outbound start (driver cam), joins stock road, 29–30 FPS, no crash.
- Lessons: start sections come from happou_night_start_data1/2.gz (not vh2 loose files); keep all 25 stock GMO parts/order/quantisation; deck must cover the full path range (driver cam sits at path ~67); stock roads are 0x104 strips ~3 m.
- Open: return start (vh_a28 in start_data2) still shows stock; deck texture too bright/blurry; collision still stock.
- Blocked: atracdenc build denied by the auto-mode classifier even after Daniel's chat approval.
- v8 (2026-10-29): first ~400 m of Happogahara both directions = Wangan deck + continuous walls + new collision (path 0–160), stock-look asphalt, spectators moved. PPSSPP: walls hold, no falls, 30 FPS. Join to stock road at ~380–400 m untested (keyboard driving). Next: Daniel drives build17h; then extend (M4) section by section.
- M4 (2026-10-29): highway over sections 0–8 (path 0–639, ~1.7 km) + return start 27–28; m17/f3/m4/manifest.json (48 files, stock sizes). Test autopilot BOOT (m17/f3/ap/BOOT_AP.BIN, test only, control block 0x08D5A910) drove it in PPSSPP: no falls, smooth join to stock road at ~1'47, 30 FPS. build17h.iso currently carries the autopilot BOOT.
- M8 (2026-10-29): FULL Happogahara is the highway, both directions (m17/f3/m8/manifest.json, 131 files, stock sizes). Autopilot v6 finished outbound/return/outbound in one run (~8'28 at ≤69 km/h), all checkpoints register, no voids, 26–30 FPS. Left: outbound replay-start navy strip, rival AI at highway speeds, scenery polish (lamps/signs/skyline), course name/map/minimap, merge into a release build (without autopilot).

## Build 18 + release kit v2 (2026-10-29; work/m17/f3/m9)
- Build 18 = build 17 + Wangan night highway course (replaces Happogahara, all 32 sections, both directions; lamps, gantries, city layer, ground skirt) + WANGAN rename everywhere. remix_build\build18\ (md5 8ed85619…).
- QA: menus/intro show WANGAN; SL rival and DZC Akio drive the course; autopilot (test BOOT) finishes outbound 8'28 / return 8'25 at 25-30 FPS; no navy strip. One unreproduced crash in SL Wangan after the player car got stuck in a wall.
- Release kit v2: remix_build\release\InitialD_Remix_v2_kit.zip (180 MB); apply on stock ISO reproduces build 18 byte-identically (md5 verified).

## Build 19 + release kit v3 (2026-10-29)
- build19 = build18 + M19 AB (start flare, rainbow Akio, Akio rebalance) + C (CAR DATA panel, Wangan top speed rows) + D (intro+loop songs). ISO md5 478e96419db2627922e180b6925c2c72, BOOT c568e7d6….
- QA fix: CAR DATA font prio 0x40/0x41 crashed Select Car (no such layer) → 0xd/0xe.
- Open: SL vs Akio hangs at time-up (also build 18); Wangan wall-roll with no pause; in-race aura not visible from in-car cam; audio of intro/loop unheard by QA; Wangan >195 not driven.
- Kit v3 InitialD_Remix_v3_kit.zip (181 MB), apply verified.

## Build 20 + release kit v4 (2026-10-29)
- build20 = build19 + G (AURA TUNE: 18 steps bought with Tune Up cards, SQUARE in Change Car) + H (SL Akio card-pick clamp, flat Wangan wall bands, top-bar hint) + QA fix Q (post-race BGM index clamp for enemy 31; that was the real SL-vs-Akio freeze).
- ISO md5 3c5a8a9f7f324353958c91811a9db04b (collision v5 end caps; kit v4 final); BOOT 36ad2331…; kit v4 183 MB, apply verified.
- Wangan collision v2: no endless roll, START works; known issue: wrong-way past Return start ends nose-up at end cap (needs Retry). Open; in-race aura not visible (in-car camera); SELECT on a car with no aura shows no message.

## Build 20 (2026-10-30; remix_build\build20, kit v4 md5 3c5a8a9f…)
- Aura tuning: Garage > Change Car, SQUARE opens AURA TUNE panel: 18 steps (Blue/Red/Yellow/Green/Purple/White × stage 1–3 = 0.6/1.0/1.6× size, start flare 1.5/2.5/4.0×), 1 Tune Up card (id 0xad) each, progression-only (cards collectible), next colour unlocks at previous stage 3. SELECT cycles unlocked colours at highest stage / off. Stored in garage entry word0 bits 18–22 + byte7 bits 1–3.
- Rival auras: Akio rainbow pulsing (Challenge), Bunta small red at Challenge level ≥11. Akio pace: Challenge 0.97×/235 km/h, Street Legends 0.90×/210 km/h.
- CAR DATA panel: TRIANGLE on Change Car (35 cars, 3 pages, per course). Wangan top speed rows raised (225; Devil Z 252).
- Music: 30 songs re-encoded intro (from 0:00) + whole-bar loop.
- Fixes: Street Legends vs Akio post-race freeze (card row + music index clamp); Wangan lost-ground rolling (cell coverage), wedges, end caps.
- Known: wrong way past Wangan return start → stuck nose-up, Retry needed. In-race aura size and music not judged by eye/ear.
- BOOT chain: build18 BOOT → m19_ab → m19_c → m20_g → m20_h (+ fix Q in work/m20/q); final m20/BOOT20.BIN (+Q).

## Build 21 + release kit v5 (2026-10-30)
- build21 = build20 + m21/t branding "Initial Z Street Stage+" (title, 43 loading screens, mode/maker banners, card back, PARAM.SFO title, ICON0, PIC1) + m21/w Wangan (collision v6 end aprons, seam fix). BOOT = BOOT20+Q.
- ISO Initial_Z_StreetStagePlus_build21.iso md5 af70087ea3d4d8f250fa77540b75de9a; kit v5 185 MB apply verified.
- QA: branding OK (title/loading/banner/window title); seam gone; side walls OK; regression OK. Not reached: wrong-way into the end apron (keyboard). Card Collection watermark still old logo (not in set).

## Build 21 (2026-10-30; remix_build\build21, kit v5 md5 af70087e…)
- Rebrand: original "INITIAL Z / STREET STAGE+" logo (m21/t/logo.py) on title, 43 loading screens, mode select, maker select, card back; PARAM.SFO title "Initial Z Street Stage+", new ICON0/PIC1. Not yet: Card Collection background watermark (old logo), ICON1.PMF.
- Wangan: section-join seams fixed; wide asphalt apron + cap at course ends (wrong-way recovery untested).

## Build 22 (2026-10-30)
- build22 = build21 + BOOT chain (m22 ac aura in-car fix, mu full-song streaming BGM, t savedata strings; BOOT22 md5 117bf0d3…) + 30 full songs + 17 branding files (ICON1.PMF etc.). ISO Initial_Z_StreetStagePlus_build22.iso.
- QA: music streaming no crash (song past end/loop, retry, preview, stock BGM ok); chase cam = TRIANGLE shows aura; in-car 119 km/h ok (180+ not reached); branding ok (copyright line clipped at "fan"); regression ok.
- Kit v6 not built: only 0.64 GB free on the drive; needs ~0.6 GB. Release v6 scripts are in remix_build\release.

## Build 22 (2026-10-30; remix_build\build22\Initial_Z_StreetStagePlus_build22.iso; kit v6 pending disk space)
- Music: race songs ss_01–30 now STREAM from disc (m22/mu, hooks 0x1abae0/0x1abc78, 256 KB buffer) → full-length songs looping to 0:00.
- Aura: player aura hidden within 3.2 m of camera (in-car/bumper), size capped by distance (m22/ac, tunables 0x563940..).
- Branding: Card Collection/menus watermark (PSP_back.gim ×11 files), save icons + 27 save-list strings, title copyright line (cut off after "fan" — shorten), ending staff card, ICON1.PMF, release naming InitialZ_StreetStagePlus.
- BOOT chain: BOOT20Q → m22_ac → m22_mu → m22_t (md5 117bf0d3…).

## Build 23 + kit v6 (2026-10-30)
- build23 = build22 + title.bin (full copyright line in bottom strip). ISO Initial_Z_StreetStagePlus_build23.iso md5 df204f765cb797e40b606f8538210778.
- Kit InitialZ_StreetStagePlus_v6_kit.zip (341 MB), apply verified. QA: title line full, menu + TA ok.
- Build 23 (2026-10-30): build 22 + full copyright line moved to title bottom strip. Kit v6 InitialZ_StreetStagePlus_v6_kit.zip rebuilds it (md5 df204f76…). Current build to play.

## Build 24 + kit v7 (2026-10-30)
- build24 = build23 + m24/w Wangan night expressway (131 files). ISO md5 c55f46ac750156100c4080d87c8ab21f (after m24c deck fix in place); kit v7 rebuilt + verified.
- QA: towers/skyline ring/gantry sign/lamps OK, SL rivals (Daiki/Tachi/Akio) fine; m24c fixed deck (grey asphalt + lane lines); sections 9–14 unreached by keyboard. Disk ~0.7 GB free.
- Build 24 (2026-10-30; kit v7 md5 c55f46ac…): Wangan night city — lit towers + red lights, 360° skyline ring, sodium lamp pools/heads, English gantry signs, lane lines (thin strips using the stock road white line). Lesson: course vertex colours are 16-bit 5551 with opacity bit (0xc631 = stock grey); renamed texture slots are ignored by the game. Daniel confirmed build 23: aura in-car OK, full songs OK, beats Akio, Devil Z handling OK, Wangan end recovery OK. Rivals hold pace on Wangan.

## Branch 25x — Devil Z separate from S15 (experimental; build 24 = fallback)
- Variant approach (work/m25/car): S15 fully stock again in car 12; Devil Z = garage entry car 12 + bit 24 (START toggles in Change Car); own files car/race|select/nissan_s30_*, game2d/game2z.bin.gz; swap routine copies variant data into car-12 tables at race init / highlight.
- v2 QA: S15 stock everywhere; Devil Z race/HUD/aura/CAR DATA OK; save persistence OK. Open: Devil Z garage list name/model shows S15 (regressed from v1); an S15 and a Devil Z can't both be in one race (player S15 in Devil Z Challenge races as a Devil Z).
- Next: true car #36 per work/m25/car/PLAN36.md (6 PPSSPP-testable stages; 40+ tables, 128 35/36 sites).

## Build 26 (26d) — Devil Z is its own car #36 (2026-10-30; work/m26/car36, ISO in remix_build\build26a)
- Car id 35 = Devil Z (NISSAN list after S15), S15 (car 12) fully stock. Per-car tables extended to 36 (incl. 0x1d284c rival data, 0x21cdf4/0x21cea4/0x21cf34 paint, 0x208bd4 relocs, 0xc0968, 0x215c24, 0x21e910, 0x1bd454, 0x1d11d4, 0x1cebec, 0x1f20fc, switch 0x1bc274; aura limit 0x55f08c). Name slot 73 must stay blank (stock overlay); Devil Z name in slot 74. TA records: car 35 shares car 12's slots.
- Save migration on load (marker S+0x1cb): ≤24 saves car-12 → 35; 25x saves bit-24 entries → 35. Daniel's pre-26 save backup: remix_build\build26a\SAVEDATA_backup_pre26.
- PPSSPP QA 26d: buy Devil Z, paint, Akio blue, Challenge, Street Legends, Wangan/Akina TA, aura, persistence all PASS. Not yet: Project D Web rankings for car 35, Versus garage, release kit.

## Branch 27 — Wangan own course + Akina Snow + BGM page (in progress, 2026-10-31; work/m27)
- Daniel chose: Wangan as a true 10th course (keep slot 9), and Akina Snow playable as a SNOW weather option on Akina (stock PSP has no Akina Snow assets — must be built).
- Done (static only): C-1/D-1 engine — BOOT27C (course factory 0–19: 16/17 Akina Snow physics, 18/19 Wangan files; 20-row top speed; Happogahara stock). hpbgm: Project D Web BGM list 59 entries (WMP + 30 songs), chain after crs9.
- Next: C-2 menus/records/save migration, D-2 snow assets + weather UI (plan: m27/crs9/PLAN_C2_D2.md). QA blocked on disk space.
- 27 (2026-10-31): Time Attack 9th item = Wangan WORKS in PPSSPP (BOOT27C2H md5 877c959f, work/m27/c2p1; ISO remix_build\build27a). Wangan runs as engine course 4 / crsmdl 8/9 with flags WSEL (menu) + RW (race is Wangan, 0x56dbd1) + WFLAG (disc paths, top speed, records). Only 4 DISC paths are rewritten (section-bundle prefix + happou_night_data/start_data1/2 → wangan_*); inner XBB names stay stock (rewriting them broke lookups). Wangan records use Happogahara's unused day slots. Cursor returns to item 9.
- Remaining: Street Legends Wangan area + rivals, Devil Z/Bunta & Versus lists, WANGAN course-select art (9th item still says HAPPOGAHARA), Akina Snow assets + SNOW weather option. Project D Web BGM list (59 songs) PASS.
- 27b-snow (2026-10-31; build27a ISO, manifest m27/snow, BOOT27S 9e0c4a8b): TA 9th item WANGAN name + "WANGAN NIGHT" intro; Akina weather DRY/WET/SNOW with snow-recoloured day/night archives (akina_snow*/akina_snown*), round slow snowflakes (rain mesh reshaped), snow grip rows 16/17, SNOW records in course-8 slots. PPSSPP: all pass; FPS ~22 on snow start. Open: SNOW intro banner says [DOWN DAY WET]; TA top strip stays on MYOGI for item 9; Wangan in Street Legends/Bunta/Versus lists, CAR DATA line, seiha; records separation + grip need a real lap.

## Build 27 — current (2026-10-31; remix_build\build27\Initial_Z_StreetStagePlus_build27.iso md5 97176434…, kit v8 InitialZ_StreetStagePlus_v8_kit.zip)
- Devil Z own car #36; Wangan own course (9th item) in TA, Street Legends (area 9, shares Happogahara progress/Bunta level/default BGM; records separate), Challenge Bunta, Devil Z Challenge; Happogahara stock; Akina SNOW weather; Project D Web BGM list 59 songs; CAR DATA 10 courses; WANGAN strip tiles/headers/seiha.
- BOOT chain: 26D → crs9c → c2p1/c2p2 → hpbgm → snow → final(F) → slw(G,H,I) = BOOT27I d0afeeee.
- Not done: Versus Wangan (course data sent between PSPs carries only course id). Untested by lap: Wangan/SNOW record separation, SNOW grip.

## Build 28 — current (2026-10-31; remix_build\build28\Initial_Z_StreetStagePlus_build28.iso md5 3fd817b8…, kit v9)
- Versus: Wangan 9th course; host writes 0x57 to rule-packet pad byte 0xfb (obj+0xc0) for Wangan; needs both players on build 28. Tested with two PPSSPP instances (ad hoc localhost) both roles.
- CRITICAL FIX: game heap "UserSbrk" (_sbrk 0x366d4) was being created at 0x08D69000, overlapping remix code (0x565000+) — latent corruption risk in all builds ≥ ~20. BOOT28W reserves 0x553c00–0x579000 ("RemixRegion") at module start (hooks 0x3610c, 0x3672c); heap now ≥0x08D7D000; status word 0x08D772D0. Keep ALL new remix code below 0x579000 or raise the reservation.
- Autopilot test BOOT must be rebased onto BOOT28W (+0x200; APB 0x08D77DC0).
- Verified by autopilot: Wangan and Happogahara records separate; SNOW record separate from WET.
- Cosmetic: Versus race-details label says "Happo" for Wangan.

## Build 30 — current (2026-10-31; remix_build\build30, ISO md5 e8f1651d…, kit v10)
- Wangan night photo on all course/rival select screens; cyan Wangan map in TA/Versus (SL/Bunta keep Happogahara's map, same shape).
- Versus Battle Details shows "Wangan" (hook 0x1a0200, short-name table 0x240ef4).
- Akina SNOW perf: runs on WET path with tyre spray (0xf4bac/0xf4d4c) and wet tail-light streaks (0xf54d0) skipped → 24–27 FPS (was 13–30); flakes visible; [SNOW] banner; records course-8 slots.
- Miki (enemy 17) Street Legends Akina 8th slot on day snow, English talk, portrait PSP_akina08_miki; card row via Kai's row 16 (stock parser skips row 17). Lose path OK; win/card screen untested; panel shows [UP·NIGHT·WET].
- BOOT chain: 28W → 29V → 29S3 → 30M (c0906d26). RemixRegion ceiling 0x579000; used up to 0x5741a0.

## Build 31 — current (2026-10-31; remix_build\build31, ISO md5 b0dea23f…, kit v11)
- Garage panels: 8x12 font (cdsm_00.gim), opaque backdrop (m31/ui). NISSAN maker grid 9th cell Devil Z (m31/art). SL area face row 8 slots incl. Akio (all areas+Wangan) and Miki (m31/faces BOOT31F).
- Akio per-course wins/losses at S+0x1b0..0x1b9 (m31/akio); old saves start unbeaten everywhere.
- Wangan path apply now rewrites every load + RW/WFLAG decision at factory and race setup (m31/wfix). Daniel's "road disappears at ~23 s" (vh_ blocks opened) not reproduced; all modes tested open wg_; Versus untested.
- BOOT chain: 30M → ui → akio → wfix → faces (f6ee1561). Free code space below RemixRegion ceiling 0x579000 ≈ 11 KB — raise the ceiling (move heap start) before adding much more code.

## Pending build 33/34 (2026-10-31) — waiting on disk space (Daniel must delete old ISOs; overwriting files was blocked as destructive)
- BOOT32H: heap start moved to 0x08DB4000, RemixRegion ceiling 0x5B0000 (safe code region 0x5763b0+). Smoke-tested OK.
- BOOT33U (m33/unlock): Devil Z buyable after any Street Legends Akio win (per-course, old counter, or owning one); Devil Z Challenge menu locked until Bunta beaten (new locked banner in sel_gamemode).
- BOOT34W (m34/wriv): Wangan own SL lineup Nakazato, Kyoko, EVO5, EVO6, Sudo, Keisuke, Ryosuke, Akio; own progress S+0x1ba–0x1c0. Untested in PPSSPP.
- M35 real highway (2026-10-31, m35/hw): Daniel rejected the Happogahara-line reskin. New Wangan route = WMP Shuto carriageway, 6050 m (2.2 km sweeper, JCT with ramps/overpasses, 3 km straight; min radius ~204 m). New path/AI lines, collision, 32 sections from WMP chunks in true positions, gates by path index; manifest_hw.json (131 files, stock sizes). Autopilot BOOT35AP follows new line. Untested in PPSSPP (disk full). Risks: section culling by stock positions, checkpoint triggers, camera paths/minimap, fog.

## Build 35 — current (2026-11-01; remix_build\build35, ISO md5 81d1749d…, kit v12)
- Wangan = real WMP expressway route (6050 m) with new path/AI/collision/sections, Wangan spawn table hook (0x10a244/0x10a2e0 tables 0x1e5b70/0x1e5d20), path edge files _l (−7.8 m) / _r (+7.8 m) (swapping them breaks progress → no streaming + WRONG WAY), Wangan replay cameras w_camdata_40/41, TA records slots 16/17 (OUT/RET), new course maps. Includes 33U unlocks, 34W Wangan SL lineup (forced night — day rivals skip night archives), heap ceiling 0x5B0000.
- QA: TA laps both dirs (~2'30"–2'44" by autopilot, 205 km/h top), SL vs Kyoko/Nakazato OK. Open: rival pace ~150 km/h on straights (needs highway tuning); outbound replay unverified; Happogahara OUT holds old Wangan times.

## Build 36 — current (2026-11-01; remix_build\build36, ISO md5 c539b7a5…, kit v13)
- Devil Z tach needle fixed: per-car tach-dial table 0x1f36b0 had 35 entries → extended to 36 (Devil Z 9k dial); refs 0x8527c (race HUD), 0xc48e8 (replay HUD). BOOT36T.
- SL course-select faces at 0.62 scale, 2 rows of 4 (hook 0x110028), map/labels clear. BOOT36F (4f484507) = 35G → 36T → faces.
- Test leftovers now go to the Recycle Bin via Explorer ribbon Delete (right-click blocked); Daniel empties the bin.

## Build 37 — current (2026-11-01; remix_build\build37, ISO md5 d2890343…, kit v14)
- Wangan rival pace: AI target speed comes from BOOT per-point byte table 0x1d3528 (rows per course variant; reads 0x10452c/0x104648/0x1046b4); Wangan reads new per-rival tables (wspdB.py). Stock AI ×0.70 when far ahead — bypassed on Wangan via hook at 0x1044e8 (×1.08 when behind). Measured: Nakazato 198–200, Ryosuke 223–230, Akio 243–245 km/h. FD/FC Wangan top 242.
- TA records live in driver file S (0x491ef8): times S+0x1e0 + slot·0x578 + car·40 (ms low 25 bits), laps S+0xc6c0 + slot·560 + car·16. One-time clear of Happogahara OUT (slots 8, 26) at unpack 0x148fbc, marker S+0x1c2=0x3B.
- BOOT37B ed444181 (chain 36F → 37B), next free 0x57d240.

## Build 38 — current (2026-11-01; remix_build\build38, ISO md5 8a4b5315…, kit v15)
- Race music fix: M22 stream buffer (256 KB) was allocated from heap 0x1869f, which shrank as BOOT grew → in Street Legends/Bunta/Devil Z the alloc failed silently (no file open). Now heap 0 (stock race-music heap); streaming covers ids 110–147 (WMP ♪20–27 + new ♪28–57). BOOT38M (01e90ba9) = 37B + 6 words.
- Future builds: base ISO is build38 (build26a ISO deleted); build37 keeps SAVEDATA_backup_pre37 + pkg.

## Build 39 — current (2026-11-02; remix_build\build39, ISO md5 97668dc0…; kit v16 pending disk space)
- Aura stats (m39/aurastat, BOOT39A): progress P 0–18 → top speed ×(1+0.015P) (0x106728), drive force ×(1+0.02P) (0x1081b0), traction ×(1+0.01P) (0x108630), player's own garage car only; CAR DATA/AURA TUNE show bonus. Full aura Devil Z ~320 km/h Wangan vs Akio cap 250.
- SNOW on all 9 courses in TA + Versus (m39/snow, BOOT39S f08f114a): course mask 0xff, <c>_rain_data→<c>_snow_data, <c>_night_data→<c>_snown_data (14 new archives), snow-surface flag, Versus packet byte 0xfb bit 7. SNOW records share WET slots (except Akina). Flakes small dots; rain-object reshape at init with null checks.
- Daniel's save restored after tests.

## Build 40 (in progress, 2026-11-02; test ISO remix_build\build40t)
- Done & PPSSPP-verified: WMP characters as Wangan SL lineup (Hiramoto R32, Masaki FD, Reina R32, Eiji Evo VI, Kuroki R32, Ota FD, Shima FC, Akio) with ported WMP art + original English talk + Wangan night talk bg; bigger snowflakes + SNOW label; opening movie pipeline (H.264 + silent ATRAC3plus track copied from stock; video-only/LPCM PMFs hang) + "Don't Stand So Close" (ss_16, id 133) played via BGM hook at movie start, movie ends via stream-EOF + 1.5 s while song plays.
- Open: Wangan-lineup post-race talk text blank (Akio too, only on Wangan); new opening still has placeholder clips (17/19 need capture with Devil Z Challenge + cars); release blocked by disk space.
- BOOT chain: 39S(85ff0742) → 40C → 40M → 40N(05b8c37f) → 40S snowfix → 40F → 40G (6c3ea79f). Test autopilot at 0x580840–0x587f04 (test-only).
- Build 40 RELEASED (2026-11-02; remix_build\build40, ISO md5 91f21c6b…, kit v17): WMP Wangan lineup, snow fixes, movie-song hook present but OFF (MBGM_ID=0), stock opening.pmf. Known issue: Wangan SL post-race talk blank (G+0x1c reads 8 at talk; poke after race setup untested). Base for next build: build40 ISO. New opening video: 17/19 clips still to capture.
- Build 41 — current (2026-11-02; remix_build\build41, ISO md5 ec18d03b…, kit v18 shipped): aura bonus now +1 km/h top speed per colour at stage 3 (max +6), % boosts removed; Akio (Challenge + SL) capped at player's base top + 0.5 km/h with strong catch-up → unbeatable without a huge aura. Cards: win/TA finish → 10 cards (5% aura chance each), loss → 3 (no aura), 5×2 grid on result screen. BOOT41C 4bf4dcda (40R → 41A → 41C). Partly QA'd (Akio no-aura loss + 3 cards PASS); 10-card screen, SL time-up/retire untested. Usage limit ~93%.
  QA done: 10-card grid OK (60 FPS, aura card seen); SL retire → no card screen (stock); cosmetic: bottom card row covers the "You got these cards!" bar. Build 41 = base.

## Build 42 — current (2026-11-06; remix_build\build42, ISO md5 7cfd197d…, kit v19)
- Title screen + PIC1: Akio (original WMP bust 1719, mirrored, night-graded, rainbow aura) across from Takumi.
- WMP art polish (m42/wmpart): face framing/eye line matched to ID, sharpened/levelled, no-dither quantise, condensed serif start cards.
- Challenge Akio spec (m42/akio, BOOT42K 497d04da): Devil Z Challenge only — line speed 1.15× profile, corners up to 1.40×, player+8 catch-up, AI 15, cap = player no-aura top + 0.5 km/h for any car (closes faster-car loophole). SL Akio keeps build 41 set. QA: Akio 1.8 km ahead at 54 s with no aura.
- Intro capture: capture42.iso (BOOT42KAP autopilot) ready in remix_build\capture42; blocked on folder access to Documents\PPSSPP\PSP\Cheats and PSP\VIDEO. Akio leads from 3 s with 42K → film from countdown or slow him via 0x592720 for capture only.

## Build 43 — current (2026-11-06; remix_build\build43, ISO md5 d455f1ac…, kit v20)
- Title: Akio flipped (mirror of Takumi). Card screen rewritten (m43/cards, BOOT43C 90ccdfbd, code 0x593000–0x593f8f): thumbnails, names, NEW/×count tags, 10 on win/TA (5×2), 5 on loss (1 row), bar no longer covered; cards hide with bar on O.
- Note: stock card gate skips SL time-up/retire (no cards). 126 English card thumbnails replaced.
- Intro video: pipeline + edit.py ready; capture blocked on PPSSPP VIDEO folder access.

## Build 44 — current (2026-11-06; remix_build\build44, ISO md5 b94f41a1…, kit v21 md5 f0d39018…)
- New opening movie (m44/video): art-only Wangan-night intro, 15 driver vignettes (ID + WMP busts, car-select models), Akio/Devil Z with rainbow aura, logo; opening_new.pmf 9903f86f (104 s, silent ATRAC3plus). BOOT44V 42d10367 = BOOT43C + MBGM_ID 133 (ss_16 "Don't Stand So Close" via the M40 movie-BGM hook).
- Built by build44\MAKE44.bat from the build43 ISO; verify44.py checks dir record + lba.dat + md5 of opening.pmf/BOOT/EBOOT and sector overlaps (OK).
- PPSSPP QA: opening plays to the title, no hang; START (hold ~0.5 s) skips cleanly; title Akio mirrored; TA Wangan finish (autopilot BOOT44VAP, test only, ISO rebuilt clean after) → 10-card grid OK. Not verified: the song is audible (QA has no audio; PSP\AUDIO folder access denied); Project D Web Movie (both entries locked "No.??" on Daniel's save).
- Daniel's save backed up/restored. Kit v21 434 MB, apply verified exit 0.

## Build 45 — integrated, NOT released (2026-11-06; remix_build\build45, ISO md5 14336b80…)
- = build 44 + polish (result.bin, BOOT45P) + rivals (Wangan Rivals page 2, 36 portraits, gate) + Hakone (10th course, 70 files) + new opening (c9356143); BOOT45PRH e1908dba (chain reproduced). verify45: 117/117 OK.
- BLOCKER: SL course select cursor 9 (Hakone) hangs — stock 0xd3ddc copies only 9 counts (0x21179c) into a 0x40 frame, count[9] reads the caller's stack → endless SlotToEnemy loop. Hakone patch must clamp/extend. Kit v22 held.
- QA pass: opening, DZC gate locked, Akina/Wangan page-2 (L works, R did not), SL retire 5 cards, TA Hakone loads. Blank Wangan talk log at 0x08D98100 captured (talkTbl_HIRAMOTO11/07). Cheat tests blocked (no PSP\Cheats access). Report: work/m45/QA_B45.md.
- Build 45 r2 (BOOT45PRH 38e85e93; ISO md5 3b0c1f92…): SL Hakone hang, TA labels/strip, R page switch FIXED; TA Hakone out/ret + replay, 10-card win, FORCE/×99 cheats, Happogahara PASS. NEW BLOCKER: Devil Z Challenge crashes on Myogi and Hakone — rivaldemo XBB not loaded on the Bunta/DZC path (bunta_crs_sel +64 KB and rivaldemo +64 KB in the same transition). Kit v22 held. Blank Wangan/Hakone post-race talk: dumps in work/m45/qa/talkobj_*.txt (WMP talk tables use W_0/N and no D_ delay).

## Build 45 round 3 (2026-11-06)
- ISO 913a11f9 (BOOT45PRH 73311b21). DZC Myogi/Hakone fixed (no crash, Ignore-illegal OFF). Hakone panel/strip OK. Bunta, SL Hakone, regressions OK.
- OPEN: SL post-race talk blank for stock rivals too (Ninomiya, Bunta) — new vs r2; suspect r3 rivaldemo.bin. Kit v22 not released (also needs ~1.8 GB more disk: empty Recycle Bin).
- Build 45 r4 (2026-11-06): blank SL post-race talk is PRE-EXISTING (build 44 blank on Happogahara/Ninomiya and Akina/Bunta; Myogi/Kenji OK on b44 and r3). Card gate not the cause (cheat `_L 0x20597024 0` → still blank). Lead: blank tables lack the `D_n…D` block (only 25/761 tables have it). Needs code/data fix; kit v22 held. Details: work/m45/QA_B45.md round 4.

## Build 45 RELEASED — kit v22 (2026-11-06)
- ISO `remix_build\build45\Initial_Z_StreetStagePlus_build45.iso` md5 913a11f9852cb5d41341026b3f351bf0 (1,851,316,224 B), = r3 (BOOT45PRH 73311b21).
- Kit `remix_build\release\InitialZ_StreetStagePlus_v22_kit.zip` md5 f7f2c0305347591af64bb9601b87054d, 504,844,111 B (548 runs, 701 MB changed). Now ships ULJM05093.ini + CHEATS.md (make_kit.py copies them if present). Test-apply exit 0, md5 913a11f9; test_apply.iso recycled.
- Cheat ini checked: all 366 lines use CWCheat addr = runtime − 0x08800000.
- New: Hakone (10th course; credits © OpenStreetMap contributors ODbL, Copernicus WorldDEM-30), all WMP rivals on SL L/R page 2 + Hakone lineup, DZC all-clear gate, card-name polish, SL retire 5 cards.
- Known issues: blank SL post-race talk (pre-existing in build 44; fix in build 46 — blank tables lack `D_n…D`), a few rivals with no art, no Hakone in Versus.
- HOW_TO_TEST.md and release README.txt updated. build45\r4 test leftovers recycled. Free space ~3.5 GB.

## Build 46 + kit v23 (2026-11-07; remix_build\build46)
- Chain: 45PRH 73311b21 → TALK 46T 34eeb1b3 → AURA 46TA 0c808a4f (verify46a ALL OK) → CARS 46TAC 0d76eadf (verify46c 177305/177305). No overlapping patches. AP: BOOT46AP f0e7ca93.
- ISO `build46\Initial_Z_StreetStagePlus_build46.iso` md5 951e3dc99b74e9b53fe8619594f0d6fa (MAKE46 from build45 ISO + f46.zip/rl46.txt; VERIFY46 149/149). 6 UI base files matched build 45 (no rebuild).
- QA (Ignore illegal OFF): talk FIXED (Goto/Hakone, Ninomiya/Happo, Bunta, Kenji lines); intro OK; legend glow on SL Bunta; Challenge Bunta small/big glow OK via threshold test codes (Daniel's save is below level 10 → no glow, by design); Akio rainbow DZC Hakone OK; Wangan no glow, Kuroki R33; Supra bought, name/picture/model, Hakone TA AP 5'02"721, 10-card win OK; rebuilt clean.
- Gaps: Toyota maker thumbnails missing for new cars; NISMO parts logo on Toyotas; Supra texture patch; rival-select text still old cars; Celsior/Mark II purchase, CAR DATA screen, mirror glow, page-2 rival car, S15/Devil Z TA regression not run (usage limit). FPS ~16–22 in aura races vs ~25–30 before (host-dependent; watch).
- Kit test-apply now streamed (release\verify_kit.py) — disk ~1.5 GB free.

## Build 47 + kit v24 (2026-11-07; remix_build\build47)
- Stream LOD fix (m47/stream, 162 files) + opening_low.pmf 588376e2; BOOT unchanged 0d76eadf. ISO md5 e8ca8106933e448e2cc1332e5d1d1093 (VERIFY47 246/246, 123 files relocated, lba.dat consistent).
- Disk ~0.5 GB free: MAKE47 moved the build 46 ISO into build47 and patched in place (build 46 = kit v23 + stock). make_kit streams remix.kit into the zip; verify_kit.py takes the zip.
- Lean QA: Wangan/Hakone both directions (starts) 29–30 FPS, no pop seen; Happogahara + SL talk OK; opening OK; song-off no visible difference on PC. Hakone U-bend not reached.
- Cheat added: "Intro song OFF" _L 0x20584690 0x00000000. Recycle Bin does NOT free disk space — Daniel must empty it before the next build.

## Build 48 + kit v25 (2026-11-07; remix_build\build48)
- BOOT48M 86664dd5 = BOOT48R 70f5c3c5 (rebuilt from 46C 0d76eadf) + MBGM_ID=0; opening48.pmf 65fd7279 (song as the PMF's own ATRAC3plus track). ISO md5 ca8a07c1e81a1365274f3bbc54832837, VERIFY48 246/246; build 47 ISO kept (disk 2.3 GB free after Daniel emptied the bin).
- QA: audio capture shows continuous music for the movie length, no dropouts, clean end at the title. Movie FPS 7–28 while recording (watch on device). Daniel's save has clear word 0x08C94F9C = 0x100 (game treats it as cleared), so the Takumi lock can't be shown on it; verify48 covers the lock matrix. Wangan race + talk OK.
- Cheats: Takumi on Akina beaten `_L 0x70494F89 0x00000010` (8-bit OR); Intro song OFF removed.

## Build 49 + kit v26 (2026-11-07; remix_build\build49)
- BOOT49 c7e023b9f3514b9e31c9019b356fca13 = BOOT48M 86664dd5 + byte diffs of 49P dc8c3758 (cards still picked when all x99; 4 B), BOOT49R 56ddc99c (DZC unlocks after one Akio SL win; 46 B), BOOT49A fd4a3bea (aura STEP 0x5a5210 = 2 km/h; 1 B). No overlaps, no header/reloc bytes. opening49.pmf f6cf590d (manifest49i).
- ISO md5 cbcd37c26dc9f8970902c8a9333e6cf9 (1,996,007,424 B), VERIFY49 246/246; build 48 ISO moved in (kit v25 recreates it).
- Kit v26: release\InitialZ_StreetStagePlus_v26_kit.zip md5 a22f391294dfae51af3ef44aa57d2ddf, 596,690,485 B; TEST-APPLY OK. Disk free after: ~0.99 GB.
- Cheats: new "Unlock Devil Z Challenge (Akio beaten once on Akina; saves)" `_L 0x704960AB 0x00000010` (OR 0x10 on AKP[3] vaddr 0x4920AB, Akina); old one renamed "Devil Z Challenge FORCE (temporary)"; aura step default note 2; CHEATS.md warns x99 card codes make the card screen show only x99 repeats.
- QA: intro + song to title; DZC dark on Daniel's save (no Akio win), lit with Akio cheat; AURA TUNE "+36 km/h" at HUGE (CAR DATA screen not opened: Triangle unmapped); SL retire with x99 ON -> x99 cards shown, OFF -> normal NEW cards (retire awards cards, no win needed). Save/cheats restored, Ignore illegal ON.

## Build 50 + kit v27 (2026-11-07; remix_build\build50) — movie-only
- opening.pmf = opening49b.pmf 20a0a2fb44c4ef44b00115ecd649decf (same size; removes the 5% per-beat brightness flash). BOOT stays BOOT49 c7e023b9. ISO md5 efc77b413a978986079bdf70998e125e, VERIFY50 246/246; build 49 ISO moved in (kit v26 recreates it).
- Kit v27: release\InitialZ_StreetStagePlus_v27_kit.zip md5 cce25dc9497114248fdc6ddd8e1c6fda, 596,682,693 B; TEST-APPLY OK. Disk free after: ~0.34 GB (old kits v17–v24 ≈ 3.5 GB are the obvious candidates for Daniel to clear; build48 folder holds no ISO).
- QA: opening to title at 29–30 FPS while recording audio; music continuous for the whole movie (~108 s), no dropouts.
- Note: the v27 kit's README.txt has LF line endings (content correct).

## Build 51 + kit v28 (2026-11-07; remix_build\build51) — movie-only
- opening.pmf = opening51.pmf ef76b7f76a4e1376f2748701a6fb77ee (35,137,536 B; build-44 layout + new Bunta/Takumi/Devil Z ending, song embedded). BOOT stays BOOT49 c7e023b9. ISO md5 cb98167b35e145d0d4926c26855ef5c5, VERIFY51 246/246; build 50 ISO kept (disk now ~33 GB free; old kits v17–v24 are gone, so nothing was recycled).
- Kit v28: release\InitialZ_StreetStagePlus_v28_kit.zip md5 6c4381956cbd9afe8255dfb81928130d, 596,660,749 B; TEST-APPLY OK.
- QA: opening to title; recorded music continuous 107.8 s, movie 50–106 s min 50 ms RMS 2224 (no halfway stop; that was the preview file). PMF audio PES 0.95–109.7 s, no gaps. Movie FPS 7–29 while recording (lowest in the aura ending).

## Build 52 + kit v29 (2026-11-08; remix_build\build52) — cars 2 + aura-lite + Hakone camber + intro
- BOOT52 a85c3ca41cbd95bf802b0731935047e1 = BOOT52D 558139fe + diffs of BOOT52A b9679347 + BOOT52H c470ba91 vs BOOT52C 093bb301 (m52/merge/merge52.py: 0 byte overlaps, no header/existing-reloc change, .rel.data +32/+19/+6). verify52h ALL OK, verify52a ALL OK, verify52d 66/66, verify52c 91/91; all reloc orders relocate identically.
- ISO md5 2463d67d7b5120d61a9b1ba23123f321, VERIFY52 254/254 (build 51 ISO kept). Kit v29 md5 11d07cc482d53be4e68164fdfabbf538, 599,657,280 B, TEST-APPLY OK.
- QA PASS: intro Kuroki R33/Shima 964 cards; Shima race car black 964; Toyota grid 9 cars, Supra paints; Hakone SNOW loads snow Hakone; autopilot (QA ISO build52ap, BOOT45HAP) through the outbound U-bend at 62–70 km/h, no wall hits; DZC (Hakone, Wangan) + Wangan race OK.
- QA FAIL (cars): rival-select rows Kuroki "V-spec II (BNR32)", Shima "RX-7 ∞ III (FC3S)"; grey panel above the 964 roof in the race intro; small quad at the Supra roof in New Car. Supra/Mark II grid thumbnails speckled. TRD logo not seen.
- Not run: Versus course list (needs 2nd player; PPSSPP joined a relay → backed out), 10-card win screen (needs a win).
- Aura FPS (PPSSPP FPS counter, same spots; b51 → b52): Akio Myogi VS shot 27–28 → 23–25; countdown 26–29 → 25–30; GO 26–30 → 20–22; Akio ~55 m ahead 22–23 → 19–30; 125 m 17–19 → 21; 250 m+ 27 → 24–28. Bunta Akina (VS/3/GO/+2s/+4s): 30/24/27/30/30 → 30/20/30/30/29. No clear gain at this PC's 30 FPS cap; glow looks the same. Mirror: Akio's Devil Z seen in the mirror on Wangan, no glow visible there (b51 not compared).

## Build 53 + kit v30 (2026-11-08; remix_build\build53) — ship candidate
- BOOT53 4b48068f20d7690626c8abc076470d87 = BOOT52 + diffs of BOOT53C 9b75e040 (cars), BOOT53M f99f1247 (map), BOOT53K 7fdfebe5 (m53/akio; Akio scales with aura P) via m53/merge/merge53.py (0 overlaps, +82 relocs). verify53m/53k ALL OK, verify53c 73/73.
- ISO md5 abbe282ea1f2e59df9107b0ea3598f43, VERIFY53 254/254. Kit v30 md5 b3bc1f994541320a090bfcff0e1ee42f, 602,867,220 B, TEST-APPLY OK. game2d: map 40790f0e (cars' game2d was the unchanged b52 copy).
- QA PASS: R33/964 rival rows, 964 VS no panel, Supra no roof square, Toyota thumbs clean, Happo minimap, SL talk, opening.
- QA FAIL: Wangan/Hakone in-race minimap shows dots only (no road line); aura glow not in the mirror (mirror pass doesn't draw effects).
- Akio scaling inconclusive (no build-53 autopilot BOOT; manual drive at P=18 lost by 900+ m — Akio ~285 km/h). Daniel reports (in the app) Akio still beats him by ~250 m at max aura (likely b52).

## Build 54 + kit v31 (2026-11-08; remix_build\build54)
- BOOT54A 3932e7a1 (m54/akio: mirror-pass rival auras PL5 + Akio accel limit) crashes at every Devil Z Challenge start (bad jump 0x02948300, PC 0x0940f888, RA 0x08823488) on clean + AP ISOs; MIRON (0x5a5db0) = 0 avoids it. Shipped BOOT54B a16c18a2 = 54A with MIRON default 0 (one byte; no reloc there).
- ISO md5 94e2a8793302f59a73bdd4cda09f5500 (VERIFY54B 254/254). game2d b61bdab5: minimap line PASS on Wangan Out/Back, Hakone Out/Return. SL race + talk PASS.
- Akio P=18 test inconclusive: BOOT54AP (54A + BOOT53AP diff, AP hooks 0x1eaf0/0xfb754 + 0x580840–0x586952) autopilot drove 115–145 km/h scraping the wall; Akio −1592 m at 1:43. Needs an autopilot that actually runs flat out (or a line/K fix) before the scaling can be judged.
- Kit v31 md5 6ab8f000bec3c386f85ac01bdb401036, 602,867,993 B, TEST-APPLY OK.

## Build 55 + kit v32 (2026-11-08; remix_build\build55) — INITIAL Z page with 6 buyable cars
- BOOT55C 4a7f7614 (cars) on BOOT55A 09bf83a1 (= BOOT54B with the PL5 mirror hook unwired at 0x5569b0); verify55c 135/135. rl55 = BOOT/EBOOT + cars manifest55c minus its stale game2d d7efcd2f (kept the map b61bdab5).
- ISO md5 36d0b72dd38d4bda617cdac226363bcb, 2,014,259,200 B, VERIFY55 254/254 (sel_car / sel_maker relocated).
- QA PASS: New Car > INITIAL Z lists Sileighty, BCNR33, Z32, Z31, 964, Celsior; bought R33 + 964 (CAR DATA OK); TA Wangan with both (HUD, no memory errors, Ignore illegal off); Toyota page OK; Devil Z SL Myogi race runs. Sound not checked.
- Notes: new-car thumbnails plain grey (speckled top strip), no driver portraits, NISMO parts maker shown for the 964.
- README: removed the "Nissan rival cars not buyable" known issue.
- Kit v32 md5 f7f0780d6ad40463850b6e7fa14d9300, 603,527,800 B, TEST-APPLY OK (applied md5 36d0b72d).

## Build 56 + kit v33 (2026-11-08; remix_build\build56) — dialogue only
- build 55 + rivaldemo f68b1f5f (m56/talk: Akio + 15 Wangan drivers rewritten per scene, stock back-to-back repeats fixed, DZC WIN15 first line). BOOT55C unchanged. ISO md5 b6b7a0e00d099f4f97beb82a184423d5, VERIFY56 254/254.
- QA PASS: SL Akio Myogi (pre 14 / post 18 / travel 20, all distinct), DZC MEET15 first line + LOSE15, Hiramoto (7/11/13), Kenji pre/post; no memory errors. Pause-menu Exit counts as a loss (scene 21 needs a real retire/time-up). WIN15 not seen (needs a win).
- Kit v33 md5 af7c85581a0f0359ce4d31e45fdf4728, 603,755,607 B, TEST-APPLY OK. Disk free ~15.8 GB.

## Build 57 + kit v34 (2026-11-08; remix_build\build57) — rival finish fix (BOOT only)
- BOOT56H 828d8535 (BOOT55C + hkcnt: AI point count per crsmdl 8/9 = Hakone 600 / Wangan 606 / Happo 560). ISO md5 b4bcde3ecc908b04ecf3d153caf77a82, VERIFY57 254/254. AP QA ISO build57ap (BOOT57AP 5b8fa107 = 56H + BOOT53AP diff, merge53 MBASE=BOOT53).
- QA via ADVANTAGE sampling: Akio DZC Wangan BACK keeps ~263 km/h to the line (LOSE 2'33"155, Akio 159 m past); DZC Wangan first run LOSE 2'55"277; SL Wangan OUT Hiramoto and SL Hakone OUT Goto both finish at speed. Happogahara not reached (autopilot too slow, time-up).
- Kit v34 md5 6cc28ecdd7bee28f14750ee068afcc0b, 603,755,944 B, TEST-APPLY OK. Disk free ~11.1 GB.

## Build 58 + kit v35 (2026-11-08; remix_build\build58) — aura cards from aura opponents, Rainbow Aura card 192, NG+ auras, Akio retune
- BOOT58 49a43a8e = 56H + BOOT58C 893c3b83 (cards) + BOOT58A 282fe555 (aura); 0 overlaps, +200 relocs; verify58c/58a ALL OK both orders. Assets: card_viewer/card_view_s19/result (bases checked = shipped crs9/polish), + PSP_192/PSP_s_192 added.
- ISO 71f544aa8ae780a02b918f4081c953ab, VERIFY58 258/258. Kit v35 88bff8341dc8d739f00ff34b5fd68704, 605,967,884 B, TEST-APPLY OK. AP QA ISO build58ap (BOOT58AP 9e2d2cb0).
- QA: no aura cards on losses/time-up/TA PASS; NG+ tiers via OPPT/OPPS memory PASS (1/3/5/7 -> small/medium/big/max); Rainbow card + AURA TUNE + rainbow glow PASS; Akio Wangan ~285 km/h PASS. NOT DONE: an aura win (no way to win with the autopilot), Akina 2'38 (time-up before Akio finishes when the player is stationary). Note: AURA TUNE shows RAINBOW even with Blue selected.
