#!/usr/bin/env python3
"""gzip helpers that keep the original header (FNAME, MTIME, OS) so the game's
loader sees exactly what it expects.

  psp_gz.py unpack IN.gz OUT
  psp_gz.py repack ORIG.gz NEWDATA OUT.gz     # copies ORIG's header fields
"""
import struct, sys, zlib


def header(gz):
    if gz[:2] != b'\x1f\x8b':
        raise ValueError('not gzip')
    flg = gz[3]; mtime = struct.unpack_from('<I', gz, 4)[0]; xfl, os_ = gz[8], gz[9]
    p = 10; name = None
    if flg & 4:
        p += 2 + struct.unpack_from('<H', gz, p)[0]
    if flg & 8:
        e = gz.index(b'\0', p); name = gz[p:e]; p = e + 1
    return flg, mtime, xfl, os_, name


def repack(orig, data):
    flg, mtime, xfl, os_, name = header(orig)
    out = bytearray(b'\x1f\x8b\x08' + bytes([8 if name else 0]) + struct.pack('<I', mtime) + bytes([2, os_]))
    if name:
        out += name + b'\0'
    c = zlib.compressobj(9, zlib.DEFLATED, -15, 9)
    out += c.compress(data) + c.flush()
    out += struct.pack('<II', zlib.crc32(data) & 0xffffffff, len(data) & 0xffffffff)
    return bytes(out)


if __name__ == '__main__':
    import gzip
    if sys.argv[1] == 'unpack':
        open(sys.argv[3], 'wb').write(gzip.decompress(open(sys.argv[2], 'rb').read()))
    elif sys.argv[1] == 'repack':
        o = open(sys.argv[2], 'rb').read(); d = open(sys.argv[3], 'rb').read()
        out = repack(o, d)
        assert gzip.decompress(out) == d
        open(sys.argv[4], 'wb').write(out)
        print(f'{sys.argv[4]}: {len(out)} bytes (orig {len(o)})')
