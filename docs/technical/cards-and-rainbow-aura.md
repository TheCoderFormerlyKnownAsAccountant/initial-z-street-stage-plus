# M58 CARDS (build 58): aura drops only from aura opponents + Rainbow Aura card (id 192)

- `m58_cards_boot.py BOOT56H BOOT58C --json patch58c.json` → **BOOT58C md5 893c3b83a38433dbd6aaf185ffa90c6a**.
  - New code is only in 0x595000–0x595287, written in place (the region was zero), plus 85 in-place words.
  - 48 relocations are appended to .rel.data.
  - `verify58c.py` → ALL OK (52 checks, verify58c.log).
- Assets: `art_rainbow.py` (art/), `m58_assets.py` → files/, add/, assets58.json. `manifest.json` lists them.

## 1. Aura drops
- At the card screen (M43 PRE → M58PRE), the race qualifies when: mode SL (0) or Challenge (2), outcome 0, and RKIND (0x5563e0, set by M46 RIV at race start) ≠ 0.
  - Qualifying win: the first AGUAR (1) cards are aura cards (186–191); every other slot rolls APCT (25) %.
  - Anything else (TA, losses, any opponent without an aura): DB+0xc = 0, so no aura cards.
- Tunables:
  - AGUAR u8 0x595010 (`_L 0x00599010`)
  - APCT u8 0x595011 (`_L 0x00599011`)
- unicorn: 60 qualifying wins → first card always an aura, other slots 21 % aura. No aura cards in 60 non-qualifying wins or losses.

## 2. Rainbow Aura (id 192)
- **Card manager 191 → 192:**
  - 20 bound sites changed, plus the viewer wrap and the thumbnail bound.
  - Arrays re-laid for 192 ids (A2 0x780, A3 0xd80, buffer 0x1380, fields 0x1580.., 46 remaps); 6 allocs 0x15a0 → 0x15c0.
  - M15 hooks: category 7, label width 84 (WID[6]), label cell col 1 row 13 (LBL1/LBL2).
- **Devil Z Challenge wins per item** (8 courses, Wangan, Hakone): bits in the free 0xf000 nibbles of S+0x1a2/1a4/1a6.
  - Every stock writer read-modify-writes these entries and masks 0xff, 0x800 and 0x100–0x400 (checked: 0x147c68, 0x14e848/8bc/a30, viewer 0x1510c0/134).
  - The "All cards x99" cheats overwrite the nibbles while they're on.
- When all 10 items are won and the card isn't owned, RBADD adds card 192 to that screen's batch (replacing the 10th card if needed), tagged NEW. The normal award loop then sets S+0x1ae = 0x0801.
- **Assets:**
  - Art: `PSP_192.gim` and `PSP_s_192.gim` (Sticker-card template, rainbow flame/frame), added loose under card/pic.
  - `card_view_s19.bin` + `PSP_s_192.gim`.
  - `card_viewer.bin` (m27/crs9): cardtext block 192 + font06 "Rainbow Aura" label.
  - `result.bin.gz` (m45/polish): name "Rainbow" + result cardtext block.
- Cheats in `cheats58.ini`: Give Rainbow (`_L 0x104960A6 0x00000801`), Rainbow ×99, AGUAR/APCT, rainbow reward off (0x00599012 = 0).

## QA
1. **Card Collection:** page 20 shows 191 White and 192 Rainbow Aura (thumbnail, detail page, "Aura Card" type, "Rainbow Aura" label). Every other page is unchanged; check pages 1, 10 and 19 for text and labels.
2. **SL win vs Nakazato** (legend aura): at least 1 aura card in the 10. **SL win vs a non-aura rival:** no aura cards. **TA finish:** none. **Loss:** 5 cards, none.
3. **Devil Z Challenge:** use the cheat or play to win all 10 items. On the last win the card screen shows Rainbow, tagged NEW. It is never given again.
4. **Old saves:** cards 1–191 are unchanged in Card Collection, and the counts on the 10-card screen match.
