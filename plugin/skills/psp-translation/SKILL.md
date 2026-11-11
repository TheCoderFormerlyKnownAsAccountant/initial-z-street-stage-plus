---
name: psp-translation
description: Assess and perform Japanese-to-English (or other) translation of PSP games — string extraction from executables, per-screen glyph atlases, baked menu textures, width/byte budgets, dual-tile fonts, repointing, and redrawing menu labels in the game's style. Use for "translate the menus", "English patch", "is a translation viable".
---

# Translation

## Assessment checklist (produce counts for each)
1. Code strings: `sjis_scan.py BOOT.BIN --min 3 --json strings.json`; keep entries that are NUL-terminated and contain kana. Note `%s/%d`, `\n`, and full-width characters.
2. Font system: find `*_lst.txt` (char=index maps) and their atlas GIMs (`*_00.gim`, `*_01.gim`). Count glyph slots per screen (256 per atlas) and how many are free after the English set.
3. Baked text: `menu_label.py list layout.ana sheet.png` for every `@ANA`; count label textures and help panels.
4. Movies/voice: subtitles would need new overlay code; mark out of scope unless asked.
5. Verdict per channel: easy (in-place, fits), medium (needs DTE/atlas edits), hard (needs repointing or renderer change).

## Techniques
- **Baked labels** (fastest win, menus become navigable): `menu_label.py patch IN.ana OUT.ana --set IDX="TEXT":ACCENT:plain|glow`. Texture size/format unchanged, text fitted to the original label's opaque bbox.
- **Atlas text**: rewrite the atlas with Latin glyphs and update `*_lst.txt` so the full-width code points the strings use (Ａ-Ｚ, ａ-ｚ, ０-９, punctuation) map to new glyphs. Test whether ASCII bytes render; if not, use full-width code points or a dual-tile scheme where one 16 px cell holds two 8 px letters (assign unused kanji code points to letter pairs and encode strings with them).
- **Byte budget**: Japanese 2 bytes/char, so an English string of the same byte length gets about 2× the characters in ASCII, 1× in full-width. Longer strings → repoint to free space (psp-code-patcher) and update the pointer + relocation.
- **Glossary first**, then translate in batches by screen; keep IDs stable (`file:offset`).

## Initial D Street Stage findings (ULJM05093)
- ~700 UI strings in BOOT.BIN `.data` (file 0x1f3600–0x2427ff, ≈25 KB): errors, save/load, garage/tuning, communication, card trade, coaching lines.
- Message rendering uses per-screen atlases (e.g. `select/sel_gamemode.bin` → `msg_00.gim`, `msg_01.gim`, `msg_lst.txt`), 16×16 glyphs incl. full-width Latin.
- Main menu items, headers and mode descriptions are baked GIMs in `PSP_mode_select.ana` (48 textures, labels are index8 512×64). English versions already produced as a proof (CHALLENGE BUNTA!!, STREET LEGENDS, TIME ATTACK, VERSUS, GARAGE, CARD COLLECTION, PROJECT D WEB, OPTIONS).
- Verdict: menus = viable now; system messages = viable (full-width English or DTE); story/coaching dialogue = viable with repointing; voice = keep Japanese.
