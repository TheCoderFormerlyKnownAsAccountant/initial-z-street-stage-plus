# Initial D Street Stage (頭文字Ｄ ＳＴＲＥＥＴ ＳＴＡＧＥ)

- Disc ID ULJM05093, disc version 1.01, firmware 2.60, Sega. ISO 1.19 GB (≈300 MB real data + padding).
- BOOT.BIN: plain ELF, e_type 0xFFA0, load off 0x54 / vaddr 0, .text 0x0–0x1b82f4, .data vaddr 0x1b9894 size 0x99f5c, full section headers incl. .rel.text/.rel.data.

## Filesystem (`PSP_GAME/USRDIR/data/`)
- `car/race/<code>_race.bin(.gz)`, `car/select/<code>_sel.bin(.gz)` — 35 cars (both raw and gz present). Codes: toyota_ae85l/ae86l/ae86t/sw20/zzw30/sxe10/st205, nissan_bnr32/bnr34/s13k/s14q/s14k/s15/rps13/rps13k/er34, honda_ek9/eg6/dc2/ap1, mitsu_ce9a/cn9a/ct9a/cp9a/cp9at, mazda_fd3s/fd3sa/fc3s/na6ce/nb8c/se3p, subaru_gc8s6/gdb/gc8s5, suzuki_ea11r.
- `course/<akagi|akina|happou|iroha|myougi|syoumaru|tuchisaka|usui>/` — `*_data.gz` per day/night/rain, variant folders with `k_<v>_aNN.gmo`, `k_<v>_blk_NN_[01].bin`, `k_<v>_sub_NN.bin`.
- `bunta/bunta_crs_sel.bin.gz` — Bunta challenge course select (XBB: PSP_BGM_select.ana, PSP_BUNTA_00.ana, PSP_course_select_00/02/03/04.ana, PSP_makerselect_01.ana).
- `select/` — sel_gamemode (main menu), sel_car, sel_maker, sel_mission, sel_tunecrs, sel_nameentry, driverfile_sel.
- `garage/` — garage_car, topmenu, tunemain (tuning screens, 12 tuning card textures PSP_174–185), tunemenu, tunewindow.
- `font/<screen>/` — `*_lst.txt` + `*_00.gim` glyph atlases; `font/talk/<CHARACTER>/` dialogue fonts.
- `sound/bgm/{race,hp,rival,misc}/*.at3`, `sound/se/engine/*.bin` (ae86, al, cp, ek9, evo, fd, gc8, gtr, mr2, mrs, na6, s13 + tu_* variants), `sound/voice/`.
- `msg/*.ana`, `game2d/`, `title/`, `rivaldemo/`, `homepage/`, `card/`, `test/gmomerge` (dev leftovers).

## ⚠ lba.dat: the game's own file table (read this before patching anything)
- `PSP_GAME/USRDIR/lba.dat` = `XBB\x01`, count at 0x04, 3761 records × 16 bytes from 0x20: {u32 disc byte offset (LBA×2048), u32 size, 0, u32 name hash}, then a sorted hash→index LUT.
- The game opens files through this table (`sce_lbn` paths), **not** the ISO directory. Effects seen in practice:
  - A file patched in place that grows past its recorded size is read truncated. A truncated gzip hangs the game; this was the build 4 maker-select hang.
  - A file relocated to the end of the disc is silently read from its **old** sector, so the edit never shows.
- `iso_tool.py patch` (≥ plugin 0.3.0) rewrites the matching lba.dat record for every replaced file. It also helps to keep gzips ≤ original size: repack with zopfli (`zopfli.zopfli.compress(data, numiterations=15)[2:-4]` behind the original gzip header).
- Every record carries its file's XBB name hash, so lba.dat + the ISO directory give ~3700 (path, hash) pairs for cracking the hash.

## Code facts (BOOT.BIN vaddr = file offset − 0x54)
- PPSSPP runs a plain decrypted ELF as EBOOT.BIN, and patched BOOT.BIN copied over EBOOT.BIN works in-game (tested, build 4). EBOOT = BOOT.BIN + 0x150-byte ~PSP header.
- Per-car engine sound index: u32[35] at vaddr 0x1eb904 (car order = code table). Engine banks: 0 ae86, 1 al, 2 cp, 3 ek9, 4 evo, 5 fd, 6 gc8, 7 gtr, 8 mr2, 9 mrs, 10 na6, 11 s13. Names: 0x1eb990 (u32[12] → `<x>.bin`), 0x1eb9c0 (6 names × 12: U/D .DAT, phd, pbd). Loader at 0x1ac5a0.
- Car code-name pointer table: vaddr 0x1f1218 (35). Short names (maker screen text) at 0x214d84 and 0x21fdb0; full names at 0x23c7e4. Name-entry word list at 0x1ce5cc and 0x1ce66c: **don't** touch.
- Physics: struct-of-arrays at file 0x1d8048…, stride 0x8c (35 × 4 bytes). Drivetrain u32 at file 0x1d90b0 (FR 0, FF 1, MR 2, 4WD 3).
  - Tables 12–29 = **power/pace per course variant** (row = race-setup arg0 `[0x4b1320]`, 0–17; car = `[0x4b130c]`). Every stock car sits near 225, which is how the game balances its cars.
    - ×1.5 gave 114 → 174 km/h at 4 s; ×1.12 gives +14% (shipped for the Devil Z in build 5).
  - Groups 34/43/52/61/70/79/88/97/106/115 (9 rows each, row = course/2) don't change straight-line acceleration. They're probably grip/drift/AI factors; 70–95 favour the AE86.
  - Rival-AI tables (indexed by rival id `[0x4b13e4]`, 31 = special) live at 0x1d2e58…0x1d7f6c.
- Body/collision box: 11 floats × 35 at vaddr 0x1d19f0 = {half-track F, half-track R, front-axle z, rear-axle z, half-width ×2, front length, rear length, 0.3, 0.3, 0.2}.
- Engine/meter record: 24 bytes × 35 at vaddr 0x1d1ff8 = {gears, tach max, mid, redline, 2.0, flag}.
- No float gear ratios exist anywhere: the gearbox is arcade-style.
- PPSSPP load base 0x08804000 (module "beancar"); CWCheat address = vaddr + 0x4000. Cheat files work for live tuning. PPSSPP rewrites the .ini when you leave its Cheats screen, so edit the file only while that screen is closed. Disabling a cheat does not restore memory.
- Time-attack record names: `timeattack/ta_crs_sel.bin.gz` → `PSP_TA_rec_carname.ana` tex 0 (16-px rows, S15 = row 12).
- Maker-select screen: `select/sel_maker.bin.gz` → `PSP_makerselect_00.ana`: tex 12 = model-name list, tex 13–50 = 128×64 thumbnails (S15 = tex 36). Its car pictures come from garage_car/sel_car icons.
- Race HUD driver code: `game2d/game2d.bin.gz` → `PSP_game_vs_carname.ana` tex 0 (256×128 atlas of `[CODE]` cells).

## Formats
- gzip (FNAME) → `XBB\x01` → `@ANA` / GIM / txt. XBB round-trips byte-identical; name hash unknown.
- Models GMO, textures GIM (standard Sony).

## Tables in BOOT.BIN (file offsets)
- Car code-name pointer table 0x1f126c–0x1f12f4 (35 × u32 vaddr; index 0 = toyota_ae86t, last = mazda_se3p), strings 0x1f1070–0x1f1218; path format `data/car/%s/%s_%s.bin`.
- BGM path strings 0x2426dc…; pointer table referencing them at ~0x1eb56c.
- Course id strings 0x243a0c (MYOGI, USUI, AKAGI, AKINA, HAPPOU, IROHA, SHOU…).
- UI strings Shift-JIS 0x1f3600–0x2427ff (~700 strings, ~25 KB). Includes name-entry profanity filter list (~0x212000).

## Car container (`<code>_race.bin` / `<code>_sel.bin`, XBB, identical .gz copies)
- Parts are addressed by **slot index** (dummy entries keep indices); names: `<short>_NNN<tag>.gmo`.
  000 body (paint mat `bdcol` has no diffuse → runtime paint colour; part 1 = windows `*_mado`), 001–004 bu, 005–008 fs,
  018 bm, 022 gk, 026–027 rk, 032–035 eb, 038–041 ss, 042–045 rb (rear), 046–049 rw (wing, 046 = none), 052–055 mu,
  062–068 ti (wheel styles; `_race`/`_sel`), 077–080 ca, 082 db, 098 badges/wipers, 099 interior + driver sprite,
  100 nmlight (plate lamp), 2xx = `_race`/`_sel` LOD + `200envbody`/`201envwin` reflection pass, 990 rival, car_shadow, number plates.
  Variants per tag = visual tuning stages.
