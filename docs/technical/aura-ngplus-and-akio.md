# M58 AURA + AKIO (build 58)
`m58_aura_boot.py base56H.BIN BOOT58A.BIN --json patch58a.json` (base BOOT56H 828d8535) → **BOOT58A md5 282fe555ac77c39acfd235d32d7394c5**.
Diff: region 0x5a6200–0x5a696f + hook words 0x5567cc (RIV→RIV2), 0x5569b0 (PL4→PL6), 0x556a54 (hE1→hG1), 0x556aec (hF2→hG2),
0x55f0fc (hGAP3→hGAP4), all existing R_26; new relocs appended. `verify58a.py` → ALL OK (122 checks).

## 1. Star / NG+ system (findings)
- The SL "stars" are the game-clear count G+0x94 (0x490f9c, save S+0x1cc). 0x148944 (save load) raises it by 1 when all 31 rivals
  incl. Miki and Bunta are beaten, resets SL progress, max 7. 0x10ff64 (SL area screen) draws one star per clear (loop to 7).
- Rival AI pace does not use it: the per-level speed table 0x1d34e8 is all 1.0; the info-panel stars are baked per-rival art.
  Only Bunta (Challenge) has a level ladder: G+0x438[course] 0..15 (16 = cleared), unlocked max in save 0x4a35b5[course].
- So "NG+ cycles" = clears 1..7 (7 levels). Aura by clear count: NGS = 0 / .55 / .65 / .85 / 1.0 / 1.2 / 1.35 / 1.6
  (tiers: 1–2 small, 3–4 medium, 5–6 big, 7 max). Legends keep their colour and at least their M46 size; Bunta keeps his
  level rule (max with NG+); Akio = rainbow. Other rivals: NGCOL table (per enemy id). Wangan/Hakone and page-2 drivers use NGCOL of
  their donor id (they run on donor enemy ids).
## 2. Rainbow option
- Card 192 owned (0x4920a6 & 0x800) + the garage car has 18/18 steps + White selected → the race aura is Akio's rainbow (gmo 9) with
  his flare then pulse (PL6 writes the player scale from the AB tables). Bonus = full white (+36 at STEP 2). AURA TUNE header shows
  "RAINBOW" when it applies. No change to the SELECT cycle (select White to use it).
## 3. Akio
- **No built-in world-ranking table exists.** Searched: TA ranking builder 0x148298 (own records only), save init 0x1469e8 (no seeding),
  Project D Web data (hp_data_00..02: gallery text only), save_data / tushin / timeattack files, BOOT data scans. The TA "ranking" is
  built only from the player's own times (S+0x1e0…).
- Reference "record" used instead: Akina downhill (crsmdl 6, dfi line 7.69 km) = 2'40"00, i.e. 4 s under Daniel's 2'44 in his
  fully upgraded Z. Other courses scale with the game's own AI speed profile (0x1d3528) × the level-15 multiplier (LM, 1.00–1.18).
- hG1/hG2: Challenge (M42 set) / SL (M41 set) then ADJ58 — no aura weakening (M53 ADJ and M54 accel limiter no longer called):
  GAIN = GT[ctx][crsmdl] (stock 1.324 CH / 1.311 SL; Wangan 1.15; Hakone 1.20 / 1.18), RB_MUL 1.0, RB_ADD +4 / +2,
  CORNER_CAP 1.25 / 1.15, TOP = player base top + 0.5 (touge), **286 km/h on Wangan** (max-aura Devil Z 288).
- Predicted Akio solo laps (calib58.py / table58.py, rail model ±1 km/h per AI call): see table58.json.
## Tunables (CWCheat = vaddr + 0x4000)
rainbow on/off `_L 0x005AA213`, NG+ on/off `_L 0x005AA218`, Akio set on/off `_L 0x005AA219`, Wangan top `_L 0x205AA224 0x438F0000`,
GT Challenge f32[18] at 0x205AA280, SL at 0x205AA2C8 (index = crsmdl 0–15, 16 Wangan, 17 Hakone), NGS f32[8] at 0x205AA240,
RB_ADD f32[2] 0x205AA228, CAP f32[2] 0x205AA230.
## QA
1. Save with clears 0 / 1 / 3 / 5 / 7 (cheat on 0x490f9c): SL rivals glow none/small/medium/big/max; legends keep colour.
2. Card screen gives aura cards only vs aura opponents (OPPK/OPPT).
3. Rainbow: give card 192 (`_L 0x104960A6 0x00000801`), 18 steps, White → rainbow pulse; header shows RAINBOW.
4. Akio Challenge: Akina downhill dry ≈ 2'38", independent of aura; Wangan top ≈ 286.
