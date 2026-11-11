#!/usr/bin/env python3
"""Replace every copy of a texture (exact GIM bytes) inside XBB/gz archives.

  gim_swap.py OLD.gim NEW.gim OUT_DIR ARCHIVE[.gz] ...
Games reuse the same texture (e.g. a car-name atlas) in many screens. This finds the
old GIM bytes inside every entry of each archive, swaps in the new bytes (same length
required), repacks the XBB, re-gzips with the original header, and reports counts.
"""
import os, sys, gzip
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xbb, psp_gz


def swap(old, new, path, out_dir):
    raw = open(path, 'rb').read()
    is_gz = raw[:2] == b'\x1f\x8b'
    data = gzip.decompress(raw) if is_gz else raw
    n = data.count(old)
    if not n:
        return 0
    if data[:4] == b'XBB\x01':
        ents = xbb.parse(data)
        blobs = [data[e['offset']:e['offset'] + e['size']].replace(old, new) for e in ents]
        out = xbb.build(ents, blobs)
    else:
        out = data.replace(old, new)
    os.makedirs(out_dir, exist_ok=True)
    name = os.path.basename(path)
    if is_gz:
        open(os.path.join(out_dir, name), 'wb').write(psp_gz.repack(raw, out))
        open(os.path.join(out_dir, name[:-3]), 'wb').write(out)
    else:
        open(os.path.join(out_dir, name), 'wb').write(out)
    return n


if __name__ == '__main__':
    old = open(sys.argv[1], 'rb').read(); new = open(sys.argv[2], 'rb').read()
    assert len(old) == len(new), 'GIM sizes differ'
    for p in sys.argv[4:]:
        print(p, swap(old, new, p, sys.argv[3]), 'copies')