- Coordinates: metres, Y up, **+Z = front**, wheel centres at y = 0 (S15 tyre radius 0.339 → ground at −0.339).
- `<code>.bin` (828 bytes) per-car params: plate transforms {scale3, rot3°, pos3} at 0x00 + 0x24·k (front) and 0xd8 + 0x24·k (rear);
  wheel positions {x,y,z} at 0x210 + 0x24·k (6 records; S15 ±0.715, z +1.29 / −1.2388).
- Textures referenced by name (`*.pic` → `*.gim` in the same XBB). Car GIMs: index4 swizzled, 16-colour RGBA8888 palette.
- GMOs use named long chunks (hdr_len 0x1c–0x34), float positions, 16-bit normals/UVs, draws with a 5th field = start vertex.

## Proven so far
- Main menu (`select/sel_gamemode.bin.gz` → `PSP_mode_select.ana`) translated to English: **boots and works in PPSSPP** (2026-10-15).
- Build 2: Devil Z converted into the nissan_s15 slot (race + sel), awaiting PPSSPP test.

## Open
- XBB hash; car .bin internals; physics/tuning tables; course blk/sub formats; ANA layout geometry; whether ASCII renders in message boxes.

## Bunta challenge / modes (static analysis of build6 BOOT.BIN, 2026-10-15)
All addresses are vaddrs (file = vaddr + 0x54, CWCheat = vaddr + 0x4000). Tools and patches: `work/m5/` (ida.py, gscan.py, rel.py, xbbhash.py, patches/010-devilz-challenge.{json,asm}, ULJM05093_devilz.ini).

### XBB + lba.dat name hash (solved)
- Hash function at 0x140d6c(name, seed): `acc += c; h += rotl32(c, acc&31) + rotl32(seed, c&31)`. c is a **signed** char, and the "rotl" of c uses `srav`, so it is arithmetic. Seed = XBB header u32 at 0x0c, which is 0 in every stock file. `work/m5/xbbhash.py` matches 774/774 rivaldemo entries plus sel_gamemode, sel_car and bunta_crs_sel.
- lba.dat uses the same hash on the USRDIR-relative path with **backslashes** (`data\rivaldemo\rivaldemo.bin.gz`). It matched 989/989 files in the ISO listing. New files can therefore be added to XBBs and to lba.dat.

### Global game state G = 0x490f08 (getter 0xdd25c)
- +0x00 game mode = main-menu index (0 Legend/公道最速伝説, 1 Time Attack, 2 Bunta). +0x04 course id. +0x08/+0x0c/+0x1c/+0x20 time, direction, crsmdlid, weather.
- +0x10 player car. +0x14 **opponent car**. +0x18 enemy/rival id.
- +0x438 [8] Bunta level per course (0x491340). +0x49c flags (0x100000 = "BUNTA_UP" message). +0x4c8 next sequence id (0x4913d0).
- Race setup 0xff384 copies G into the race globals: 0x4b12e8 = mode, 0x4b1314 = rival, 0x4b130c = player car, 0x4b12c8.. = Bunta levels. 0x103cc4 then forces rival AI id 31 (`addiu t2,zero,0x1f` at 0x103d30) when mode == 2.
- SetEnemy(e) at 0xde564 writes G+0x18 = e. In modes other than 2 it also copies course/time/etc. from the enemy table. It always sets G+0x14 = enemy[e].car.
- Enemy table at 0x213930 has 31 entries of 32 bytes: {dir, time, car, course, crsmdl, ?, ?, 1}. Entry 6 TOKYO = car 12 (Devil Z slot), 13 TAKUMI = car 0, 29 TAKUMI2 = car 0, 30 BUNTA = car 29 (gc8s5).
- Name tables: upper-case names at 0x210cfc (32 entries, used for talkTbl), lower-case at 0x21112c, HUD names at 0x1d10f0/0x1f736c/0x214a14.
- Per-rival default BGM table is at 0x1e62d4. 0x1f27cc holds 12-byte per-rival visual tuning records.

### Main menu (seq 0x0a, scene ctor 0xd6068, update 0xd6734)
- There are **8 items** (cursor ctor 0x1140a4(...,8,...) at 0xd64f0). Index → seq id via the jump table at 0x1cf2f4 (`sltiu at,v0,8` at 0xd6a50): 0,1,2 → 0x0b car select; 3 → 0x0e comms; 4 → 0x44 garage; 5 → 0x0f cards; 6 → 0x10 Project D HP; 7 → 0x11 options. The index is stored as G+0 at 0xd6b14.
- CHALLENGE BUNTA = index 2. It is locked unless save byte 0x4a35b4 bit0 is set. The check is at 0xd664c, 0xd6940 and 0xd69b8, plus widget gray-out at 0x1115c8/0x1117cc/0x115888. The bit is set when a card is obtained (0x14e9c0). Locked message: 0x211bbc.
- The mode_select widget (0x110f80) picks ANA objects arithmetically from the item index (s3+3, +0xb, +0x13, +0x1b; locked Bunta uses 0x2d/0x2e). Adding a 9th item means re-laying out the ANA, so repurposing index 2 is the safe option.

### Master sequencer 0x149820 (table 0x1e9890, 0x5e entries)
- 0x28–0x32 Legend, 0x33–0x3a Time Attack, 0x3b–0x43 Bunta (handler 0x14abd8, sub-table 0x1e9a6c), 0x44–0x4a garage, 0x59 debug test menu (0x90cfc: "Rival Scene Test", "Bunta Challenge Test" ctor 0x117438).
- Bunta flow:
  - 0x3b course select HSelectBuntaCrs (0x9c380 / 0x9b850, loads data/bunta/bunta_crs_sel.bin.gz).
  - 0x3c pre-race demo (MEET, scene = level).
  - 0x3d race load (0x94d90 + 0x94654).
  - 0x3e race.
  - Post-race (0x7e0f8) → 0x40 result (0x9c704), or 0x3f (0x74a64), or 0x4b.
  - 0x40 → 0x41 WIN demo (0x9b088, scene = level+0xf) or 0x42 LOSE demo (0x9b288, scene = level+0x20), via seq 0x0c save, then back to 0x3b.
- Course select commit is at 0x9bd60–0x9bfd0. Cursor → course table at 0x1d0eec = {0,1,2,3,5,4,6,7}. Course → crsmdl jump table at 0x1bdc04. Next seq = 0x3c. SetEnemy is 13 for level <6, 29 for level <11, else 30.
- Levels run 0..15 (16 = cleared). The selectable maximum per course is save bytes 0x4a35b5[course]. On a player win (0x7ef18) the level goes up by one and the save byte follows.
- Race loader 0x863d4, mode-2 branch at 0x86590: the opponent car at sp+0x264 is **hard-coded 0** for levels <11 (0x865c4, 0x8660c) and = [G+0x14] for levels ≥11. Car array → 0x490330.

### Bunta AI (rival id 31)
- 0x104370: if rid == 31, speed = lo + (hi − lo) · (BuntaLevel[idx[row]] & 0xf) / 15.
  - lo = B[row]·C[row], hi = A[row]·E[row].
  - A = 0x1d3458, B = 0x1d3410, C = 0x1d7e78, E = 0x1d7ec0, idx = 0x1d34a0. Row = course variant [0x4b1320] (0–17).
- Other rivals use T1 0x1d2e58[rid·12] × T3 0x1d7b80 × difficulty 0x1d7cf8 (Bunta mode skips the difficulty factor).

### Rival demo / dialogue (data/rivaldemo/rivaldemo.bin.gz, a single XBB for every character)
- Talk file chooser at 0xcd7c0(enemy, scene):
  - Enemy <31: `talkTbl_<NAME>%02d.txt` with scenes 00–23.
  - Enemy 31 (Bunta challenge; 0xcfecc uses 0xdeb30(30)+1):
    - scene <0x10: MEET05/10/15 (AKINA_ variant on course 3).
    - 0x10–0x1f: WIN%02d, or `BUNTA_<CRS>_WIN14` at level 15.
    - 0x20–0x2f: LOSE05/10/15.
    - ≥0x30: TIMEUP.
