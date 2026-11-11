# Build history

This is a readable summary. The full engineering notes for every build are in [DEV_LOG.md](DEV_LOG.md).

| Builds | Dates (2026) | Highlights |
|---|---|---|
| 1–4 | mid Oct | Disc, XBB and `lba.dat` reverse-engineered. First English main menu, S30 names, HUD and GT-R engine sound. Patched EBOOT. |
| 5–8 | Oct | Devil Z data: power, collision box, Akio portrait and name, 5-speed gearbox. **DEVIL Z CHALLENGE** first replaces Challenge Bunta, then becomes a 9th menu item with an asset hash-swap hook. 8 WMP race tracks added as songs. |
| 9–11 | Oct | Rubber-band AI for Akio and a permanently blue Devil Z. Akio becomes an extra Street Legends rival on all 8 courses after Bunta. Menu freeze fixed (an out-of-bounds widget write). |
| 12 | 17–28 Oct | **All 826 rival talk scripts in English** (4,891 lines) with a half-width font hook. Scene-load memory tightened. |
| 13–14 | 28 Oct | English system messages (~530), 8 px fonts, ~300 re-lettered textures, full Card Collection text, Devil Z race model slimmed. Full Japanese-to-English conversion. |
| 15–16 | 28 Oct | **Aura cards** and the AURA TUNE spec. 30 extra race songs (own ATRAC3 encoder). |
| 17–24 | 29–30 Oct | First Wangan highway experiments, release kits v1–v7, the new "Initial Z" branding, Wangan at night (skyline, sodium lamps, gantries). |
| 25–26 | 30 Oct | **Devil Z becomes its own car (#36)** instead of replacing the S15. |
| 27–31 | 31 Oct | Wangan as its own course item. Akina SNOW. Miki's snow event. Garage panels. Akio's per-course record. |
| 32–35 | 31 Oct–1 Nov | Heap moved to make room for remix code. Devil Z unlock rules. Wangan lineup. **Wangan rebuilt on a real WMP expressway route** (6 km, Daikoku JCT): grid, streaming, progress, replay cameras and record slots all traced and fixed. |
| 36–39 | 1–2 Nov | Devil Z tach, Wangan rival pace, race-music streaming fix, aura stats, **SNOW on every course**. |
| 40–43 | 2–6 Nov | **WMP drivers** as the Wangan lineup, with art polished to Initial D's look. Opening movie pipeline. Aura +km/h per step. Card screen rewritten (thumbnails, names, 10 on a win and 5 on a loss). Akio mirrored on the title. |
| 44 | 6 Nov | New opening movie: rival vignettes and the Devil Z with its rainbow aura. |
| 45 | 6 Nov | **Hakone from OpenStreetMap + DEM**. 15 WMP rivals on every course. Unlock gate. Cheat file. |
| 46 | 7 Nov | **Talk bug fixed** (English lines were run as script commands). Legend auras in races. **7 WMP cars**. |
| 47–51 | 7 Nov | Wangan/Hakone pop-in fixed (LODs). Song embedded in the movie as ATRAC3plus. Progression (Takumi → Wangan drivers, Bunta → Akio). Stutter fixes. Intro reverted to the original layout with a new ending. |
| 52–55 | 8 Nov | Car fixes, cheaper auras, Hakone camber and Versus, **real minimaps for Wangan and Hakone**, **INITIAL Z car page**. |
| 56 | 8 Nov | **Dialogue rewrite** for Akio and all Wangan drivers. |
| 57 | 8 Nov | Rivals no longer stop 400 m before the finish on Wangan and Hakone. |
| 58 | 8 Nov | Aura cards only from aura drivers. New Game+ star auras. **Rainbow Aura card**. Akio retuned. |

Every release kit rebuilds a byte-exact ISO from the player's own stock disc, and each one was test-applied with MD5 verification.
