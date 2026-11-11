---
name: psp-formats
description: Reference for PSP game file formats and how to read/write them with the plugin's tools — UMD ISO layout, PARAM.SFO, EBOOT/BOOT.BIN, GIM textures, GMO models, @ANA layouts, Sega XBB, Genki BUILD.DAT/UCL, gzip, AT3 audio, PMF video. Use when identifying an unknown file, converting assets, or before repacking anything.
---

# PSP formats

Identify first: `python ${CLAUDE_PLUGIN_ROOT}/scripts/magic.py` (import `guess`) or check magic bytes below.

| Magic | Format | Read | Write |
|---|---|---|---|
| `CD001` @0x8001 | ISO9660 UMD | `iso_tool.py` | `iso_tool.py patch` |
| `\0PSF` | PARAM.SFO | `iso_tool.param_sfo` | rarely needed |
| `\x7fELF` | plain executable (BOOT.BIN often unencrypted) | `mips_tool.py` | binary patch / armips |
| `~PSP` | encrypted PRX/EBOOT | decrypt via PPSSPP dump | replace with patched ELF |
| `MIG.00.1PSP` | GIM texture | `gim.py topng` | `gim.py frompng` (template) |
| `OMG.00.1PSP` | GMO model | `gmo.py` | extend gmo.py / clone template |
| `@ANA` | Sega 2D layout/animation with embedded GIMs | `menu_label.py list` | in-place GIM swap |
| `XBB\x01` | Sega archive | `xbb.py` | `xbb.py repack` |
| `\x00\xe9UCL\xff\x01\x1a` | uclpack stream | `ucl.py` | store raw / `ucl.store` |
| `1f 8b` | gzip | `psp_gz.py` | `psp_gz.py repack` |
| `RIFF....WAVE` + fmt 0x270/0xFFFE | ATRAC3/ATRAC3plus (.at3) | ffmpeg decode | at3tool encode |
| `PSMF` | video (.pmf) | ffmpeg (partial) | Sony UMD Stream Composer |

Details: `references/gim.md`, `references/gmo.md`, `references/containers.md`.

## Rules of thumb
- Chunked Sony formats (GIM, GMO) use: long chunk `u16 type, u16 flags, u32 size, u32 child_off, u32 data_off`; short chunk (type has bit 15) `u16 type, u16 8, u32 size, payload`.
- Swizzled textures ("faster" pixel order = 1) are 16-byte × 8-row tiles.
- 16-bit vertex positions are normalized and need the GMO 0x8015 offset/scale chunk to become world units.
- `0xCD` fill bytes are padding from Sony's debug allocator — safe landmarks, not data.
- A file size that is a multiple of 2048 means it is sector-aligned on disc; keep it that way when replacing.
