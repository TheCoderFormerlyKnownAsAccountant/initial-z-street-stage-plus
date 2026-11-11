#!/usr/bin/env python3
"""Wangan Midnight Portable BUILD.TOC / BUILD.DAT archive tool (Genki format).

TOC layout (little-endian):
  header 32 bytes: u32 count(+1 sentinel), u32 ?, u32 ?, u32 dat_bytes, u32 0, u32 ?, u32 0, u32 0
  entries 16 bytes each: u32 sector, u32 stored_size, u32 unpacked_size (0 = stored raw), u32 0
Compressed entries are uclpack streams (NRV2B, LE32 bit buffer).
Files have no names; ids are entry indexes. `catalog` guesses types by magic.

Usage:
  wmp_build.py unpack  BUILD.TOC BUILD.DAT OUT_DIR
  wmp_build.py repack  BUILD.TOC BUILD.DAT MOD_DIR OUT_TOC OUT_DAT
     MOD_DIR holds replacement files named <id>.bin (decompressed). They are
     stored raw (unpacked_size = 0) and appended to the DAT; TOC sectors updated.
"""
import json, os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ucl
from magic import guess

SECTOR = 2048


def read_toc(p):
    t = open(p, 'rb').read()
    hdr = list(struct.unpack_from('<8I', t, 0))
    n = (len(t) - 32) // 16
    return hdr, [list(struct.unpack_from('<4I', t, 32 + 16 * i)) for i in range(n)]


def unpack(toc, dat, out):
    hdr, ents = read_toc(toc)
    d = open(dat, 'rb').read()
    os.makedirs(out, exist_ok=True)
    cat = []
    for i, (sec, sz, usz, _) in enumerate(ents):
        raw = d[sec * SECTOR: sec * SECTOR + sz]
        data = ucl.decompress(raw) if usz else raw
        open(os.path.join(out, f'{i:05d}.bin'), 'wb').write(data)
        cat.append({'id': i, 'sector': sec, 'stored': sz, 'size': len(data), 'compressed': bool(usz), 'type': guess(data)})
    json.dump({'header': hdr, 'entries': cat}, open(os.path.join(out, '_catalog.json'), 'w'), indent=0)
    print(f'unpacked {len(ents)} entries to {out}')


def repack(toc, dat, mods, otoc, odat):
    hdr, ents = read_toc(toc)
    import shutil
    shutil.copyfile(dat, odat)
    with open(odat, 'r+b') as fp:
        fp.seek(0, 2)
        end = (fp.tell() + SECTOR - 1) // SECTOR
        for f in sorted(os.listdir(mods)):
            if not f.endswith('.bin'):
                continue
            i = int(f.split('.')[0])
            data = open(os.path.join(mods, f), 'rb').read()
            alloc = (ents[i][1] + SECTOR - 1) // SECTOR * SECTOR
            sec = ents[i][0] if len(data) <= alloc else end
            if sec == end:
                end += (len(data) + SECTOR - 1) // SECTOR
            fp.seek(sec * SECTOR); fp.write(data + b'\0' * ((-len(data)) % SECTOR))
            ents[i] = [sec, len(data), 0, 0]
            print(f'entry {i}: {len(data)} bytes @ sector {sec}')
        fp.seek(0, 2); size = fp.tell()
    hdr[3] = size
    out = struct.pack('<8I', *hdr) + b''.join(struct.pack('<4I', *e) for e in ents)
    open(otoc, 'wb').write(out)
    print('wrote', otoc, odat)


if __name__ == '__main__':
    c = sys.argv[1]
    if c == 'unpack':
        unpack(*sys.argv[2:5])
    elif c == 'repack':
        repack(*sys.argv[2:7])
    else:
        print(__doc__)
