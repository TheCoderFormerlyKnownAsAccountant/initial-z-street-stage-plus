# GIM (MIG.00.1PSP)

Header 16 bytes `MIG.00.1PSP\0` + 4. Blocks: `u16 id, u16 0, u32 block_size, u32 header_size(next), u32 data_offset`.
IDs: 0x02 root, 0x03 picture, 0x04 image, 0x05 palette, 0xFF file info.

Image/palette data header (at block+0x10):
```
0x00 u16 header_len (0x30)   0x02 u16 ?
0x04 u16 format              0x06 u16 pixel_order (0 linear, 1 swizzled)
0x08 u16 width               0x0A u16 height
0x0C u16 bpp                 0x0E u16 pitch_align  0x10 u16 height_align
0x1C u32 pixel_start (relative to header start)
```
Formats: 0 RGBA5650, 1 RGBA5551, 2 RGBA4444, 3 RGBA8888, 4 index4, 5 index8, 6 index16, 7 index32, 8–10 DXT1/3/5.
Swizzle: row bytes padded to 16; height padded to 8; tiles of 16 bytes × 8 rows, row-major tile order.

Observed:
- Wangan Midnight Portable car textures: index4/index8, mostly 256×128 swizzled; body shading is greyscale (paint applied via material).
- Initial D menu labels: index8 512×64 swizzled; glyph atlases: index4 256×256 (16×16 cells), white + alpha.

Encoding new art: always encode into the original as template (`gim.py frompng new.png orig.gim out.gim`) so size, format, palette size and swizzle stay identical. The palette is regenerated (quantize to 16/256 colors with averaged alpha).