- Scripts are Shift-JIS with CRLF, one quoted token per line.
  - Commands are `"X_n"` or a bare `"X"` (P = portrait frame, C = speaker side, W = wait frames, N = page/wait, K, B, I, R, E = end, X, *, <, b, i…).
  - Text lines use `¥n` (0x5c 'n') for newlines. Parser at 0xce358.
  - Dynamic inserts: player name (default "プレイヤー" 0x210fd0), loss count ("九十九回以上も").
- Font: `rivaltalkfont_00..03.gim` (256×256 4bpp, 16×16 cells) + `rivaltalkfont_lst.txt` (`char=index`, 915 glyphs, full-width only, page = idx/256).
  - 109 cells are free on page 3.
  - Page count = literal 4 at 0xcde88 (`addiu a3,zero,4`). With 0, the loader 0xb79f8 probes up to 8 `%s_%02d.gim`.
  - Init at 0xb77c4(…,16,16,256,256).
- Speaker names: `charNameTbl.txt` (line 16 = 文太) + `charNameTbl_lst.txt` + `charName_00.gim` (60/256 cells used).
- Portrait: enemy 31 → `data/rivaldemo/char/PSP_akina06_bunta.ana.gz` (0xd0588). Model: `/driveA/model/rival/r_bunta_challenge/rival_bunta_challenge_{pol,tex}`. Other rivals use `PSP_<crs>%02d_<name>.ana.gz`.
- **There is no font/talk/<CHARACTER>/ folder.** Talk text and font live in rivaldemo.bin. font/demo_charname/ is only a loose copy of the charName files.
- Mode-2 race-start name image is hard-coded to enemy 30 at 0xec694 → `PSP_st_rivalname_BUNTA.gim` in game2d/start2d.bin.

### Devil Z Challenge patch (phase 1, repurposes mode 2)
- `work/m5/patches/010-devilz-challenge.json` / `.asm`: 6 immediates, none of them relocated.
  - 0x9bfa0/0x9bfb0/0x9bfb8 → SetEnemy(6), so G+0x14 = 12.
  - 0x865ac/0x865b4 → `slti at,v1,0`, so every level takes the [G+0x14] path.
  - 0x8665c → `addiu a1,zero,90`, so the tuning record is 30 (stock parts).
- AI stays 31. Statically verified only; PPSSPP test is pending.

## Rival character assets (confirmed in build 7, Devil Z Challenge)
- Talk scenes: `rivaldemo/rivaldemo.bin.gz` (XBB, 774 files).
  - `talkTbl_<NAME>_*.txt` scripts are Shift-JIS, one quoted token per line.
  - `*_N` sets the speaker to line N of `charNameTbl.txt`. Appending a new line (index 30) works.
  - Fonts: `rivaltalkfont_00..03.gim` with `rivaltalkfont_lst.txt` (LF line endings), and `charName_00.gim` with `charNameTbl_lst.txt`. New glyphs can go in the free cells; they are 16-px white alpha glyphs.
  - VS-scene names: `PSP_demo_vs_rivalname.ana` tex 2, 32-px rows (row 14 = Bunta, row 6 = 東京から来た二人).
- Talk portraits: `rivaldemo/char/PSP_<course><nn>_<name>.ana.gz`. Each holds 10 frames (P_0..P_9), 256×256 or 512×256, 8-bit.
- Race HUD:
  - Faces: `game2d` → `rivalface.bin` (nested XBB of 31 `PSP_g_k_NN_face_*.ana.gz`, 128×64, about 83×42 visible).
  - Names: `PSP_game_rival_<NAME>.gim` (64×16, only about 47 px visible).
- Race-start name card: `start2d.bin.gz` → `PSP_st_rivalname_<NAME>.gim` (128×32 or 256×32).
- Bunta course select: `bunta/bunta_crs_sel.bin.gz` → `PSP_BUNTA_00.ana` tex 0 (face and level panel) and `PSP_course_select_00.ana` tex 8 (button hint bar).
- Main menu, Bunta item: `PSP_mode_select.ana` tex 3 (banner art), tex 6/9/12 (labels), tex 15 (description).

## BGM / music (static analysis of build7 BOOT.BIN, M7, 2026-10-15)
All addresses are vaddrs (file = vaddr + 0x54, CWCheat = vaddr + 0x4000). Tools, patch and builder: `work/m7/`.

### Sound table and playback
- One sound table for all streamed audio: 110 entries of 8 bytes {char *path, u32 flags} at 0x1eb518 (ids 0..109). Every pointer has an R_MIPS_32 relocation.
  - id 0 = misc/dogfight; ids 1..20 = race songs, with id 12 = misc/DancinInMyDreamsS (not selectable).
  - 21..39 hp previews, 40..45 misc (win/lose/timeup/CAR_SELECT/STAGE_SELECT/RESULT), 46..74 rival themes, 75..79 misc WIN/LOSE, 80..109 voice/hp.
  - flags byte0 = loop, byte1 = race song. Race songs are 0x101.
- The table is followed by a per-rival BGM-id table at 0x1eb888 (31 words), then the per-car engine table at 0x1eb904. It cannot grow in place.
- Only two code sites read it, both through relocated lui/addiu pairs:
  - play(ch, id, a, b) at 0x1ab9d8 (wrapper 0x1ab9c0): 0x1abab4/0x1ababc. It formats the path with `"%sdata/sound/%s"`, prefix "disc0:/PSP_GAME/USRDIR/", then opens the stream.
  - Stream start at 0x1abbe4: 0x1abc28/0x1abc2c, which reads the flags (loop = −byte0).
- No bounds check on id anywhere.
- Race start (0x7d6cc) plays id [0x491378] if ≥0. The same id goes to replay (0x922b4), the comms packet as a byte (0x19f738, sb +0x102), and 0x491e10.
- File resolution (0x13e5e8):
  - Strip "disc0:/PSP_GAME/USRDIR/", replace '/' with '\\', then look up in lba.dat. The lookup at 0x13ea18 is xbb_hash plus a binary search of the sorted LUT.
  - Then open `disc0:/sce_lbn0x%x_size0x%x`.
  - Case is preserved: lba.dat hash of `data\sound\bgm\race\SpeedySpeedBoy.at3` matches, the lower-case form does not.
  - **No fallback to the ISO directory**: a file missing from lba.dat fails to open.
  - lba.dat itself is loaded by name through the ISO (0x97e9c → 0x13e518 → 0x3180), so its directory-record size is what gets read.
- Stock race BGM sizes (lba.dat): SpeedySpeedBoy 387 404 B, rememberme 490 724 B, DancinInMyDreamsS 806 216 B. The codec is not confirmed: no IDSS .at3 has been staged. USRDIR/module has libatrac3plus.prx.

### Course-select BGM selector (shared by Bunta, Time Attack, comms and Legend/visit screens)
- Selector object (ctor 0xd34b4/0xd34fc) has +8 = v (selector value), +0xc = mode byte [0x4913a8], +0x10 = changed.
  - The ctor restores v from [0x4913a9] when mode == 2.
  - Update 0xd35b4 copies the 22-word table 0x211724 to the stack: −2 = skip, −1 = accept, n = unlock check.
  - Up (pad 0x10) / down (0x40) step v and wrap over 0..21.
  - Unlock check: 0x162a18(1, n, 2) with n = v (v<13) else v−1, using save bit-pairs at 0x4a35a0 (category 1: songs ≥12 need the HP unlock; n>21 is always locked).
  - The value is stored to 0x4913a9 (byte) and save word 0x4a35ec.
- Commit 0xd36dc: [0x491378] = v if 0≤v<21 else −1 (v = 21 is "NO BGM"); −1 when mode == 1. **Selector value v == sound id** for stock songs.
- Name widget 0x10e7c0 (vtable 0x24eca0, update 0x10e928):
  - It is the `PSP_BGM_select.ana` scene in bunta_crs_sel, ta_crs_sel, tushin_crs_sel and visit_rival_sel. All four copies are byte-identical.
  - It plays anim tab21[v] on layer 1 (tab at 0x21df10 = 1..12,1,13..20); v≤0 or v≥21 → anim 1 (NO BGM).
- Archive loads pass a size argument to 0x140b64: bunta 0x200000, ta/tushin 0x300000, visit_rival 0x280000. Keep the decompressed XBB below it.

