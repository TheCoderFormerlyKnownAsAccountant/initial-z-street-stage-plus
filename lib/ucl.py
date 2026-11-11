#!/usr/bin/env python3
"""uclpack container reader (magic 00 E9 55 43 4C FF 01 1A), NRV2B/2D/2E.

Builds libnrv.so from nrv.c on first use (needs gcc). Used by Genki-era PSP
titles such as Wangan Midnight Portable (BUILD.DAT).
"""
import ctypes, os, struct, subprocess, sys

MAGIC = b'\x00\xe9UCL\xff\x01\x1a'
_HERE = os.path.dirname(os.path.abspath(__file__))
_LIB = None
_PREF = [1]  # last bit-buffer width that worked (1 = LE32, Genki's choice)


def _lib():
    global _LIB
    if _LIB is None:
        so = os.path.join(os.environ.get('PSP_REMIX_CACHE', '/tmp'), 'libnrv2.so')
        if not os.path.exists(so):
            subprocess.check_call(['gcc', '-O2', '-shared', '-fPIC', os.path.join(_HERE, 'nrv.c'), '-o', so])
        _LIB = ctypes.CDLL(so)
        _LIB.nrv_decompress.restype = ctypes.c_long
        _LIB.nrv_decompress.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_char_p, ctypes.c_size_t, ctypes.c_char_p, ctypes.c_size_t]
    return _LIB


def is_ucl(data):
    return data[:8] == MAGIC


def decompress(data):
    if not is_ucl(data):
        raise ValueError('not a uclpack stream')
    flags, method, level, block = struct.unpack_from('>IBBI', data, 8)
    pos = 18
    out = bytearray()
    lib = _lib()
    while True:
        (dst_len,) = struct.unpack_from('>I', data, pos); pos += 4
        if dst_len == 0:
            break
        (src_len,) = struct.unpack_from('>I', data, pos); pos += 4
        if flags & 1:  # adler32 of uncompressed
            pos += 4
        if flags & 2:  # adler32 of compressed
            pos += 4
        chunk = data[pos:pos + src_len]; pos += src_len
        if src_len == dst_len:
            out += chunk
        else:
            buf = ctypes.create_string_buffer(dst_len)
            r = -9
            for bits32 in ((1, 0) if _PREF[0] else (0, 1)):
                r = lib.nrv_decompress(method, bits32, bytes(chunk) + b'\0' * 8, src_len, buf, dst_len)
                if r == dst_len:
                    _PREF[0] = bits32
                    break
            if r != dst_len:
                raise ValueError(f'NRV decode failed method={method:#x} r={r} want={dst_len}')
            out += buf.raw
        if pos >= len(data):
            break
    return bytes(out)


def store(data, block=0x40000):
    """Wrap raw bytes in a valid uclpack container using stored blocks (no compression).
    Every NRV decoder accepts src_len == dst_len as a stored block."""
    out = bytearray(MAGIC + struct.pack('>IBBI', 0, 0x2b, 7, block))
    for i in range(0, len(data), block):
        c = data[i:i + block]
        out += struct.pack('>II', len(c), len(c)) + c
    out += struct.pack('>I', 0)
    return bytes(out)


if __name__ == '__main__':
    src, dst = sys.argv[1:3]
    open(dst, 'wb').write(decompress(open(src, 'rb').read()))
