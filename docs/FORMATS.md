# PSP formats, as learned on Initial Z

This is a summary. The readers and writers are in [`lib/`](../lib/).

## Disc
- **UMD ISO (ISO 9660)**: `iso_tool.py` reads files, and with `patch --replace/--add` writes replacements and new files. It keeps LBAs where a file still fits, relocates it otherwise, enlarges directories, and re-verifies directory records afterwards.
- **`USRDIR/lba.dat`** (Initial D): the game does **not** use the ISO directory. It reads files through this table, which has 3,761 entries of {disc byte offset, size, 0, name hash}. Any changed file has to be updated here.
- **Name hash**: found in the executable (function at 0x140d6c) and reimplemented in `xbbhash.py`. The same hash is used for XBB entry names and for `lba.dat` paths (USRDIR-relative, with backslashes). Solving it is what made *adding* files possible.

## Containers
- **gzip**: repacked gzips must keep the original header fields and should not grow past the original size, so zopfli is used.
- **XBB (`XBB\x01`)**: Sega's archive. Entries are hashed names plus offset/size. Several names can **alias** one blob, which is important for staying within memory. The scene loader reserves a fixed buffer per file, so every repack is checked against that limit.
- **BUILD.DAT / BUILD.TOC** (Wangan Midnight Portable, Genki): 8,354 entries compressed with **UCL NRV2B (LE32)**. `nrv.c` is a clean-room decompressor.

## Graphics
- **GIM** (`MIG.00.1PSP`): chunked textures with 4/8-bit palettes and optional swizzle (16-byte × 8-row tiles). Re-encoding preserves the palette layout and avoids dithering, so new art doesn't look noisy.
- **GMO** (`OMG.00.1PSP`): chunked models. Positions are 16-bit, normalised by a per-model **quantisation box** (chunk 0x8015). Moving geometry to a new course means rebuilding these boxes and the bounding boxes, and the LODs with them.
- **@ANA**: Sega's 2D layout and animation format with embedded GIMs. It drives menus, faces, cards, HUD and minimaps, and was reverse-engineered far enough to add animations, textures and sprite pieces.

## Executable
- `BOOT.BIN` is a plain ELF. EBOOT.BIN holds the same code behind a 0x150-byte `~PSP` header.
- Addresses: vaddr = file offset − 0x54; runtime = vaddr + 0x08804000; CWCheat = vaddr + 0x4000.
- New code lives in reserved regions past the stock end of the image. The heap start was moved so that remix code and data never collide with the game's allocations.
- Every hook is checked with a **relocation simulation** at the real load address, plus **Unicorn** runs of the patched functions.

## Courses (Initial D)
- **Path files** (`s_vh_path`, `_l`, `_r`): progress is "which quad am I in", so the left/right sides must follow the stock winding. Swapping them breaks streaming and gives WRONG WAY.
- **AI lines**: 10 m points, zero-terminated. A per-course point limit in the executable wraps progress; this is what made rivals stop before the finish on the new courses.
- Also in the executable rather than the course files: section boundaries (by path index), start grid tables, replay camera files and record slots.
- **Collision**: triangle cells with wall bands and end aprons. The road surface tilts with curvature (about −1.02 × curvature).

## Audio and video
- **PMF / PSMF**: H.264 Main@2.1 480×272 plus ATRAC3plus. Movies **must** carry an ATRAC3plus stream; LPCM or video-only PMFs hang the game. The opening carries the song as 2048-byte ATRAC3plus frames, read through the 0x0FD0 per-frame header.
- **AT3**: ATRAC3 in RIFF for race BGM, produced by an in-house encoder (`tools/audio/at3enc.py`).

## Text
- **Talk scripts**: a token grammar of speaker, pose, window and wait commands, page end `N`, talk end `E`. **Any line starting with a command letter is executed as a command.** The Japanese originals never collided with this; English lines did, until a load-time marker fixed it.
- System strings are SJIS in the executable, and glyph atlases are per screen. English talk uses a half-width 8×16 font through a code hook.
