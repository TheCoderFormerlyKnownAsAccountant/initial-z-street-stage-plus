# M45 RIVALS: every WMP rival in Street Legends + all-clear gate (build 45)

- Build: `python3 tools/assets45.py` (files/, add/, anims45.json, prev/assets45.png), then
  `python3 tools/m45_rivals_boot.py ../../m44/video/BOOT44V.BIN BOOT45R.BIN --json patch45r.json`
  (`--no-hakone` drops the Hakone lineup and its gate term, for a chain without M45 HAKONE).
- Verify: `python3 tools/verify45.py ../../m44/video/BOOT44V.BIN BOOT45R.BIN patch45r.json` → ALL OK (90 checks, unicorn on the relocated image). The builder also asserts that every HI16 is paired with a LO16 that has the same carry.
- **BOOT45R.BIN md5 b29c34d2a33a0a5d3ae25d22cefc4b12** (BOOT + EBOOT). Region 0x597000–0x59893f; 30 patched words; 1215 code words; +620 relocs.
- Chain order: polish (0x594000) → **rivals** → hakone (0x5a0000). The builder needs memsz ≤ 0x597000 (or that region empty). It checks every hook head it replaces and stops if one moved.
- Manifest: `manifest45r.json`. It replaces 4 files (visit_rival_sel, rivaldemo, game2d, start2d; built on m42/wmpart/files = build 44) and adds 36 talk portraits.

## Roster
- **15 WMP drivers.** These are all the WMP roster rivals that have a bust in BUILD.DAT: the M40 7 plus 8 new ones.
- **Not included (no bust in the game data):** Yamashita, Sonoda, Tezuka, Motoki, Yamanaka, Yamamoto and Maki.
  - In-car faces 1298–1332 might cover them, but that mapping is unproven.

