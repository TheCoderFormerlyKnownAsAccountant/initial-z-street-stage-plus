#!/usr/bin/env python3
"""XBB name hash (BOOT.BIN vaddr 0x140d6c), seed = XBB header u32 @0x0c (0 in stock files)."""
import struct, sys
def xbb_hash(name, seed=0):
    h = 0; acc = 0
    for ch in name.encode('shift_jis') if isinstance(name, str) else name:
        c = ch - 256 if ch >= 128 else ch          # lb = signed byte
        acc = (acc + c) & 0xffffffff
        s = acc & 31
        cu = c & 0xffffffff
        sra = (c >> ((32 - s) & 31)) & 0xffffffff  # srav on signed value
        t = ((cu << s) & 0xffffffff) | sra
        s2 = c & 31
        r = ((seed << s2) & 0xffffffff) | (seed >> ((32 - s2) & 31) if s2 else seed)
        if s2 == 0: r = seed | seed
        h = (h + t + r) & 0xffffffff
    return h
if __name__ == '__main__':
    sys.path.insert(0, 'lib')
    import xbb
    d = open(sys.argv[1], 'rb').read(); seed = struct.unpack_from('<I', d, 0xc)[0]
    ok = bad = 0
    for e in xbb.parse(d):
        if xbb_hash(e['name'], seed) == e['hash']: ok += 1
        else:
            bad += 1
            if bad < 5: print('MISMATCH', e['name'], hex(e['hash']), hex(xbb_hash(e['name'], seed)))
    print(f'seed={seed:#x} ok={ok} bad={bad}')
