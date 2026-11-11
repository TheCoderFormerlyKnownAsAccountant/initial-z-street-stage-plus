# M40 WMPCHAR: Wangan Midnight Portable drivers as Wangan's Street Legends lineup

Option A (Daniel). Chained on BOOT39S (85ff0742, snow fork update) -> **BOOT40C.BIN (md5 033a2276a223e02067eb4c240723ef27)**.
Not tested in PPSSPP yet: everything below was checked offline (unicorn + parsers).

## Lineup (Wangan SL area only; Happogahara and every home course stay stock)
| Slot | Enemy id | WMP driver (bust) | Car in race | Name shown |
|---|---|---|---|---|
| 1 | 10 | Hiramoto (1739) | R32 (own) | Koichi Hiramoto |
| 2 | 24 | Masaki (1742) | FD (own) | Masaki |
| 3 | 26 | Reina (1745) | **R32** (was Evo V) | Reina Akikawa |
| 4 | 27 | Eiji (1720) | Evo VI (own) | Eiji Kamiya |
| 5 | 11 | Kuroki (1727) | **R32** (was Evo III; stands in for his R33) | Kuroki |
| 6 | 8 | Ota (1721) | FD (own) | Ota |
| 7 | 12 | Shima (1732) | FC (own; stands in for the 964 Blackbird) | Tatsuya Shima |
| 8 | 31 | Akio | Devil Z | unchanged |

Enemy ids, WGP progress bytes, save layout and the M37 pace rows are unchanged, so existing Wangan progress carries over.

## Art (only WMP's own drawings, cropped / scaled / graded / quantised / framed)
- Source: WMP BUILD.DAT busts 1719–1745 (240×232). Grade: saturation 0.85, contrast 1.08.
- Rival-select small and big face: tight 48×64 head crop on white. Area face row: 44×58. HUD: 60×44 forehead-to-chin close-up inside Akio's speed-line frame (64 colours, because game2d is full).
- Talk portrait: full bust, 10 identical poses on the Bunta layout.
- Name labels use the remix's existing English styles:
  - info panel / VS: DejaVu Sans Bold Oblique, white; VS adds a dark outline
  - HUD: DejaVu Sans Bold with outline
  - start card: DejaVu Serif Condensed Bold with navy outline
- Previews: `prev/assets40.png`, `prev/portraits.png`, `prev/faces48.png`.

## Mapping evidence (bust -> driver)
- The 27 busts follow the gojūon order of name plates 1775–1805, skipping 山下 / 山中 / 山本 / リカコ. All 5 women land on female busts.
- The portraits confirm it: Masaki (1742) and Ota (1721) wear RGO jackets, and Kuroki (1727) wears the Flat Racing badge.
- Still a PPSSPP check (QA 1). Hiramoto, Reina, Eiji and Shima rest on the order only.

## Files
- **Tools:** `tools/art.py` (crops), `tools/talk40.py` (dialogue), `tools/assets40.py` (writes files/, add/, anims40.json, prev/), `tools/m40_boot.py`, `tools/verify40.py`, `tools/verify_assets40.py`, `manifest40c.json`, `patch40c.json`.
- **Replaced:**

  | File | Raw size | Buffer |
  |---|---|---|
  | visit/visit_rival_sel.bin.gz | 0x237000 | buffer raised 0x220000 → 0x240000 |
  | visit/visit_crs_sel.bin.gz | 0x1c9400 | buffer raised 0x1c0000 → 0x1d0000 |
  | rivaldemo/rivaldemo.bin.gz | 0x129a80 | 0x130000 |
  | game2d/game2d.bin.gz | 0x17fe80 | 0x180000 (**0x180 bytes left**) |
  | game2d/start2d.bin.gz | 0x65780 | 0x80000 |

- **New:** `rivaldemo/char/PSP_hap{02,01,03,04,03,03,04}_{hiramoto,masaki,reina,eiji,kuroki,ota,shima}.ana.gz`
- **Inside the XBBs:**
  - `talkTbl_<KEY>00..23.txt` (168 files)
  - charNameTbl lines 33–39 (speakers `*_32..*_38`)
  - `PSP_game_rival_<KEY>.gim`
  - rivalface `PSP_g_k_<e>_face_<low>.ana.gz`
  - `PSP_st_rivalname_<KEY>.gim`
  - New anims: _01 36–42, _02 32–38, _03 32–38, course_select_05 33–39, VS 32–38

