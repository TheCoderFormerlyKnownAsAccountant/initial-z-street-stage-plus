#!/usr/bin/env python3
"""Sega XBB\\x01 container (Initial D Street Stage menus, garage, Bunta, title...).

Layout (little-endian):
  0x00 'XBB\\x01'  u32 count  (pad to 0x20)
  0x20 count * {u32 offset, u32 size, u32 name_offset, u32 name_hash}
  then count * {u32 name_hash, u32 index} sorted by hash (lookup table)
  then NUL-terminated names, then file data (128-byte aligned).
The name hash function is not yet identified (not CRC32/FNV/djb2). Repacking
keeps every original hash, so replacing files is safe; ADDING files needs the
hash routine from BOOT.BIN.

  xbb.py list   IN.bin
  xbb.py unpack IN.bin OUT_DIR
  xbb.py repack IN.bin MOD_DIR OUT.bin      # files in MOD_DIR replace same-named entries
"""
import json, os, struct, sys

ALIGN = 0x80


def parse(d):
    if d[:4] != b'XBB\x01':
        raise ValueError('not XBB')
    n = struct.unpack_from('<I', d, 4)[0]
    ents = []
    for i in range(n):
        o, s, no, h = struct.unpack_from('<4I', d, 0x20 + 16 * i)
        name = d[no:d.index(b'\0', no)].decode('ascii', 'replace')
        ents.append({'name': name, 'offset': o, 'size': s, 'hash': h})
    return ents


def build(ents, blobs):
    n = len(ents)
    hdr = bytearray(b'XBB\x01' + struct.pack('<I', n) + b'\0' * 24)
    table_off = 0x20; lut_off = table_off + 16 * n; names_off = lut_off + 8 * n
    names = bytearray(); name_pos = []
    for e in ents:
        name_pos.append(names_off + len(names)); names += e['name'].encode() + b'\0'
    data_off = (names_off + len(names) + ALIGN - 1) // ALIGN * ALIGN
    out = bytearray(data_off)
    out[:0x20] = hdr
    pos = data_off; body = bytearray()
    for i, (e, b) in enumerate(zip(ents, blobs)):
        struct.pack_into('<4I', out, table_off + 16 * i, pos, len(b), name_pos[i], e['hash'])
        body += b + b'\0' * ((-len(b)) % ALIGN); pos += len(b) + ((-len(b)) % ALIGN)
    for k, (h, i) in enumerate(sorted((e['hash'], i) for i, e in enumerate(ents))):
        struct.pack_into('<II', out, lut_off + 8 * k, h, i)
    out[names_off:names_off + len(names)] = names
    return bytes(out + body)


def main():
    cmd, src = sys.argv[1], sys.argv[2]
    d = open(src, 'rb').read(); ents = parse(d)
    if cmd == 'list':
        for e in ents:
            print(f"{e['offset']:#09x} {e['size']:>9} {e['hash']:08x} {e['name']}")
    elif cmd == 'unpack':
        out = sys.argv[3]; os.makedirs(out, exist_ok=True)
        for e in ents:
            open(os.path.join(out, e['name']), 'wb').write(d[e['offset']:e['offset'] + e['size']])
        json.dump(ents, open(os.path.join(out, '_xbb.json'), 'w'), indent=1)
    elif cmd == 'repack':
        mods, dst = sys.argv[3], sys.argv[4]
        blobs = []
        for e in ents:
            p = os.path.join(mods, e['name'])
            blobs.append(open(p, 'rb').read() if os.path.exists(p) else d[e['offset']:e['offset'] + e['size']])
        open(dst, 'wb').write(build(ents, blobs))
        print('wrote', dst)


if __name__ == '__main__':
    main()
