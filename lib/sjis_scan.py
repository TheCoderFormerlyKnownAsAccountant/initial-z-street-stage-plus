#!/usr/bin/env python3
"""Find Shift-JIS strings in binaries (EBOOT/BOOT.BIN, layout files, tables).

  sjis_scan.py FILE [--min 2] [--json OUT.json] [--base 0x08804000]

Emits offset, byte length, and decoded text for every run of >= --min
double-byte JIS characters (ASCII allowed inside a run). With --base, also
prints the PSP virtual address (ELF segment base) so code xrefs can be found.
JSON output is the input format for translate.py.
"""
import argparse, json, sys


def is_lead(b):
    return 0x81 <= b <= 0x9f or 0xe0 <= b <= 0xfc


def scan(d, min_dbcs=2):
    out = []; i = 0; n = len(d)
    while i < n:
        j = i; dbcs = 0; ok = True
        while j < n:
            b = d[j]
            if is_lead(b) and j + 1 < n and 0x40 <= d[j + 1] <= 0xfc and d[j + 1] != 0x7f:
                try:
                    d[j:j + 2].decode('shift_jis')
                except UnicodeDecodeError:
                    break
                dbcs += 1; j += 2
            elif 0x20 <= b < 0x7f or b in (0x0a, 0x0d) or 0xa1 <= b <= 0xdf:
                j += 1
            else:
                break
        if dbcs >= min_dbcs:
            raw = d[i:j]
            try:
                txt = raw.decode('shift_jis')
                term = d[j] if j < n else None
                out.append({'offset': i, 'length': j - i, 'nul_terminated': term == 0, 'text': txt})
            except UnicodeDecodeError:
                pass
            i = j
        else:
            i = max(j, i + 1)
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('file'); ap.add_argument('--min', type=int, default=2)
    ap.add_argument('--json'); ap.add_argument('--base', type=lambda x: int(x, 0), default=None)
    ap.add_argument('--file-offset', type=lambda x: int(x, 0), default=0, help='ELF segment file offset (for --base)')
    a = ap.parse_args()
    d = open(a.file, 'rb').read(); res = scan(d, a.min)
    for r in res:
        if a.base is not None:
            r['vaddr'] = a.base + r['offset'] - a.file_offset
    if a.json:
        json.dump(res, open(a.json, 'w'), ensure_ascii=False, indent=1)
    for r in res:
        va = f" va={r['vaddr']:#010x}" if 'vaddr' in r else ''
        print(f"{r['offset']:#08x} len={r['length']:<4}{va} {r['text'][:80]!r}")
    print(f'{len(res)} strings', file=sys.stderr)