## BOOT (region 0x57faa0–0x58067f; 13 patched words; +489 relocs)
- **Names:** `h_riv40` (0xdc7bc, then WRIV h_riv) points 35 name-table entries at the WMP names when SL + course 4 + RW. These are the talk name, portrait name, HUD face, HUD name and start card for each of the 7 enemies. In every other context they point back at the stock names. `h_area40` (0xd3794, then WRIV h_area) restores them too.
- **Anims:** these anim calls are remapped in the Wangan context:
  - 0x110af8 (_03), 0x110c00 (_01), 0x110ce8 (_02)
  - 0xd03e4 (VS)
  - 0x1100c0 (_05, only with the Wangan cursor 8)
- **Cars:** `h_se40` (0xde564, then WRIV h_se3) sets G+0x14 = 7 for e26 and e11. For those two, the parts record (0x8654c), dress-up record (0x7081c) and model flags (0x70928) come from enemy 10.
- **verify40.py: ALL OK.** It checks:
  - exact diff and relocations
  - table swap on, off and restore in each mode
  - each anim hook in and out of context, plus Akio
  - SetEnemy cars in and out of context
  - donor records and register preservation

## Talk
- 7 sets of original English lines, written for this remix (no manga or WMP script lines): intro, meet again, after a loss, decline, player won ×2, player lost, rematch yes/no.
- Mapped to scenes 0–23 like M30 Miki; 1/8/15 stay "E". Up to 38 characters per line, 2 lines per page, full-width spaces.

