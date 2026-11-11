# Wangan Midnight Portable (湾岸ミッドナイト portable)

- Disc ID ULJM05264, disc version 1.02, firmware 3.30, Genki / Namco Bandai 2007. ISO 336 MB.
- EBOOT encrypted; BOOT.BIN is a plain ELF (use it for code analysis).
- Filesystem: `USRDIR/build/BUILD.TOC` + `BUILD.DAT` (215 MB, 8354 nameless entries), `USRDIR/WMN/Movie/*.pmf`, `USRDIR/WMN/Sound/Atrac3/*.at3` (BGM).

## BUILD.DAT map (entry ids)
- 280–306: misc + first car set. Player cars = GMO followed by its ~21–25 GIMs:
  307 FC3S, 330 SE3P (RX-8), 353 CT9A, 376 CP9A, 399 Z15A (GTO), 422 BNR34, 445 BNR32, 468 Z33, 491 Z32, 514 S15, 537 RPS13, 560 GDB, 583 GC8, 606 BL5 (Legacy), 629 JZA80, 652 GRS182 (Crown), 675 SXE10, 698 ZZT231, 721 ZZW30.
- 744–822: story/rival cars, GMO + 2 GIMs each: **744 akio (Devil Z, S30 Fairlady Z)**, 747 harada, 750 yamashita, 753 makoto, 756 reina, 759 hiramoto, 762 tomoya, 765 taka, 768 sonoda, 771 ryou, 774 motoki, 777 yamanaka, 780 yamamoto, 783 goto, 786 kijima, 789 masaki, 792 ota, 795 oki, 798 kei, 801 gachan, 804 eiji, 807 maki, 810 shima; traffic 813 JZX90, 816 KR42V, 819 E39A, 822 truck.
- 826–1091: wheel/tire packs (GMO + GIM pairs; brands RAYS, Enkei, SSR, Work, etc.).
- 1092–1138+: 4958-byte car spec records (8 sections; ASCII name + chassis, e.g. 1092 "FAIRLADY Z Z-L / S30"), then other cars/rivals.
- 1146–1805: UI textures, XMD containers (78), GIM sets.
- 1813–8343: course streaming chunks (texture pack + many GMO chunks per group, repeated for routes/directions).
- 34 PPHD sound banks; FNIG records (floats, likely course/camera data).

## Devil Z (akio) model
GMO 744: 23 parts, 3146 verts, 2510 tris, vertex type 0x122 (uv16, normal8, pos16), offset/scale (3.393, 0.556, 0)/(5.632, 0.656, 2.398); textures akio_bd/bn/fl/rs/muf/en/in/num/flef + shared headlight. Decal sheet 745 (S30 Z badge, Fairlady Z script). Low-poly compared to player cars (~220 KB) — plan a detail pass.

## Formats
- BUILD.TOC entries `{sector, stored, unpacked(0=raw), 0}`; compressed = uclpack NRV2B **LE32**.
- Offset-table packs `u32 n, offsets[n]` everywhere.

## Text / dialogue (confirmed 2026-10-15; codec `scripts/wmp_text.py`, round-trip 142/142 packs)
- No Shift-JIS/UTF-16 text anywhere in BUILD.DAT or BOOT.BIN (BOOT.BIN only has 1 stray `Ｚ`). All game text is **glyph-indexed**.
- Fonts: 132–135 = glyph bitmap fonts (4 sizes). 136 = charset as SJIS (3578 glyphs, no Latin prefix). **137 = charset as UTF-16 u16 per glyph (3775 glyphs: ASCII + Latin-1 + 3578 SJIS-order glyphs). Glyph index = index into 137.**
- Text packs = entries **138–279** (offset-table packs). Layout: `u32 n; u32 offs[n]`; zero pad to `offs[0] = ((4+4n)//32 + 2)*32`; record = `u32 0, u32 0xFFFFFFFF, u32 glyph[], u32 0xFFFF`, padded with zeros to `(used//32 + 1)*32` bytes (last record unpadded). Glyph `0xFFFE` = line break. Confirmed via byte-exact build over all 142 packs.
- **No speaker field** in records (header is always `0, -1`). The speaker is implied by the pack (arcade quote packs) or the scene. A `.data` search for per-line speaker tables found nothing.
- Pack map: 138 system words (はい/いいえ/決定…), 139 Shutoko area names, 140 car names/grades/chassis codes, 141 mode names, 142 result menu, 143–144 system/help messages, **145 rival roster** (23 names in the same order as rival GMOs 744…810: アキオ, 原田, 山下, マコト, レイナ, 平本, 友也, 黒木, 園田, 帝塚, 元木, 山中, 山本, 後藤, 城島, マサキ, 大田, オキ, ケイ, ガッちゃん, エイジ, マキ, 島).
  - **146–168 arcade rival battle quotes**, one pack per rival: slot0 `-`, slots 1–3 (sometimes 1–4) pre-race, `-`, then "rival wins" and "rival loses" lines, `-`. **146 = Akio.** The pack order is NOT the 145 order (147 = Shima/Blackbird, 152 = Harada, 193 mentions 911 = Jojima).
  - 169–202 scenario battle quote packs. Mixed speakers: the protagonist's lines come first, then the opponent's.
  - 203–257 scenario story cutscene scripts (one large pack per chapter plus short epilogue packs). Slots 2–4/5 are chapter-intro narration, `-` separates scenes.
  - 258–261 final chapter (259 = Akio POV, 261 = Shima POV). 262–275 tuning-shop dialogue. 276 shop names, 277 scenario series titles, 278 mission objectives, 279 mission descriptions.
- BOOT.BIN `0xc29f4` (VA): `f(scenario 0..22, chapter) -> global mission index`. Jump table at 0x16ce34 with bases 0,12,24,36,48,50,62,74,86,98,100,112,124,127,130,133,160,164,168,173,177,182,203. Inverse at ~0xc2990. Not a pack-id mapping.
- Entries 9–34 and 130/131 are typed object-graph records (tag 0 = float, 2 = ref). They are not text.

## Sound (confirmed)
- 34 PPHD banks = 17 pairs at 1151…1218 (odd = PPHD header, even = raw PS-ADPCM body). PPVA sample table at `PPVA+0x20`, 16 B each `{offset, rate, size, -1}`.
  - 1151/1153/1155/1157 = system SFX/ambience (8/4/39/7 samples, about 58 s total).
  - 1159–1217 = 30 banks × 8 samples of about 1 s, identical 1616-byte headers = per-car engine loops.
- **No character voice clips** exist in BUILD.DAT. Total non-engine audio is too short to hold voiced dialogue.
- `USRDIR/WMN/Sound/Atrac3/*.at3` = BGM. All files are ATRAC3plus, 44.1 kHz stereo, 96 kbps. `poem.at3` = 30.2 s music cue in three phrases (silences at 7.5 s, 14.1–15.7 s, 28.1 s). It is wide-band stereo (centroid about 3 kHz, side about -13 dB) and very likely instrumental BGM for the "poem" narration screens, not speech (likely; judged from signal stats, not by listening).
- The only other audio is in `Movie/wangan_end_0[01].pmf` (ending movies, not inspected).
