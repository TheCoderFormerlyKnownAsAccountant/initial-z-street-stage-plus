#!/usr/bin/env python3
"""M46 TALK boot patch.  m46_talk_boot.py IN OUT [--json patch46t.json]
IN = BOOT45PRH.BIN (73311b21...) or any chained BOOT with the stock talk loader/runner and an
all-zero region [0x594250, 0x597000) inside the loaded segment (written in place)."""
import json, os, struct, sys
sys.path.insert(0, 'work/m19/c')
import m19_c_boot as C
OFF, R_26 = 0x54, 4
REGION_START, REGION_END = 0x594250, 0x597000
MARKER = b'M46 TALK\0'
HERE = os.path.dirname(os.path.abspath(__file__))
J = lambda op, t: (op << 26) | ((t >> 2) & 0x3ffffff)

def build(src, dst, jpath=None):
    d = bytearray(open(src, 'rb').read())
    phoff = struct.unpack_from('<I', d, 0x1c)[0]
    p = list(struct.unpack_from('<8I', d, phoff)); filesz, memsz = p[4], p[5]
    assert filesz == memsz
    seg_end = OFF + filesz
    if MARKER in d[OFF:seg_end]: sys.exit('already patched (M46 TALK marker present)')
    if memsz < REGION_END: sys.exit('segment does not cover the region (expects a chained BOOT45PRH)')
    if any(d[OFF + REGION_START:OFF + REGION_END]): sys.exit('region 0x594250-0x596fff not empty')
    u32 = lambda va: struct.unpack_from('<I', d, va + OFF)[0]
    shoff = struct.unpack_from('<I', d, 0x20)[0]; shn, shstr = struct.unpack_from('<HH', d, 0x30)
    sh = [list(struct.unpack_from('<10I', d, shoff + 40 * i)) for i in range(shn)]
    nmo = sh[shstr][4]; nm = lambda s: d[nmo + s[0]:d.index(b'\0', nmo + s[0])].decode()
    reldata = [i for i, s in enumerate(sh) if nm(s) == '.rel.data'][0]
    rel = {}
    for s in sh:
        if s[1] != 0x700000a0: continue
        for k in range(s[5] // 8):
            v, t = struct.unpack_from('<II', d, s[4] + 8 * k); rel[v] = t
    patches, newrel = [], []
    def put(va, new, why, expect, keeprel=False):
        old = u32(va)
        if old != expect: raise SystemExit(f'{va:#x}: expected {expect:08x} found {old:08x} ({why})')
        if keeprel: assert rel.get(va) == R_26, (hex(va), rel.get(va))
        elif va in rel: raise SystemExit(f'{va:#x} is relocated ({why})')
        struct.pack_into('<I', d, va + OFF, new)
        patches.append({'vaddr': f'{va:#x}', 'old': f'{old:08x}', 'new': f'{new:08x}', 'why': why})
    region = bytearray(MARKER) + bytes((-len(MARKER)) % 16)
    CODE = REGION_START + len(region)
    words, crel, L = C.asm(open(os.path.join(HERE, 'm46_talk.s')).read(), CODE, {})
    region += struct.pack('<%dI' % len(words), *words)
    newrel += crel
    region += bytes((-len(region)) % 16)
    assert REGION_START + len(region) <= REGION_END
    put(0xcdc0c, 0x24440002, 'token malloc len+1 -> len+2 (room for the 0x01 text prefix)', 0x24440001)
    put(0xcdc40, J(3, L['TCPY']), 'token strcpy -> TCPY (prefix text-shaped tokens with 0x01)', J(3, 0x3e00c), keeprel=True)
    put(0xcfa80, J(3, L['TMEAS']), 'text queue 0xb7bac -> TMEAS (skip the 0x01 prefix)', J(3, 0xb7bac), keeprel=True)
    d[OFF + REGION_START:OFF + REGION_START + len(region)] = region
    # append relocs to .rel.data (shift everything after it)
    relbytes = b''.join(struct.pack('<II', v, t) for v, t in newrel)
    rd_end = sh[reldata][4] + sh[reldata][5]
    out = bytearray(d[:rd_end]) + relbytes + d[rd_end:]
    new_shoff = shoff + (len(relbytes) if shoff >= rd_end else 0)
    struct.pack_into('<I', out, 0x20, new_shoff)
    for i, s in enumerate(sh):
        if s[1] != 8 and s[4] >= rd_end: s[4] += len(relbytes)
        if i == reldata: s[5] += len(relbytes)
        struct.pack_into('<10I', out, new_shoff + 40 * i, *s)
    open(dst, 'wb').write(out)
    info = {'region': f'{REGION_START:#x}-{REGION_START + len(region) - 1:#x}', 'labels': {k: hex(v) for k, v in L.items()},
            'code_words': len(words), 'patches': len(patches), 'new_relocs': len(newrel)}
    if jpath: json.dump({'info': info, 'code_patches': patches, 'new_relocs': [[hex(v), t] for v, t in newrel]}, open(jpath, 'w'), indent=1)
    return info

if __name__ == '__main__':
    a = sys.argv[1:]; jp = None
    if '--json' in a: i = a.index('--json'); jp = a[i + 1]; del a[i:i + 2]
    print(json.dumps(build(a[0], a[1], jp), indent=1))