## QA list (PPSSPP, build 40 ISO)
1. **WMP mapping check** (on Daniel's WMP ISO, ULJM05264): in story mode, compare each rival's intro bust with the name on screen.
   - Required: 1739 Hiramoto, 1742 Masaki, 1745 Reina, 1720 Eiji, 1727 Kuroki, 1721 Ota, 1732 Shima.
   - Fix any mismatch by changing `bust` in tools/art.py and rerunning assets40.py.
2. **SL → Wangan area face row:** the 7 WMP faces plus Akio. Faces scale with WGP wins. Happogahara row stays stock (Daiki/Smiley/Tomo).
3. **Wangan rival select:** small faces, big face, info panel (name, car row, stars, no team row) for all 8 slots.
   - Watch for memory errors or a hang on entry, since the visit_rival_sel buffer is now 0x240000.
4. **Talk:** intro text and portrait for each driver.
   - Decline → re-enter → "meet again" text. Win → won text; lose → lost text; rematch yes/no.
   - Speaker names Hiramoto: … Shima:.
5. **VS card:** name position and outline. **Start card:** name size. **In-race HUD:** face + name. Reina and Kuroki must race an R32 with a sane colour and parts.
6. **Akio** (slot 8) unchanged everywhere.
7. **Leaving Wangan restores everything:** go back to area select → Akagi (Nakazato/Sudo) and Myogi/Akina rivals show their own faces, names, talk and cars. Also check Happogahara.
8. **Memory:** watch for memory errors in the course-select (visit_crs_sel buffer +64 KB) and rival-select screens. game2d has only 0x180 bytes spare, so any later game2d addition needs its buffer raised (0x84dfc / 0x85178 / 0xc4984).
9. **Save/load inside the Wangan area:** WGP progress is unchanged and names are correct after loading. The Wangan flag is restored by the rival-select ctor.
10. **Leak check:** result screen and rival cards may still show stock identities for e10/24/26/27/11/8/12 after a Wangan race (not remapped this round). Note what appears.

## Open / later
- 964 Blackbird for Shima and R33 for Kuroki (car ports); WMP-style pace tuning; result/card art for the WMP drivers.

## QA round 1 fixes (build40t)
- **Talk background:** `tools/m40_fix_boot.py` → **BOOT40F.BIN** (md5 c83832e2c67635ac3017d0b779f46617). Chained on BOOT40S (199fbddb), region 0x589800–0x58986f, one site.
  - h_bg40 at the rivaldemo bg sprintf 0xd023c: in Wangan SL with demo course 4, the path becomes `PSP_rbg_wan_n?.ana.gz`.
  - New disc files `rivaldemo/bg/PSP_rbg_wan_nf.ana.gz` and `_nr.ana.gz`: 7 shots from M29's renders of the Wangan course, in the stock layout.
  - The script accepts any input that contains BOOT40C and ends ≤ 0x589800. Checked with `tools/verify_fix40.py`.
- **"WANGAN NIGHT" overlapping "FINAL" on the race intro:** start2d PSP_game_start2d_01 anim 29 (M27 c2p2 label) now draws at 82% size, at x 0..105 instead of 0..128.
- **Post-race blank "Akio:":** Akio's talk files are M11/M31's, not M40's.
  - The pre-race line QA saw ("...Want to go, then?") is in talkTbl_AKIO_AKINA_MEET05, a challenge-path file, not in talkTbl_AKIO%02d.
  - So Akio on Wangan goes through the challenge talk path. The post-race file it picks is probably a challenge name that has no text for this case.
  - Every stock post-race table ends with "K_0" "E", so the speaker name with an empty box under the Rematch menu is normal once the lines have played.
  - All 21 non-"E" scenes of the 7 WMP sets have text.
  - Next: QA one WMP rival post-race (win, lose, time-up). For Akio, breakpoint 0xcd874 to log s3 (talk id) / s2 (scene) after TIME UP.
- **Result screen:** the stock RESULT panel (battle result, total/section times, advantage) has no rival-name field for any rival, so there is no stale name to replace. Showing a name needs a new element (deferred).
- **SNOW option:** not caused by M40.
  - The 5 replaced files are visit/visit_rival_sel, visit/visit_crs_sel (the SL area select, not TA), rivaldemo/rivaldemo, game2d/game2d and game2d/start2d (rebuilt from m27/final, so the SNOW intro anim 30 is kept).
  - The TA weather widget lives in timeattack/ta_crs_sel plus the M39 wcount code, and M40 touches neither.

## QA round 2 fixes
- **Hang when choosing Hiramoto or Reina (black screen at talk load):** found and confirmed statically. The rivaldemo ctor 0xcfd58 sets the demo course obj+0x1ac from the enemy's home-course table 0x2111ac (M11 hook 0x55503c sends only Akio to the race course). So the portrait path became `PSP_akina02_hiramoto` / `PSP_tu03_reina`, files that don't exist, and the load failed.
  - Fix: **BOOT40G.BIN** (md5 600af06b9c88e1f7eb8237a49f2879cf) via `tools/m40_fix2_boot.py`. Chained on r2 BOOT40NSF (efc3c475); region 0x589870–0x58990f; one site 0xcfdf0 → h_crs40. In the Wangan SL context, the 7 lineup enemies get demo course 4. Portraits then resolve to the shipped `PSP_hap<nn>_<name>`, and backgrounds to fix 1's `PSP_rbg_wan_n?`.
  - `tools/verify_talkload40.py` simulates the whole load per slot: rival-select name swap → demo ctor course → 24 talk tables in the shipped rivaldemo XBB (speaker < charNameTbl count, poses < 10, text present) → portrait file in the disc adds → background file. All 8 slots pass. Run on BOOT40NSF, it reproduces the missing portraits (course 3 / 7).
  - Also ruled out:
    - rivaldemo raw 0x12a500 vs its 0x130000 buffer (loader 0xcb4c4 / 0xcbeac / 0x1183bc)
    - XBB hash collisions (none)
    - speaker index range (bounds-checked, list is dynamic)
    - full-width name glyphs (same path as Miki)
- **Akio blank after a race:** talk scenes 1/8/15 are "E" in every stock set. Akio and the 7 WMP sets now have a short time-up line there (rivaldemo rebuilt, 0x12a500).
  - The scene choice for the TIME UP path was not proven at runtime. Scenes 3/4/10/11/17/18/21 already had text.

## QA round 3: post-race talk shows only the speaker name
- **Static result: the M40 talk files are not the cause.** `tools/lint_talk40.py` passes:
  - The 168 M40 tables use only tokens found in the 850 working English tables (M13 / M11 / M30).
  - Text is single-byte ASCII with SJIS 0x8140 spaces, ends with CRLF and "K_0"/"E", and the longest line is 36 characters (limit 44).
  - Every post-race outcome loads an existing table whose first page has text, for all 7 WMP drivers and Akio. Scene ids are read from the BOOT: win 3/10/17; lose 21 (state 2 = time-up/retire), 18 (has wins), 4 (first loss), 11; the time-up path at 0x118334 uses 1/8/15.
- Akio's post-race tables are M11/M13 originals and show the same blank. So the problem is in the post-race talk environment, not in the files.
  - Text and names use the same font routine 0xb7bac (h_ascii), but separate font objects.
- **Decisive runtime A/B tests** (no debugger needed):
  1. Same ISO: lose or time out against a stock rival (Akina, Nakazato). If the box is blank, the bug is global.
  2. build39 ISO: same test against Akio on Wangan. If blank, it predates M40.
  3. Wait 3 s on the first post-race page before pressing anything (the typewriter may start late).
- If blank only on 40t: memory is the suspect. Next step is to cut the M40 buffer raises back to the exact sizes (visit_rival_sel 0x237000, visit_crs_sel 0x1c9400) and re-test.

## QA round 4: blank post-race text only for the Wangan lineup (WMP rivals and Akio)
- **Checked statically, all as expected:**
  - The post-race talk is built by the same rivaldemo ctor 0xcfd58 as the pre-race one.
  - Scene choice: lose path 0xcb62c and win path 0xcc014 are stock and unhooked. They use the WGP/AKP getters, giving 21/18/4/11 and 3/10/17; the time-up path 0x118334 gives 1..15.
  - Every one of those resolves to an existing table with text, for the 7 WMP drivers and Akio (lint_talk40.py).
  - Names are not restored before the post-race talk: QA saw "Hiramoto:" (*_32), and a restore would give "Nakazato:". WACT is cleared only by the area-select ctor.
- **Ctor inputs that differ pre- vs post-race:**
  - a3 = scene;
  - G+0x10 → obj+0x230;
  - the talk text font is created the same way.
- **Wangan-only state** (set by M34 WRIV h_se3, unchanged since build 34): G+0x1c = 8 + direction, G+0x20 = 0, G+4 = 4 + RW. Akio's r1 blank came before the M40 bg/course hooks, so the cause is probably older than M40 (WRIV era). It still has to be pinned down at runtime.
- **A/B tests to isolate it:**
  1. build39 (WRIV lineup = Nakazato etc.): Wangan, race Nakazato, retire. If blank, it's a WRIV-era state issue, not M40.
  2. build40t: Happogahara (course 4 without RW), race Daiki, retire. This separates course 4 from the Wangan flags.
  3. Memory view after the race, during blank talk: read G+0x1c (0x08C94F24 = 0x490f24 + 0x08804000). Then poke it to 2 before choosing Rematch, and check whether the next post-race talk shows text.
# M42 WMPART: WMP character art polished to Initial D's look (build 42)

No BOOT change. `manifest42a.json` = the same 5 replaced files + 9 added files as manifest40c, rebuilt from the build-41 sources
(build 41 only changed result.bin.gz and BOOT, so the m40 sources are the build-41 versions). Anim bases and loader limits are
unchanged: visit_rival_sel 0x237000 / 0x240000, visit_crs_sel 0x1c9400 / 0x1d0000, rivaldemo 0x12a500 / 0x130000,
game2d 0x17ff80 / 0x180000 (0x80 bytes spare), start2d 0x65780 / 0x80000.

## What was compared (sheets/*.png: ID examples | WMP build 40/41 top row | build 42 bottom row, 3× PSP size)
| Asset | ID reference | Build 40/41 port | Build 42 |
|---|---|---|---|
| rival-select face 48×64, big face, area face 44×58 | head fills the cell (hair clipped ~2 px, chin ~88 %), eyes ~38–40 % down, crisp cel line art, warm saturated skin | head ~20 % too small, eyes ~45 %, pale/soft (WMP hatching) | eye line fixed at 38 % with per-character eye offsets, head = 1.45 × head width; colour 1.30, contrast 1.22, gamma 1.12, unsharp after the downscale |
| talk portrait 256×256 (10 poses) | head ~110 px tall, chest cut at the bottom, transparent | whole 240×232 bust scaled to the canvas (head ~75 px) | bust scaled 1.22–1.42× in 3 alternating framings, head ~105–120 px, soft chest cut; same grade + sharpen |
| HUD face 128×64 | brow-to-chin close-up inside Akio's speed-line frame | similar crop, pale | tighter (0.72 × head width), graded; 64-colour palette (game2d is full) |
| start card 128×32 | tall condensed bold serif, navy outline, cap height ≈ Nakazato's | small serif | DejaVu Serif Condensed Bold rendered at 40 px, scaled so the cap height equals the stock card's, condensed to ≤124 px |
| HUD name, VS card name, info-panel name | DejaVu Bold / Bold Oblique (as the remix's own English labels) | same | unchanged (already matched; VS row = Akio's layout) |

Quantisation: every new texture goes through `art42.quantize_nodither` (MEDIANCUT, dither off, exact alpha), then the stock
encoder, so faces have no dither noise. Only crop / scale / grade / sharpen / quantise / frame: the drawings are WMP's own.

## Files
- `tools/art42.py` (framing + grading), `tools/assets42.py` (build; writes files/, add/, prev/, anims40.json), `tools/sheets42.py`
  (contact sheets), `tools/verify_assets40.py` (ALL OK), `manifest42a.json` (with md5 per file).
- Talk tables and charNameTbl are the build-40 r2 versions (unchanged content).

## QA
1. SL Wangan rival select: faces should now sit like Nakazato's (eyes level, same head size); check the 7 small + big faces.
2. Area select Wangan row: 7 faces + Akio.
3. Talk: portrait fills the frame like the ID busts (head not tiny), bottom edge fades at the chest.
4. Race intro: start card names at the same height as "Takeshi Nakazato". HUD face + name.
5. Memory: game2d has 0x80 bytes spare; any later game2d addition needs its buffer raised (0x84dfc / 0x85178 / 0xc4984).