| Driver | Bust | WMP car → Initial Z car | Donor enemy |
|---|---|---|---|
| Harada | 1738 | Z31 300ZX → 180SX | e1 |
| Gacchan | 1723 | Celsior → Altezza | e21 |
| Oki | 1722 | FD → FD (Ota's paint row) | e3 |
| Makoto | 1741 | Z32 → FD (Masaki's row) | e4 |
| Tomoya | 1736 | R32 → R32 | e7 |
| Goto | 1730 | GT-R "ACE" → R32 | e14 |
| Toshiyuki Jojima | 1724 | FC → FC | e25 |
| Kei | 1728 | Supra → R32 | e22 |
| M40 drivers | — | unchanged | e10/24/26/27/11/8/12 |

## Lineup
Page 2 per course shows the drivers below, then Akio.

| Course | Page 2 drivers |
|---|---|
| Myogi | Harada, Gacchan, Oki, Makoto |
| Usui | Gacchan, Oki, Makoto, Tomoya |
| Akagi | Harada, Tomoya, Goto, Masaki |
| Akina | Makoto, Goto, Masaki, Ota, Eiji, Reina |
| Happogahara | Oki, Ota, Eiji, Jojima |
| Irohazaka | Masaki, Reina, Jojima, Kei |
| Shomaru | Goto, Eiji, Kei, Hiramoto |
| Tsuchisaka | Reina, Jojima, Kei, Hiramoto, Kuroki, Shima |
| **Hakone** (own lineup, no page toggle) | Goto, Reina, Jojima, Kei, Hiramoto, Kuroki, Shima + Akio |
| Wangan | unchanged (M40: 7 WMP + Akio) |

That is 36 page slots + 7 Hakone slots. Every driver appears at least once.

## How it works
- **Page 2.** In the rival select, **L or R** switches to page 2 and back. It re-enters sequence 0x29 through the same exit path as BACK.
  - Page 2 opens once all stock rivals of that course are beaten (stock area eval), or after a game clear, or once a page-2 rival there is already beaten.
  - The controls bar now reads "L/R Wangan Rivals".
- **Context.** The page context is: Street Legends and PG set. PG/PGC live at 0x597010/0x597011. The area-select ctor clears PG.
  - Hakone: the rival-select ctor sets the page context automatically for course 4 + RW + **HK (0x5a0010) = 1**.
  - Wangan (HK = 0) refuses the page context, so WRIV/M40 behave as in build 44.
- **Donor enemies.** Each driver runs on one unique donor enemy, which supplies the AI level, the HUD face number (`PSP_g_k_<e>_face_<low>`) and the portrait nn.
  - Rival-select ctor: the donor's 5 name-table entries point at the driver. Stock and M40 names are restored first, so M40's Wangan swaps still win in their own context.
  - Anims remapped: _01, _02, _03 and VS.
  - SetEnemy copies dir/time/course/crsmdl/weather of a stock rival of that course and sets the driver's car. G+0x18 stays the donor.
  - Hakone races: course 4, night, crsmdl 8+dir, dry.
  - Parts, dress-up and model-flag rows come from the car's donor (the M40 method).
  - The talk demo runs on the race course: `PSP_<crs><nn>_<low>` portraits (36 adds) and that course's stock background. Hakone uses the Wangan night background.
- **Progress.** One bit per page slot.
  - Storage: XB = S+0x1c3..0x1ca (courses 0–7) and S+0x1c1 (Hakone). These are unused bytes of the S card-table gap that pack/unpack never touch. Old saves read as 0.
  - Wins getter (whitelisted callers only: rival select, widget, talk/demo scene choice) returns the bit.
  - Race win sets the bit. A loss is a no-op. Next challenger is none.
  - The donors' stock progress, the WGP bytes and the game-clear check are never touched by page races.
  - Losses getter keeps the donor's stock nibble, so the "lost before" talk variants may not match.
- **Buffers** (all still below stock): visit_rival_sel 0x260000 (raw 0x255d00), rivaldemo 0x140000 (0x13c500), game2d 0x190000 (0x186700).

## All-clear gate
Applies to the DEVIL Z CHALLENGE menu item: all 4 M33 lock checks (draw, description, cursor, OK).

- **ALLCLR_F** at 0x597640 returns v0 = 1 when **FORCE (0x597013) ≠ 0**, or when all three of these hold:
  - stock: clear count > 0, or every enemy 0..30 incl. Bunta has a win (Miki counts as beaten, as in the stock getter);
  - all 7 Wangan rivals beaten (WGP);
  - every page slot of courses 0–7 and the Hakone lineup beaten (XB == PMASK).
- It clobbers only at/v0 and needs a `jal` (it saves t0/t1 itself).
- Akio is not required: his Street Legends slots still unlock after Bunta, and the Devil Z is still buyable after an Akio win.
- **Cheat for the cheat file:** FORCE byte, CWCheat `_L 0x0059B013 0x00000001`, unlocks the gate.
  - "All page rivals beaten" = 8-bit writes at S+0x1c3.. = 0x08C960BB..C2 (CWCheat 0x004960BB..C2): 0F 0F 0F 3F 0F 0F 0F 3F.
  - Hakone: S+0x1c1 = 0x08C960B9 (CWCheat 0x004960B9) = 7F.

## QA checklist (PPSSPP)
1. Street Legends: any course rival select. The bar shows "L/R Wangan Rivals". L/R does nothing until the course's stock rivals are beaten (or after a game clear). Then page 2 shows the WMP faces plus Akio "?"/face; L/R goes back to page 1.
2. Page 2: faces, big face, info panel (name, car row, stars), talk (portrait, English lines, speaker name), VS card, start card, HUD face/name. Race runs on the selected course with the driver's car. Check Akina and Tsuchisaka (6 drivers + Akio, 7 slots).
3. Win against a page driver: badge on page 2; the donor's stock slot on page 1 is unchanged. Save/reload keeps it.
4. Hakone (with M45 HAKONE): the 7-driver lineup + Akio. Races load Hakone at night. Wangan still shows its M40 lineup and WGP progress.
5. Devil Z Challenge stays locked after Bunta until every rival is beaten (or FORCE is set).
6. Memory: watch for memory errors on rival-select entry (buffer +128 KB), talk (+64 KB) and the race (game2d +64 KB). The Bunta race with the Devil Z was the historic memory edge.
7. Regression: page 1 everywhere, the Miki slot, the Akio slots, area face rows, TA/Versus/Bunta.

## Known / open
- Bust 1738 is shown as "Harada" by the M40 gojūon mapping, but it looks female. Check it in WMP story mode (M40 QA 1).
- Hakone rival pace: drivers outside the WRIV list use the Hakone profile without per-rival wspdB scaling .
- Card rewards after a page race are the donor's stock rows.
- Hakone area-clear mark uses WRIV's Wangan evaluation.

## QA r1 fix: R did not switch pages (build 45 QA)
- Static checks rule out a wrong mask or another handler: R = 0x200 in the game's pressed word 0x263e74 (Bunta course select uses the same bits), and no other code reads or clears that word. The only places a press is lost are presses during the page fade-in (the scene is not in state 1 yet) and taps shorter than one pad poll. That fits an R pressed right after the L toggle.
- Fix: h_page also takes its own edge from the held word 0x263e70 (PREVH = STATE+4, 0x597014). The rival-select ctor latches the buttons still held, so the toggling button doesn't ping-pong, while a different button held through the fade still toggles.
- The restore code is now a shared subroutine (smaller), and the region end is kept at 0x59893f. verify45.py: 94 checks ALL OK on both inputs.
- BOOT45R (on 44V) md5 714c904034f31d674b43f73927035dad; **BOOT45PR (on 45P 2f8380fc) md5 858762dbb62df6d87ad817bf1b9d8ac9**.

## QA r2 fixes
- **Talk grammar.** `tools/talkgrammar45.py` walks every generated table (384: 15 WMP sets plus Akio) the way the interpreter consumes them, against all 744 stock tables in the same rivaldemo. It checks token kinds and kind bigrams ⊆ stock, window/speaker before text, every page ends W_n N, ≤ 3 lines/page, ≤ 44 chars, windows closed before E, speaker/pose in range, and strict quoting/CRLF.
  - Result: **0 failing**. GOTO11 has the same skeleton as stock KENJI03 (P_ C_ *_ T W_ N … K_ E). W_0/N is the stock page end; D_ is optional (KENJI03 and KEISUKE21 have none).
  - So the generator was left as is. The blank post-race text is not a script problem: it also hits Akio's stock-style M11 tables on Wangan (M40 r4), and only happens with demo course 4 + RW (Wangan/Hakone). Still open: a runtime A/B with Happogahara Daiki (course 4, no RW) post-race.
- **Memory.** Identical talk tables are now XBB aliases (data stored once; entries are 0x80-aligned). rivaldemo raw is **0x12f100** (gz 227251 B, md5 7af00f9f…) and fits the **stock 0x130000 buffer**, so the +64 KB raise is removed (lui 0x13 kept at 0xcb4c4/0xcbeac/0x1183bc/0x78208).
- **BOOT45PR** (on 45P 2f8380fc) md5 **5ce2541ab5ce853872b321638dc78357**, region unchanged 0x597000–0x59893f. verify45: 94 checks ALL OK.

## QA r3 (all SL post-race talk blank) — aliasing ruled out statically
- The talk loader 0xcd7c0 looks the table up (0x13e968 size, 0x13e8b0 pointer → XBB base + entry offset; read only), mallocs size+1, **memcpy**s it (0xcdb14), NUL-terminates the copy and tokenises **the copy** (strtok "\r\n", 0x3f588). Nothing writes the XBB blob, so aliased talk entries can't corrupt each other.
- `tools/emu_talkload45.py BOOT rivaldemo.bin.gz` runs the game's own lookup/copy on all 1210 talkTbl names: 0 mismatches on both the aliased and the un-aliased file (Bunta 03/04, Kenji 04, Goto 11 shown). `talkgrammar45.py`: 0 failing.
- The 0x140b64 loader decompresses (0x36bf8, checks ISIZE) into the reserved block, then shrinks it to the decompressed size (0x16f98). The fit 0x12f100/0x130000 needs no slack.
- The r2 → r3 BOOT45PR change is only the 4 rivaldemo-buffer luis (0x14 → 0x13).
- The pre-M45 Wangan WMP blank happened on build 40–44 without aliasing, so aliasing does not explain it.
- A/B set for QA:
  - **A** = BOOT45PR 5ce2541a… + files/rivaldemo (aliased 0x12f100, 7af00f9f…, buffer 0x130000) = r3.
  - **B** = BOOT45PR_rd14 858762db… (= the r2 BOOT) + files_noalias/rivaldemo (0x13c500, 76e9f6bd…, buffer 0x140000) = the r2 config.

## M48 progression (build 48; chain patch `tools/m48_rivals_boot.py IN OUT --json patch48r.json`)
- Input: BOOT46F (0d76eadf, the build-47 BOOT). Any BOOT with the M45 region intact and 0x598850..0x59893f zero works. **BOOT48R md5 70f5c3c5d392c9387d6446dc3381f3a4.** The movie patch's MBGM_ID word is outside this patch (0x580690), so BOOT48M can come before or after.
- **Takumi rule.** TK = clear count > 0, or Takumi (enemy 13, Akina) wins nibble of G+0x74+13 = 0x490f89. That byte is saved through the stock S+0x1d5.. status pairs, so old saves that already beat Takumi unlock at once.
  - Page 2 on every course opens with L/R only when TK. This replaces the per-course rule; it is patched in place in hp_open, keeping the same relocation kinds.
  - Wangan and Hakone lineups (course 4 + RW): until TK every slot draws the stock locked face "?" (0x110b50 → h_lk48 → 0x110be0) and CIRCLE does nothing (0xdcde8 → h_cf48).
- **Akio rule.** Unchanged, and checked to be the same everywhere: M11/M33 rule (clear count > 0 or Bunta wins > 0) on every course, page 2, Wangan slot 8 and Hakone. On Wangan/Hakone he also needs TK.
- **Devil Z Challenge gate.** ALLCLR_F unchanged.
- **Verify:** `RULE48=1 P48=patch48r.json python3 tools/verify45.py BOOT46F.BIN BOOT48R.BIN patch48r_verify.json` → 101 checks ALL OK (verify48.log). That includes the progression matrix fresh / Takumi / Bunta / both / cleared: page 2, Wangan lineup lock, Akio on Wangan and on Myogi, CIRCLE.
- **Cheats** (8-bit OR, as in the cheat file):
  - Takumi on Akina beaten: `_L 0x70494F89 0x00000010`
  - "All Street Legends rivals beaten" already ORs 0x494F7C..0x494F9A, which includes Takumi (0x494F89), so it still opens everything.

## M49 Devil Z Challenge gate = one Street Legends Akio win (build 49; `tools/m49_rivals_boot.py IN OUT --json patch49r.json`)
- Input: BOOT48M (86664dd5). **BOOT49R md5 56ddc99c6d556f3ad941a118d9661b96.** Only bytes 0x597660..0x5976c7 change (16 words of ALLCLR_F, rewritten in place). No relocation entries are added or moved; every HI16/LO16 word keeps its kind with the same hi 0x49. The gate sites (0x5764ac / 0x576548 / 0x5765b0 / 0x576614, which call g0..g3 → ALLCLR_F 0x597640) are unchanged. Chain: 48M → 49P → 49R → 49A.
- Rule: FORCE (0x597013) ≠ 0, or any wins nibble of AKP[0..9] = S+0x1b0..0x1b9, or the pre-M31 shared Akio counter G+0x93.
  - Courses 0–7 and page 2 use AKP[course]; Wangan and Hakone use AKP[9]. These bytes live in the save, so old saves with an Akio win unlock at once.
  - The Takumi rule (WMP drivers) and the Bunta rule (Akio) are unchanged.
- Verify: `RULE48=1 RULE49=1 P48=patch48r.json python3 tools/verify45.py BOOT48M.BIN BOOT49R.BIN patch49r_verify.json` → 102 checks ALL OK (verify49.log). Gate cases:
  - locked: fresh save; Bunta only; Akio loss only; all rivals or game clear without an Akio win
  - UNLOCKED: one Akio win on Akina / Wangan / Hakone / page 2 Irohazaka, through the real race-end win path; old counter; FORCE
- Cheat: "Unlock Devil Z Challenge" = Akio beaten once on Akina, persists in the save: `_L 0x704960AB 0x00000010`. The M33 rule also makes the Devil Z buyable after this. FORCE (`_L 0x0059B013 0x00000001`) still works.
