# Containers and compression

## Sega XBB\x01 (Initial D Street Stage)
```
0x00 'XBB\x01' u32 count, pad to 0x20
0x20 count × {u32 offset, u32 size, u32 name_offset, u32 name_hash}
     count × {u32 name_hash, u32 index} sorted by hash
     names (NUL-terminated), data aligned to 0x80
```
Hash function unknown (tested: CRC32 both polys, FNV-1/1a, djb2, sdbm, OAAT, ELF, ×31/×37/×131/×65599). Repack preserving hashes is byte-identical; adding entries requires the hash routine from BOOT.BIN.
Usually wrapped in gzip (`*.bin.gz`) with FNAME set.

## Sega @ANA (2D scene)
`@ANA` u32 0x10, u32 size, u32 0x100, … element names (`PSP_mode_…`) then embedded GIMs. Text labels and help panels are baked into these GIMs. In-place GIM replacement with same byte length is safe; layout geometry is not yet decoded.

## Genki BUILD.TOC / BUILD.DAT (Wangan Midnight Portable)
TOC header 8×u32: count(+1), ?, ?, dat_bytes, 0, ?, 0, 0. Entries 16 bytes: `u32 sector(2048), u32 stored_size, u32 unpacked_size (0 = raw), u32 0`. 8354 entries, no names.
Compressed entries are uclpack (method byte 0x2B, NRV2B with a **LE32 bit buffer**, not the 8-bit variant), blocks `u32 BE dst_len, u32 BE src_len, data`.
Entry content: offset-table packs `u32 n, u32 offsets[n]` (very common), GMO, GIM, PNG, XMD, PPHD sound banks, FNIG records.

## uclpack header
`00 E9 55 43 4C FF 01 1A` + `u32 BE flags, u8 method, u8 level, u32 BE block_size`, blocks until dst_len 0. flags&1 / &2 add Adler-32 fields.

## gzip
Initial D uses standard deflate with FNAME. Repack with `psp_gz.py repack` to keep the name and mtime.
