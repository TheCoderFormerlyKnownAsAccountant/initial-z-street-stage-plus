# psp-remix

Decompile PSP UMD games, mix assets and code between them, translate them, and recompile playable remixes. First project: **Initial D Street Stage × Wangan Midnight Portable** (Devil Z as a new car, a Devil Z Challenge mode, a Wangan-style highway course, more music, English menus).

## Agents
| Agent | Role |
|---|---|
| `psp-decompiler` | Fingerprint ISO, extract, recursively unpack, convert assets, catalog everything |
| `psp-format-reverser` | Crack unknown formats from samples + code; write round-trip parsers |
| `psp-code-patcher` | Allegrex MIPS analysis; new slots, modes, tables, hooks; armips/CWCheat patches |
| `psp-asset-mixer` | Port cars/courses/music between games, restyle to target art, synthesize tuning data |
| `psp-translator` | Text inventory, glossary, glyph atlases, baked menu labels |
| `psp-recompiler` | Rebuild containers/compression/ISO with verification; xdelta + build report |
| `psp-qa-tester` | PPSSPP test plans, screenshots, debugger dumps, pass/fail evidence |

## Skills
`psp-remix-project` (orchestrator), `psp-formats`, `psp-code-patching`, `psp-car-porting`, `psp-course-porting`, `psp-translation`, `psp-music-mod`, `psp-game-notes` (per-game knowledge base).

## Tools (`scripts/`)
`iso_tool.py`, `magic.py`, `ucl.py` + `nrv.c`, `wmp_build.py`, `xbb.py`, `psp_gz.py`, `gim.py`, `gmo.py`, `sjis_scan.py`, `menu_label.py`, `mips_tool.py`. See `skills/psp-remix-project/references/tools.md`.

Requirements: Python 3.10+, `pip install pycdlib capstone pillow numpy`, `gcc` (UCL decoder). Optional: armips, xdelta3, ffmpeg, Sony at3tool (user-supplied), PPSSPP.

## Quick start
```
python scripts/iso_tool.py info GAME.iso
python scripts/iso_tool.py extract GAME.iso work/game/iso
python scripts/xbb.py unpack sel_gamemode.bin out/        # Initial D menus
python scripts/wmp_build.py unpack BUILD.TOC BUILD.DAT out/   # Wangan Midnight Portable
python scripts/iso_tool.py patch GAME.iso OUT.iso --replace /PSP_GAME/USRDIR/...=newfile
```

## Use responsibly
For personal use with discs you own. Share work only as xdelta patches, and never bundle another publisher's assets into a distributable patch.
