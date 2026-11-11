# Tool reference (`${CLAUDE_PLUGIN_ROOT}/scripts`)

Python 3.10+. `pip install pycdlib capstone pillow numpy`. `gcc` for the UCL decoder (auto-built).

| Script | Purpose | Status |
|---|---|---|
| `iso_tool.py info/list/extract/patch/rebuild` | UMD ISO9660: fingerprint, LBA layout, extract, in-place patch with directory-record repoint **and game file-table (lba.dat) sync** | tested on ULJM05264, ULJM05093 |
| `magic.py` | file-type guesser (GIM, GMO, XBB, UCL, AT3, PMF, offset tables, SJIS text) | |
| `ucl.py` + `nrv.c` | uclpack container, NRV2B/2D/2E, 8-bit and LE32 bit buffers | all 8295 WMP entries decode |
| `wmp_build.py unpack/repack` | Wangan Midnight Portable BUILD.TOC/BUILD.DAT | unpack verified; repack stores raw |
| `xbb.py list/unpack/repack` | Sega XBB\x01 container (Initial D) | byte-identical round trip |
| `psp_gz.py unpack/repack` | gzip with original header cloned | |
| `gim.py topng/frompng/info`, `gim.build()`, `gim.pictures()` | GIM textures incl. multi-picture GIMs; `build` writes Initial D-style index4/8 GIMs from any image | header byte-identical to IDSS |
| `gmo.py tree/obj/render` | GMO models: chunk tree, OBJ export with vertex offset/scale, flat-shaded previews | strips verified on WMP cars |
| `gmo_tree.py` | lossless GMO tree edit/serialize; replace part geometry, add materials/textures | 462/462 round-trip |
| `sjis_scan.py` | Shift-JIS string finder, JSON export | |
| `menu_label.py list/render/patch` | redraw baked menu labels inside @ANA layouts in Initial D style | used for English main menu demo |
| `mips_tool.py info/dis/xref/ptr/str` | Allegrex ELF helper (sections, disasm, address xrefs) | |

Missing tools to fetch/build when needed: `armips` (assembler for patches, build from source), `xdelta3` (apt), an AT3 encoder (Sony `at3tool` is not redistributable; use FFmpeg to decode and the user's own at3tool/PSP SDK copy to encode, or ATRAC3plus via `at3tool -e` on the user's machine), PPSSPP on the user's machine.
