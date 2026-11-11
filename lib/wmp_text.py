#!/usr/bin/env python3
"""Wangan Midnight Portable (ULJM05264) text packs (BUILD.DAT entries 138-279).

Pack layout (all little-endian):
    u32 n
    u32 offs[n]                       absolute offsets of records
    zero pad up to ((4+4n)//32 + 2) * 32   (== offs[0])
    record[n]:
        u32 0, u32 0xFFFFFFFF          constant record header
        u32 glyph[...]                 indices into the charset (entry 137)
        u32 0x0000FFFF                 terminator
        zero pad: every record except the last occupies (used//32 + 1)*32
                  bytes (always >= 1 pad word); the last record is unpadded.

Glyph index -> character comes from entry 00137 (u16 UTF-16 code per glyph,
3775 glyphs; glyph i is also the i-th cell of font entries 132-135).
Index 0xFFFE inside a string is a line break (rendered here as "\n").
A record containing just "-" is a group separator used by the battle-quote
packs (146-202).

No speaker field exists in the records; the speaker is implied by the pack
(arcade rival packs) or by scene context (scenario packs).

CLI:
    wmp_text.py dump <dir_with_NNNNN.bin> [first last] [--json out.json]
    wmp_text.py test <dir_with_NNNNN.bin>      round-trip every pack
"""
import json
import os
import struct
import sys

NEWLINE = 0xFFFE
TERM = 0xFFFF


def load_charset(entry137: bytes):
    codes = struct.unpack('<%dH' % (len(entry137) // 2), entry137)
    table = [chr(c) for c in codes]
    rev = {}
    for i, ch in enumerate(table):
        rev.setdefault(ch, i)
    return table, rev


def is_text_pack(data: bytes) -> bool:
    if len(data) < 16:
        return False
    n = struct.unpack_from('<I', data)[0]
    if not 0 < n < 4096 or 4 + 4 * n > len(data):
        return False
    o0 = struct.unpack_from('<I', data, 4)[0]
    if o0 != ((4 + 4 * n) // 32 + 2) * 32 or o0 + 8 > len(data):
        return False
    return struct.unpack_from('<II', data, o0) == (0, 0xFFFFFFFF)


def parse(data: bytes):
    """Return list of glyph-index lists (one per record, terminator stripped)."""
    n = struct.unpack_from('<I', data)[0]
    offs = list(struct.unpack_from('<%dI' % n, data, 4)) + [len(data)]
    recs = []
    for k in range(n):
        o = offs[k]
        h = struct.unpack_from('<II', data, o)
        if h != (0, 0xFFFFFFFF):
            raise ValueError('record %d: unexpected header %r' % (k, h))
        glyphs = []
        p = o + 8
        while True:
            w = struct.unpack_from('<I', data, p)[0]
            p += 4
            if w == TERM:
                break
            glyphs.append(w)
        recs.append(glyphs)
    return recs


def build(recs):
    n = len(recs)
    out = bytearray(struct.pack('<I', n) + b'\0' * (4 * n))
    out += b'\0' * (((4 + 4 * n) // 32 + 2) * 32 - len(out))
    offs = []
    for k, glyphs in enumerate(recs):
        offs.append(len(out))
        body = struct.pack('<II', 0, 0xFFFFFFFF) + struct.pack('<%dI' % len(glyphs), *glyphs) + struct.pack('<I', TERM)
        if k < n - 1:
            body += b'\0' * ((len(body) // 32 + 1) * 32 - len(body))
        out += body
    struct.pack_into('<%dI' % n, out, 4, *offs)
    return bytes(out)


def decode(glyphs, table):
    s = []
    for g in glyphs:
        if g == NEWLINE:
            s.append('\n')
        elif g < len(table):
            s.append(table[g])
        else:
            s.append('{%x}' % g)
    return ''.join(s)


def encode(text, rev):
    out = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == '\n':
            out.append(NEWLINE)
        elif ch == '{' and '}' in text[i:]:
            j = text.index('}', i)
            out.append(int(text[i + 1:j], 16))
            i = j
        else:
            out.append(rev[ch])
        i += 1
    return out


def _pack_ids(d, lo=138, hi=279):
    for i in range(lo, hi + 1):
        p = os.path.join(d, '%05d.bin' % i)
        if os.path.exists(p):
            yield i, p


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    cmd, d = sys.argv[1], sys.argv[2]
    table, rev = load_charset(open(os.path.join(d, '00137.bin'), 'rb').read())
    if cmd == 'test':
        ok = bad = 0
        for i, p in _pack_ids(d):
            data = open(p, 'rb').read()
            if not is_text_pack(data):
                continue
            recs = parse(data)
            # binary round-trip and text-level round-trip
            recs2 = [encode(decode(r, table), rev) for r in recs]
            if build(recs) == data and build(recs2) == data:
                ok += 1
            else:
                bad += 1
                print('MISMATCH', i)
        print('round-trip ok=%d bad=%d' % (ok, bad))
        sys.exit(1 if bad else 0)
    elif cmd == 'dump':
        args = [a for a in sys.argv[3:] if not a.startswith('--')]
        lo, hi = (int(args[0]), int(args[1])) if len(args) >= 2 else (138, 279)
        js = sys.argv[sys.argv.index('--json') + 1] if '--json' in sys.argv else None
        out = []
        for i, p in _pack_ids(d, lo, hi):
            data = open(p, 'rb').read()
            if not is_text_pack(data):
                continue
            n = struct.unpack_from('<I', data)[0]
            offs = struct.unpack_from('<%dI' % n, data, 4)
            for k, r in enumerate(parse(data)):
                t = decode(r, table)
                out.append({'id': i, 'index': k, 'offset': offs[k], 'text': t})
                if not js:
                    print('%05d %3d 0x%05x %s' % (i, k, offs[k], t.replace('\n', '／')))
        if js:
            json.dump(out, open(js, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
            print('wrote %d strings to %s' % (len(out), js))


if __name__ == '__main__':
    main()