### @ANA layout (decoded, `work/m7/tools/ana.py`, byte-identical round trip)
- File header: `@ANA`, 0x10, scene_tbl_off, 0x100, ntex, then the texture table at 0x20: ntex × {off, size, name[8]}, then the GIMs.
- Scene table: {n=1, pad, off, size, name[24]}. Scene body: {ntexref, texref[]}, padded to 0x20, then `@ANT`.
- `@ANT` header: ver 4, ncell, nframe, nanim, cell_off, frame_tbl_off, anim_tbl_off (relative to ANT).
  - Cell = 0x60 bytes {tex, ?, ?, ?, f32 u0,v0,u1,v1 in texels, geometry floats…}.
  - Frame = list of cell indices ending in −1.
  - Anim = {kf_off, nkf, f32 10.0, 0}; keyframe = {0, f32 frame, 0, f32 10.0}.
- PSP_BGM_select: cells 0/1 = frame 0 (panel and "▲▼ to change" hint); cell k+1 = frame k = anim k (k = 1 NO BGM, 2..20 = ♪1..♪19).
  - tex2 256×256 holds 16 rows; tex3 256×64 holds ♪16..♪19. Rows are 16 px, 4bpp swizzled, RGBA8888 palette.

### M7 patch (built, not yet run): 8 WMP race tracks as EXTRA songs
- `work/m7/tools/m7_boot.py` makes the PT_LOAD file-backed through .bss and appends a region at 0x553c80 (see work/m7/SPACE.md):
  - New sound table (ids 0..117) with 118 new R_MIPS_32 relocations.
  - Selector table, 30 words.
  - Paths `bgm/race/wmp_M04/M07/M09/M10/M11/M12/M13/M15.at3`, which become ids 110..117.
- Code edits: table base pairs; selector frame/table/wrap 22 → 30; commit (v 22..29 → id v+88); widget (v 22..29 → anim v−1).
- Selector order: ♪1..♪19, NO BGM (v 21, keeps saves compatible), ♪20..♪27 WANGAN MIDNIGHT 1..8. The new songs are always unlocked.
- The four course-select archives carry a new PSP_BGM_select.ana: tex3 256×192, labels cut from the stock glyphs, plus 8 cells/frames/anims.
- New disc files must be added with `iso_tool.py patch --add` so they get lba.dat records.
- WMP music: every Atrac3/*.at3 is ATRAC3plus (0xFFFE), 96 kbps, stereo, 44.1 kHz, with `smpl` loop points. M04…M15: 31–73 s, 383–878 KB.

## M8: Challenge Bunta restored + DEVIL Z CHALLENGE as a 9th main-menu item (static, 2026-10-15)
Tools, patch and builder: `work/m8/` (tools/m8_boot.py, m8_assets.py, verify_m8.py, test_make_iso.py; patches/030-m8-akio-menu.{json,asm}, swap_pairs.json; SPACE.md is now the cumulative free-space map). It supersedes the immediates of `work/m5/patches/010-devilz-challenge.json`: those sites are back to stock and the Akio values come from hooks.

### mode_select widget (0x110f80, draw 0x111458, set-index 0x11131c), solved
- The menu is a 9-row-capable wheel: 4 visible rows (layers 4-7 = label, 8-11 = banner, 12 = description, 1 = background), highlighted row 0x23c (0..2), top item = (cur − 0x23c) mod N, scroll anim 0x240 (±10).
- Anim groups in the stock ANA (8 per group): sel label 3+i, unsel label 11+i, sel banner 19+i, unsel banner 27+i, description 35+i; 43 locked desc, 44 background, 45/46 locked Bunta banner/label. Each item has 5 textures (Bunta: tex 3 banner, 6/9/12 label stack, 15 description).
- `ana.py` fix: the scene's texref list is padded to 16 bytes (not a fixed 0x20) and the file is padded to 16 at the end; mode_select (48 textures) now round-trips byte-identically.
- The ANA parser (vtable 0x248844, method 0x108) fixes offsets in place: no fixed texture/anim arrays, so 53 textures / 52 anims load (stock max seen: 51 textures).

### M8 design
- ANA: anims re-ordered into 9-wide groups (sel label 3, unsel label 12, sel banner 21, unsel banner 30, desc 39, then 48 locked desc, 49 background, 50/51 locked Bunta); item 8 uses new tex 48-52 (the build-8 Devil Z art), Bunta's tex 3/6/9/12/15 restored from build 6 (English).
- Code: cursor count 9 (0xd64f0), jump table bound 9 (0xd6a50) + new 9-entry table (entry 8 = 0xd6a98, car select), widget constants and mod 9 (0x1114ec, 0x111798, direction logic 0x111328-0x111394).
- Akio mode = game mode 2 + `akio_flag` byte 0x554180. `m8_commit` (0xd6b08) stores G+0 = 2 and flag = 1 for item 8, flag = 0 for every other item. `m8_init` (0xd64a8) puts the cursor back on item 8.
- Assets: **hash swap**. `xbb_hash` (0x140d6c) is the only name→file path for both XBB lookups (0x13e9a4/0x13ea18 → binary search on hash only, no strcmp) and lba.dat. Its `jr ra` jumps to `m8_hash`, which (flag && G+0 == 2) replaces 50 Bunta name hashes with Akio name hashes. The Bunta-flow code still builds Bunta names; the Akio files sit next to the originals under new names:
  - rivaldemo: talkTbl_AKIO_* (41), PSP_demo_vs_rivalname_AKIO.ana
  - game2d: PSP_game_rival_AKIO.gim, PSP_game_message_AKIO_UP.ana, rivalface.bin → PSP_g_k_30_face_akio.ana.gz
  - start2d: PSP_st_rivalname_AKIO.gim
  - bunta_crs_sel: PSP_AKIO_00.ana, PSP_course_select_AKIO.ana
  - disc: data/rivaldemo/char/PSP_akina07_akio.ana.gz (lba.dat via --add)
- Rival: `m8_setenemy` (the 3 jal SetEnemy in HSelectBuntaCrs) → enemy 6 when flagged, else stock 13/29/30. Race loader: `m8_lvl` (0x865a4) forces the [G+0x14] opponent-car path, `m8_tun` (0x86658) picks tuning record 30.
- Akio shares Bunta's level/save progress (G+0x438, save 0x4a35b5..). The Akio item is never locked; Bunta keeps its card lock.
- Load-size limits: rivaldemo 0x180000 (0x78208), game2d 0x1a0000, start2d 0x80000 (table 0x1e9748), bunta_crs_sel and sel_gamemode 0x200000. The M8 XBBs are 1.37/1.55/0.39/1.93/1.76 MB.
- Verified statically with unicorn: the original set-index matches the reference model for N=8 (192 cases) and the patched one for N=9 (243). The draw routine was also run (54 cursor/row/lock cases → expected anims), along with the hash swap (on, off and gated), all hooks after a simulated relocation at 0x08804000, and a synthetic ISO build. A PPSSPP run is still pending.

## Street Legends / rival slots (static analysis of build8 + M8 BOOT.BIN, M9, 2026-10-15)
Street Legends (公道最速伝説) = game mode 0, sources `a_visit.cc`. Tools: `work/m9/tools/` (rival_model.py dumps everything below from a BOOT.BIN; phaseA_sites.py checks the Phase A site list). Addresses are vaddrs.

### Flow and data model
- Sequences 0x28–0x32, handler 0x14a2d4, jump table 0x1e9a20: 0x28 course select (ctor 0xd376c, `data/visit/visit_crs_sel.bin.gz`), 0x29 rival select (ctor 0xdc794, `visit_rival_sel.bin.gz`, size 0x280000), 0x2a car select, 0x2b meet demo, 0x2c load, 0x2d race, 0x2f result, 0x30/0x31 win/lose demo (0xcbc78 / 0xcb2ac), 0x32 card.
- Enemy ids 0..30. Enemy table 0x213930 (31 × 32 B {dir, time, car, course, crsmdl, weather×3}). Read only through 0xde4e8/0xde500/0xde518/0xde530 and SetEnemy 0xde564 (6 relocated lui/addiu pairs). In mode ≠ 2, SetEnemy copies dir/time/course/crsmdl/weather into G; it always sets G+0x14 = car. Entry 31 cannot be added in place: 0x213d10 (per-course first id) follows.
- Slot → enemy: 0xde444(course, slot) = base 0x21390c[course] + slot, except Tuchi slot 4 → 28 (KEISUKE2), Tuchi slot 5 → 29 (TAKUMI2), Akina slot 5 → 30 (BUNTA).
  - Courses (id order MYOGI USUI AKAGI AKINA HAPPOU IROHA SHOMARU TSUCHISAKA, 8 = MIKI special): slots 3,3,3,6,3,3,3,6.
  - Slot-count tables (9 words, not relocated, read by lui/addiu): 0x2137e4 [3,3,3,5,3,3,3,4,1] selectable N; 0x1e80a8 [..6..6] widget shown; 0x213808 [..6..6] badge loop; 0x213d34, 0x2389e4, 0x209244 course-clear / default-cursor counts.
- "?" slots: the widget shows 0x1e80a8 slots but the cursor only reaches N. Locked extras draw anim 0 ("?"). Rival-select init 0xdcae8 raises N:
  - Akina → 6 if flag 0x8000.
  - Tuchi → 5 if 0x08000000, → 6 if 0x4000.
  - Base rivals are never hidden.
- Progress: G+0x74 = 0x490f7c u8[31]. Low nibble = losses (0xdea6c / getter 0xdead8), high nibble = wins (0xde944 / getter 0xdeaa8). Enemy 17 always reports 1 win.
  - Race end 0x7f158 calls win(e) or lose(e).
  - 0x490f9b is a padding byte, so it can hold enemy 31's progress; 0x490f9c is the clear count.
- Flags G+0x49c = 0x4913a4: 0x4000 KEISUKE2 beaten, 0x8000 TAKUMI2 beaten, 0x08000000 = enemies 0..27 all beaten.
- **Game clear**: load 0x148944. If all 31 enemies (incl. MIKI and BUNTA) are beaten, progress is reset, clear count G+0x94 = 0x490f9c is incremented (max 7), and from then on all three flags are forced on.
  - 0xcc17c (win demo) sets the ending flag when all 31 are beaten. 0xcc638 runs the ending path after Bunta while the clear count is still 0.
  - "Beaten Bunta" = wins(30) > 0 in the current loop, or clear count > 0.
- Save record S = 0x491ef8 (0x11704 B, checksum at +0x11704). Pack 0x148678 / unpack 0x148944:
  - S+0x1cc u8 = clear count.
  - S+0x1d5..0x1dc = 2-bit status per enemy (0 none, 1 lost, 2 won once, 3 won ≥2), loops `slti 0x1f` at 0x1487b0 / 0x148a90. Byte 7 pair 3 is unused, so enemy 31 fits without changing the save format.
  - The S+0x1cc..0x1d3 bitfields leave word bits 28–31 and 0x1d0 bit 31 free.
- Next-challenger chain 0xdeb70: 0x213ea8[e] (stack copy of 31). 28/29/30 are gated by the flags; locked returns 0.

### Rival select UI (visit_rival_sel.bin)
- Widget ctor 0x1102fc, update 0x11096c. ANA instances hold 128 runtime objects (0xe725c), so slots are code-limited, not ANA-limited.
  - Hard limit 6: loops `slti 6` at 0x1104e8/0x11050c/0x110ca8, badge objects s+6, spacing 60+8·(6−N) at 0x110a18.
  - The lock chain for the extra slots is at 0x110b50–0x110bd8.
- PSP_rival_select_01.ana: 34 anims. 0 = "?", e+1 = face of enemy e (tex 1..32 64×64), 32/33 = badges (won once / won ≥2), used at 0x110504/0x110c38/0x110c58. A face for enemy 31 collides with badge anim 32.
- PSP_rival_select_02.ana: 31 anims (big face = e). PSP_rival_select_03.ana: 31 anims (info panel = e).
  - Info panel textures: tex4 512×512 name rows (free: x256 y352–512, 5 rows), tex3 team rows (free y176–256), tex0/1 car-name rows.
- XBB is 2 150 144 B (build8) of 0x280000.

### Per-enemy tables (31 entries unless noted; all need an entry 31 for a new rival)
- Names:
  - 0x210cfc upper-case names, 32 entries ([31] BUNTA_CHALLENGE, chooser only).
  - 0x21112c lower-case names, 32 entries (portrait `PSP_%s%02d_%s`).
  - Both have R_MIPS_32 relocations.
- Talk chooser 0xcd7c0: id<31 → `talkTbl_<NAME>%02d` (00–06 meet, 07 after a loss, 0x0e after a win: 0x781cc); id ≥31 → Bunta-challenge files. Talk id = 0xdeb30(e) = identity table 0x213e2c (stack copy of 31); Bunta mode uses 31.
  - Other talk-id 31 checks: 0xd0070 (portrait), 0xd12e4 (VS-card skip), 0xcd15c (bg object).
  - The bg-object table 0x490484 [32 × {ptr,count}] is indexed by talk id. No static writer was found; it needs a PPSSPP write breakpoint at 0x08C94484.
- Demo crsID/flag 0x2111ac / 0x211228 (stack copies in 0xcfd58); portrait nn 0x211368 (stack copy in 0xd0058); VS name card `PSP_demo_vs_rivalname.ana` anim = talk id (31 anims, tex2 free x256 y352–512).
- Sound:
  - Rival theme 0x1eb888 (0x1ac50c, 1 pair); [31] is the engine table.
  - Default race song 0x1e62d4 (0x10a3fc, clamps e≥31 → 0).
- Race:
  - Tuning record 0x1f27cc ×12 B (0x70824, 0x86548 mode 0; 0x86664 mode 2; 0x19c468 comms).
  - Time table 0x1e6350[5][31] (0x10a42c, clamps).
  - Race init 0x103cc4: AI rid = 0x4b13e4 = enemy (31 forced in mode 2 → Bunta formula 0x104370). AI tables 0x1d2e58/0x1d7b80 (×12), 0x1d2fd0 (×8), 0x1d7f70 (×4); rid 16 has special code.
- HUD (race param +0xac = G+0x18, set at 0x84da0):
  - Face `PSP_g_k_%02d_<0x1f720c[e]>` from game2d → rivalface.bin.
  - Name `PSP_game_rival_<0x1f736c[e]>.gim` (stack copy at 0xbc0f8).
- Start card:
  - `PSP_st_rivalname_<0x1d10f0[e]>.gim` (3 pairs).
  - Round label 0x214670[e] (stack copy at 0xebf9c).
- Card encode (0x1187d0/0x119b80) and debug list (0xefccc) loop over 31; Akio can stay out of them.
- Side effect today: enemy 6 TOKYO (Akagi slot 0) drives car 12, which is the Devil Z since build 2.

### Phase A design (Akio = enemy 31, extra last slot on courses 0–7, unlocked by beating Bunta)
- Site list (90 entries, old bytes checked against the M8 and build8 BOOT.BIN, 0 mismatches): `work/m9/phaseA_sites.json`. Code: about 30 immediates, 16 retargeted pairs, 14 hooks into an M9 region after 0x554470 (M8 end). No overlap with M8's .text edits.
- Talk id 31 is shared and decided by mode (31 + mode 2 = challenge, 31 + mode 0 = Akio), so the bg table and the Bunta files stay untouched.
- New per-course table AKCRS[8] (dir/time/crsmdl/weather of each course boss); SetEnemy keeps G+4 for e = 31.
- AI alias: race-side rid = course boss (2, 5, 8, 13, 20, 16, 23, 27).
- Assets reuse M8 names where they exist: PSP_game_rival_AKIO.gim, PSP_st_rivalname_AKIO.gim, PSP_akina07_akio portrait.
  - New: talkTbl_AKIO00..23, PSP_g_k_31_face_akio, 7 portrait copies PSP_<crs>07_akio, and ANA anims in rival_select_01/02/03 + demo_vs_rivalname.

### Build 9 crash (PPSSPP, main menu): root cause and fix (2026-10-16)
- Symptom: `jalr t9` to 0 at 0x1868 (cell renderer 0x1540: `texobj = [scene+0x98][cell.tex]; texobj->vtbl[0x34]()`).
- Cause: the word after `@ANT` is the **texture-object count**. 0xeb8 allocates `[scene+0x98]` with that many objects. build 9's mode_select ANA still said 48 while cells of the new item 8 use tex 48-52, so the renderer read past the array (garbage/0 pointer) as soon as item 8 scrolled into view.
- Fix: `work/m8/tools/ana.py` writes len(texref) there (53). Only sel_gamemode.bin.gz changed (1 byte in the ANA); BOOT.BIN is unchanged.
- An emulated comparison of the draw routine (`work/m8/tools/cmp_draw.py`) found it identical to build 8 in all 630 non-wrapping cursor/row/scroll/timer cases, so there is no code-side cause for the reported glow offset / missed short presses. They are most likely side effects of the out-of-bounds texture objects. Re-check them on build 9b.
- `work/m7/tools/ana.py` has the same mislabel; it was harmless for PSP_BGM_select because that file kept 4 textures.

## M10: Akio mode gameplay (static, 2026-10-16; work/m10)
- **Bunta course select** (update 0x9bc70): selected level at obj+0x234; L/R = pad 0x200/0x100 (0x9c010/0x9c058); commit 0x9bf78 stores 0x234 into G+0x438[course]. G+0x438 is **persistent** (loaded from the save at 0x148ccc); save byte 0x4a35b5[course] = unlocked maximum. Panel widget level setter 0x10eef4 (obj+0x1e8; layer 0 anim by band, one star per level).
- **Win**: 0x7ef18 (mode 2) raises G+0x438 and the save byte, and sets the BUNTA_UP flag; levels ≥15 go to 16 at 0x7efb8. The common join point is 0x7f144.
- **Rival AI is a rail car**: per-slot objects at 0x4b14f0 + slot*0x2cc (slot 1 = rival, updated twice per frame by 0x10056c). Speed obj+0x44 is in km/h, distance per call = v/60/3.6 m. Per call the speed moves toward the target f3 by clamp((t−v)/3, ±1).
  - The target is profile byte 0x1d3528[row*1000 + segment obj+0xc] (km/h, 20..196) × the rival factor (Bunta: level-scaled A/B/C/E).
- **Player speed**: 0x4afacc is in m/s (×3.6 → km/h; the top-speed record at 0x10953c stores max(·, 3.6·v) at 0x4afc78). Player physics is a separate single instance at 0x4af8xx.
- **Paint**: the race car paint index is parts byte 9 → model byte 0x293 bits 1-3 (setter 0x625d8). RGB comes from per-car tables 0x21cdf4[car] → 36-byte entries.
  - The Devil Z (car 12, S15 slot) has 6 paints: 0 grey 828485, 1 white, 2 black, 3 **blue 000a55**, 4 yellow, 5 red.
  - Rival parts records are 0x1f27cc (12 B, byte 9 = paint), used by the race loader (record[enemy] in Legend, record[car] or m10 record in mode 2) and by 0x707fc (record[G+0x18]).
- M10 hooks (all gated on akio_flag && G+0 == 2):
  - m10_cl: Akio keeps the stored level.
  - m10_panel: 0 stars. The panel/hint art is also blanked (PSP_AKIO_00 tex0/1/2, PSP_course_select_AKIO tex 8).
  - m10_win: skips the level-up.
  - m10_ailvl: Bunta AI level = LEVEL (15).
  - m10_rb (0x1046ec): t = max(target·GAIN, min(p·RB_MUL + RB_ADD, target·CORNER_CAP if target < STRAIGHT)), capped at TOP; inactive below MINP. Only applies when rival id == 31.
  - m10_tun: record with paint 3.
  - Legend record 6 byte 9 = 3.
  - Talk fixed to MEET15/WIN15/LOSE15/TIMEUP15 (Akina variants kept) via a new swap table.
- Tunables live at 0x554470 (see work/m10/SPACE.md); the cheat file is work/m10/ULJM05093_m10_akio.ini.

## M11: Akio as enemy 31 in Street Legends (static + unicorn, 2026-10-17; work/m11)
Builds on build 10. Tools: `work/m11/tools/` (m11_boot.py, m11_assets.py, verify_m11.py, verify_widget.py, verify_assets.py, test_make_iso.py). Patch listing: `patches/050-m11-akio-legends.{json,asm}`. Region 0x5548a0–0x55520f (see work/m11/SPACE.md).
- **Slot**: Akio is the last slot on courses 0–7 (4th, or 7th on Akina/Tsuchisaka).
  - SlotToEnemy 0xde444 → h_slot (AKSLOT [3,3,3,6,3,3,3,6] → 31).
  - Shown counts 0x1e80a8 / 0x213808 are +1. The slot draws "?" until unlocked.
  - Unlocked = clear count G+0x94 > 0, or wins(30) > 0.
  - The rival-select init hook h_n (0xdcca4) raises N to AKSLOT+1.
- **Widget**: 7 slots (loop bounds 0x1104e8/0x11050c/0x110ca8, spacing 0x110a18). Badge objects move to s+7.
  - Badge anims move to 34/35 because anim 32 = e+1 is now Akio's face.
  - h_r7 maps slot label anim 9 → 22 (new 第七戦 in PSP_rival_select_00).
- **Enemy table** relocated to ET32 (6 pairs). Entry 31 is rewritten at every rival-select init from AKCRS[course]: the course boss record (2/5/8/13/20/16/23/27) with car 12 and course c. SetEnemy is unchanged.
- **Talk id 31** is shared and split by mode:
  - Mode 2 keeps the Bunta/Akio-challenge paths. h_talk 0xcd874, h_por 0xd0070, h_vs 0xd12e4 and h_bg 0xcd15c test `id == 31 && mode == 2`.
  - Mode 0 uses `talkTbl_AKIO%02d`. Name pointers 0x210d78 → "AKIO" and 0x2111a8 → "akio".
  - deb30 is made the identity function. Next challenger 0xdeb70 returns 0 for e ≥ 31.
- **Talk scene numbers** (all rivals): 0/7/14 = meet (fresh / lost to him / beat him), 1/8/15 = accept (E), 2/9/16 = decline, 3/10/17 = player won, 4/11/18 = player lost, 5/12/19 = rematch yes, 6/13/20 = rematch no, 21 = lose (other), 22 = yes, 23 = no.
- **Demo**:
  - h_demo: crsID = current course, flag = 1 → bg and portrait `PSP_<crs>07_akio.ana.gz` (8 loose disc files).
  - h_nn: portrait number 07.
  - VS card: anim 31 of PSP_demo_vs_rivalname.ana.
- **HUD**:
  - Face: 0x1f720c[31] (relocated word 0x1f7288) → "face_akio" → rivalface.bin PSP_g_k_31_face_akio.
  - Name: h_hud 0xbcd54 → "AKIO".
- **Start card**: h_st 0xec6b4 → "AKIO". h_rnd 0xec010 → round 7 = anim 15 最終戦.
- **Sound**:
  - h_theme 0x1ac510: rival theme 110 (wmp_M04).
  - h_song 0x10a410: default selector value 22 (WANGAN MIDNIGHT 1).
- **Parts**: the M10 Akio record 0x5544a0 (paint 3) is reached as record index (0x5544a0−0x1f27cc)/12 = 295527, without a table copy.
  - h_rec_a 0x7081c covers the model parts; h_rec_b 0x70928 uses TOKYO's model flags 0x1f2940[e*20].
  - h_ld 0x8654c covers the race loader.
- **AI**: no alias. Race rid 31 already selects the Bunta formula (difficulty factor 0x1d7cf8[31] = 1.0 at every setting).
  - m11_ailvl / m11_rb wrap M10 so that `mode 0 && G+0x18 == 31` gets LEVEL 15 + GAIN + rubber band, exactly like the flagged DEVIL Z CHALLENGE.
- **Progress / save**: Akio uses G pad byte 0x490f9b and save pair S+0x1dc bits 6–7 (copy loops 0x1f → 0x20).
  - The save pack's per-byte clear 0x1487a8 is NOPed (the bytes are pre-cleared at 0x148704). Without this, record 32 would wipe byte 7.
  - Akio is not part of the 31-enemy game-clear check.
- Verified with unicorn: SlotToEnemy 72 cases, SetEnemy/accessors, widget 0x11096c on all 8 courses (locked/unlocked/cursor on Akio), talk chooser filenames, demo hooks, save pack/unpack round trip, parts records, the AI rubber band (80 cases + step integration), and a synthetic ISO build. PPSSPP test pending.

## M12: build 11c fixes (PPSSPP-verified, 2026-10-17; work/m12)
- **9th menu item freeze.** In mode_select set-index (0x11131c), `sw zero,0x1f0(a0+4i)` and `sw zero,0x210(a0+4i)` clear two 8-entry per-item arrays.
  - For i = 8 the second store hits widget+0x230, the layer-system pointer, so the menu stops animating and ignores the d-pad (the cursor still moves underneath).
  - Both arrays are write-only, so both stores are NOPed (patch 040).
  - Lesson: when growing a list, grep for `sll idx,2; addu base` arrays inside the object, not only the count constants.
- **Memory.** Loaders allocate a fixed temporary buffer (rivaldemo 0x180000, menus 0x200000) via 0x140b64. If the allocation fails they return NULL silently, and a later texture lookup then crashes (rivaldemo: rain texture vt call at 0xd09d8).
  - The course-select scene keeps bunta_crs_sel resident while it loads rivaldemo.
  - Fix: Akio copies of large ANAs are XBB aliases (two entries, same bytes). The ANA loader relocates once and marks `@ANM`, then skips relocation.
  - Still tight: the after-race talk background is missing, and a Bunta race with the Devil Z as the player's car hangs (Devil Z race model is +96 KB over the stock S15).
- **PPSSPP testing.** Screen captures of a maximized PPSSPP can freeze, so run it windowed. F12 = ImGui debugger (CPU debugger, Callstacks); Ctrl+D = disassembly window.

## M13: English rival dialogue + load-buffer memory fix (build 12, PPSSPP-verified 2026-10-17; work/m13)
- Talk scripts: rivaldemo talkTbl_*.txt (826 files). The game parses them line by line (strtok "\r\n", strips the first and last char of each line), so stray quotes / trailing spaces on a line are harmless. Text unit = part of a line between the first `"` and the next `"`.
  Literal `\n` (backslash-n) = line break; window shows 2 lines (3-line pages scroll). "M" token inserts the player's car nickname from table 0x209758[35] (now English strings in the M13 region).
- Font class 0xb75bc (used by many menus): init 0xb77c4(obj, lst, size, cellW, cellH, texW, texH) assigns glyph cells in lst order (the numbers after '=' are ignored); 0xb79f8 loads N pages "<prefix>_%02d.gim"; 0xb8010 sets advance (+0x31c/+0x320); draw 0xb7bac matches 2-byte SJIS keys only, ASCII 0x20 = half advance.
  M13: hook h_ascii (0xb7d08 -> 0x555320): if cell width (+0x324) == 8, byte 0x21..0x7e draws glyph (byte-0x21) and consumes 1 byte. Talk + name fonts use 8x16 cells, 1 page, text origin x 0x70. Spaces stored as 0x8140.
- Loader 0x140b64(path, outsize*, max) allocates `max` BEFORE inflating; scene files are loaded while the previous scene is resident, so oversized maxima starved the heap (black after-race bg, Bunta+Devil Z race hang, black Street Legends rival select). M13 tightened 16 `lui a2,max` sites (rivaldemo 0x130000, visit_rival_sel 0x220000, visit_crs_sel/bunta_crs_sel 0x1c0000, game2d 0x180000, sel_gamemode 0x1b0000, result 0xd0000, sel_car 0x130000). **If one of these files grows past its max, raise the lui in work/m13/tools/m13_boot.py.**
- Heap: newlib UserSbrk 0x08d5a000-0x09edb000 (0x1181000); game heap = malloc(0x1140400) (size word 0x21b250).
- rivaldemo must be compressed with plain zlib (zopfli output failed to inflate in game).
- Tools: work/m13/tools/build_rd.py (English rivaldemo), m13_boot.py (BOOT), tok.py (unit parser), en_all.json + extra_tr.json (translations), validate.py/sim.py (line-length checks, 44 chars).

## M14: English menus, messages, HUD, cards (build 13, PPSSPP-verified 2026-10-28; work/m14)
- Message fonts: every font object built with init 0xb77c4 whose lst is msg/garage_msg/ms_error/lecture/cardtext/replay/lobbymes/message/driverfile is switched to cellW 8 / cellH 16 / 1 page (58 sites, found by scanning callers of 0xb77c4 for the "*_lst.txt" string). Advance overrides via 0xb8010 (lecture 14, cardtext 14, garage 12) -> 8. The M13 hook h_ascii then draws 1-byte ASCII.
  - New lst = 94 full-width ASCII keys (cells 0-93 = ASCII glyphs), U+3000 blank, button icons (凜 = circle, 熙 = cross), symbols, and all kana as narrow glyphs, so leftover kana and player names still show.
  - Fonts live in each scene XBB (and data/font/): replace <prefix>_lst.txt + _00.gim, drop _01.. pages. 0xb79f8 page count 0 means "load while %s_%02d.gim exists".
- ASCII space advance: 0xb7cd4 `lui v0,0x3f00` (0.5) -> 0x3f80 (1.0).
- UI strings: ~530 SJIS strings in .data rewritten in place (English always fits; tail-merged string at 0x1f595c skipped). Tools: tools/strings.py (relocation-based ref index), tr_a-d.json.
- Devil Z 6速 label = per-car 6-speed flag: byte at 0x1d1ff4+24*car, 0x1d2454+24*car, 0x1dc474+24*car (word before each engine record) and 0x1d0db8+8*car. Cleared for slot 12.
- Card viewer (card/view/card_viewer.bin): cardtext.txt (185 cards, [INFO]/[TEXT]/[HINT] blocks, CRLF SJIS) + cardtext font. **The viewer drops glyphs past about 180 per text**, so keep each text at 165 non-space characters or fewer and 31 characters per line. Card type/name labels are pre-rendered lists PSP_lec_w_font01..06.gim (16-px rows; 02_x columns split at x=80, others at 128).
- Texture re-lettering pipeline: specsrc/*.py -> texspec/*.json -> tools/build13.py.
  - It applies to identical textures in other files by md5.
  - ANA cell UV rects (tools/ann.py) give exact label boxes.
  - Hint bars are found by orange-text mask.
- Akio course-select hint: PSP_course_select_AKIO.ana is a small own ANA (header + scene + own hint GIM). Its other texture offsets are negative u32 deltas into PSP_course_select_00.ana in the same XBB buffer. This works in PPSSPP and costs 25 KB instead of 146 KB.
- Devil Z race model: s15_200envbody_race.gmo replaced by the empty stub s15_222gk_race.gmo; race.bin is back to stock size + 448 bytes.
- PAUSE descriptions (PSP_PAUSE.ana #2-4, #6-7) live in game2d.bin.gz and as a loose game2d/pause/PSP_PAUSE.ana.

## M15: Aura effect + aura cards (build 15, PPSSPP-verified 2026-10-28; work/m15)
- **Renderer (R2, `m15/r2/AURA_RENDER.md`)**: the game ships the arcade aura system (Versus intro only). `m15/i1/m15_aura_boot.py`
  re-enables it in every race: AURA_ID u8 @0x555370 (1 blue 2 red 3 yellow 4 green 5 purple 6 white, 7 rainbow), FORCE u8 @0x555372 (debug).
  h_create sets AURA_ID = FORCE ? FORCE : (Versus ? 0 : G+0xa7 & 7).
- **Per-car aura**: garage entry (S+0x11580 + 8*i) byte 7 bits 1-3 (free). Unpack 0x156ac4 hooked at 0x156c7c -> G+0xa7 (0x490faf, unused pad);
  new car 0x157180 hooked at 0x1574a0 clears the bits. Garage scene state 1 (car list, jump table 0x1e9d80) -> h_g1: SELECT (0x1) cycles owned
  auras + none, message via window obj+0x20c (0x17d544 text, 0x17d1b0 show, vt+0x10 update, vt+0xc close). Hint 273 repointed (0x2394e4).
- **Cards**: 0-based ids 185..190 (1-based 186..191). Card manager re-laid out for 191 ids (flags u16[] @0, TEXT 0x180, INFO 0x778, HINT 0xd70,
  buf 0x1368, tail 0x1568..; alloc 0x14f8 -> 0x15a0 at 6 sites; 50 field offsets remapped in 0x14d600-0x14ec00).
  Bounds 0xb9 -> 0xbf in manager/wrappers/viewer only (collection % 0x147c44/0x190734/0x1990f0 and comms trade keep 0xb9).
  Save card table u16 grows into the free gap S+0x1a2..0x1ae (saved and reloaded fine).
  Viewer: 20 pages (constants 0x150994.. ), page count digits 0x14f0a4/0x14f0b8 ("/20"), thumbs bound 0x14f830 (1-based <0xc0),
  name cells for ids >= 0xb9 via hooks 0x14dadc / 0x14dd1c (font06 col0 rows 11-15, col1 row 12), widths via 0x14decc hook,
  category 7 = "Aura Card" (font01 row 7) via 0x14e4cc hook. card_probability direct ids up to 0xbf (0x18ac84 -> 0xc0).
- **Unlocks**: Street Legends specials in result.bin.gz card_probability.txt ([08] 187, [28] 188, [14]/[15]/[16] 189 # IROHA,
  [11]/[15] 190 *_2 11 15, [30] 191). Blue: result 0x18bb18 -> h_spec: mode 2 + Akio flag 0x554180 + win + not owned -> special 186.
  Mode 2 shows no card screen after a loss, so the Blue path needs a real win to test.
- **Data**: card/pic/PSP_186..191.gim + PSP_s_186..191.gim (new disc files), card_view_s18.bin +5 thumbs, new card_view_s19.bin,
  cardtext.txt +6 [TUN] blocks in card_viewer.bin and result.bin.gz. Art from `m15/i1/aura_art.py`; data from `aura_assets.py`; build13.py hook (AURA=1).
- Caution screen fix: PSP_CAUTION.ana#0 cell 0 is x 64..447 only; cell 1 (448..511) is drawn elsewhere.

## M16: 30 extra race songs (work/m16, 2026-10-28)
- BOOT (`m16_boot.py`, on the build 15 BOOT): new sound table 148 x {path, flags} at 0x555b90 (ids 118..147 =
  `bgm/race/ss_NN.at3`, flags 0x101, 148 new R_32 relocs), selector table 60 words at 0x556030; play()/stream
  bases 0x1abab4/0x1ababc, 0x1abc28/0x1abc2c; BgmSel::update frame 0x108, 30 pairs, wrap 59/60; commit
  0xd3704 sltiu 38 (id = v+88); widget 0x10e968 slti 0x3c (anim v-1); bunta_crs_sel load max 0x1d0000 (0x9b91c).
- **@ANA: ANT+4 is the texture-slot count** (ana.py calls it 'ver'); it must equal ntexref. A 5th texture with
  ANT+4 = 4 makes cells on it index past the slot array -> null vtable crash at 0x1868.
- PSP_BGM_select gets tex4 256x360 (30 rows of 12 px), cells 30..59, frames/anims 29..58 (make_bgm_ana16.py).
- **Race BGM is loaded whole into RAM** (PPSSPP shows ALL_DATA_LOADED for stock songs). 4-6 MB files never start
  and the race hangs on RETIRE. 1.4 MB (85 s at ATRAC3 132k) is proven OK. sceAtrac accepts ATRAC3 (0x270).
- **Looping**: a `smpl` loop starting at sample 0 is ignored (song plays once). Use loop start 2048 (end = n-1) and
  fact = (n, 1024) with the encoder's 1024-sample delay left in the stream.
- **New disc files need an ISO directory record**, not only an lba.dat record: the game stats the file before
  loading it. iso_tool (build16d copy) adds records for lba-only files and grows/moves a full directory
  (fixes '.', the parent record and the L/M path tables).
- Build 16d = PPSSPP-verified: ♪28/♪42/♪57 play and loop in Time Attack, Devil Z Challenge and Street Legends.
- `at3enc.py`: own ATRAC3 LP2 encoder (QMF via adjoint of ffmpeg iqmf, MDCT window 0.5*(sin+1), odd bands reversed,
  SCALE -1/128, delay 1024, VLC tables from libavcodec, RD bit allocation). ~18 dB SNR on dense Eurobeat.

## M17–M33 summary (builds 17–33, 2026-10-29..31; work/m17..m33, PROJECT.md has per-build detail)
### Rebrand / release
- Game renamed "Initial Z Street Stage+" (original logo, PARAM.SFO title, ICON0/PIC1/ICON1.PMF, save icons + 27 save-list strings). Release = kit zip (sector diff + apply_kit.py) that rebuilds the ISO byte-identically from the stock ISO; MAKE_KIT.bat verifies md5.
### Aura v2 (M19–M22)
- Rival auras: Akio rainbow pulsing (Challenge), Bunta small red at Challenge level ≥11 (m19/ab). Race-start flare scales by stage.
- Aura tuning (m20/g): SQUARE on Garage > Change Car opens an 18-step panel (6 colours × 3 stages 0.6/1.0/1.6×), 1 Tune Up card (id 0xad) each, progression-only. Progress in garage entry word0 bits 18–22, colour byte7 bits 1–3. SELECT cycles unlocked colours.
- In-car fix (m22/ac): player aura hidden within 3.2 m of the camera (aura placed with last frame's camera → near side fills the screen at ~180 km/h). Tunables 0x563940..
### CAR DATA (m19/c)
- TRIANGLE on Change Car: 36 cars × 3 pages × 10 courses (top-speed rows per course/direction; Wangan rows separate). 8x12 font cdsm_00.gim (m31/ui).
### Car #36 = Devil Z (m26/car36)
- Car id 35 (0-based). Every per-car table extended to 36 (incl. paint 0x21cdf4/0x21cea4/0x21cf34, paint/parts ptr table 0x208bd4 relocs, rival data 0x1d284c, 0xc0968, 0x215c24, 0x21e910, 0x1bd454, 0x1d11d4, 0x1cebec, 0x1f20fc, switch 0x1bc274, aura limit). Name slot 73 must stay BLANK (stock overlay layer points at it) → Devil Z name in slot 74. TA records: car 35 shares car 12's slots. Save migration via marker S+0x1cb.
- Unlock (m33/unlock): NISSAN list shows Devil Z only after an Akio Street Legends win (per-course or old shared counter) or if owned; Devil Z Challenge menu locked until Bunta beaten/game cleared.
### Wangan as its own course + Akina Snow (m27)
- Course 8 (crsmdl 16/17) is the unused arcade Akina Snow (Miki) — no PSP assets. Wangan runs as **engine course 4 / crsmdl 8/9** with flags WSEL (menu), RW (race is Wangan, 0x56dbd1), WFLAG (file switch). 9-item carousels in TA/SL/Bunta/Versus; records in Happogahara's unused day slots.
- **Only rewrite DISC paths** (section-bundle prefix `…/vh2/vh` + happou_night_data/start_data1/2 → wangan_*). Inner XBB entry names are looked up by basename — renaming them made every lookup miss (skyline but no road/collision). Also every `crsmdl÷2` site must not see 18/19 (reads past 9-entry tables) → keep crsmdl 8/9 and drive by flag.
- Path apply re-runs on every course load (m31/wfix).
- Akina SNOW: third weather item; snow-recoloured akina_snow*/akina_snown* archives; runs on the WET path with tyre spray (0xf4bac/0xf4d4c) and wet streaks (0xf54d0) skipped; rain mesh reshaped into flakes; grip rows 16/17; records course-8 slots.
- Miki (enemy 17): Akina SL 8th slot on SNOW; the stock card parser skips row 17 → use Kai's row 16 or the card loop freezes.
### Versus (m28/vs, m29/vs)
- Host writes 0x57 into rule-packet pad byte 0xfb (obj+0xc0) for Wangan; guest sets RW/WSEL. Name hook 0x1a0200 (short-name table 0x240ef4).
### Music
- Race BGM ss_01–30 streamed from disc (m22/mu hooks 0x1abae0/0x1abc78, 256 KB buffer) → full songs. Project D Web BGM list 59 entries (m27/hpbgm).
### Heap safety (m28/w, m32/heap) — READ BEFORE ADDING CODE
- newlib UserSbrk heap (_sbrk 0x366d4) was being created at 0x08D69000 inside the appended remix code → silent corruption. BOOT28W reserves the remix range ("RemixRegion") at module start (hooks 0x3610c / 0x3672c); BOOT32H raised the ceiling to **0x5B0000** (heap size word 0x21b24c 0x4604→0x4528 KB; heap now 0x08DB4000–0x09EFE000). Status word 0x08D772DC = 1.
- Free code region after build 33: 0x576a00–0x5AFFFF. Keep every new byte below the ceiling.
### Street Legends fixes
- Akio post-race freeze: rival rows exist only for 0–30 → card row + post-race music index clamped for enemy 31 (m20/h, m20/q).
- Akio per-course wins/losses S+0x1b0..0x1b9 (m31/akio). Area face row 8 slots incl. Akio/Miki (m31/faces).
- Wangan walls: collision side-layer cells must cover the whole walkable area (deck + wall bands) or the car enters a lost-ground state (keeps speed, rolls, pause blocked); end caps need asphalt run-off + bevelled wall cap.
### BOOT chain (build 33)
26D → crs9c → c2p1/c2p2 → hpbgm → snow → final → slw → vs → w(heap) → 29V → 29S3 → 30M → ui → akio → wfix → faces → heap(32H) → unlock(33U).
