#!/usr/bin/env python3
"""M61 STREET LEGENDS AKIO = PURE RECORD PACE (v1.0.1).   m61_akio_boot.py IN OUT [--json patch61.json]
IN = BOOT59 (kit bedc18a1 / private a3a026ad). Street Legends only; Devil Z Challenge unchanged.
1) SL RB_ADD (RBA[1], 0x5a622c) 2.0 -> -1000.0: target = max(line*GAIN, min(player-1000, ...)) = line*GAIN, i.e. Akio
   drives his own record line and no longer copies the player's speed (+2 km/h).
2) SL GAIN Wangan (0x5a6308) 1.15 -> 1.08 (~1'29"5) and Hakone (0x5a630c) 1.18 -> 1.10 (~2'13" up / 2'10" down).
3) Wangan/Hakone catch-up: hW (M37B) multiplied every rival's target by WBEH 1.08 while behind. 0x57ccf0 `mul.s f3,f3,f0`
   -> `jal BEH61`; BEH61 skips the multiply for SL Akio (G0 != 2, AKFLAG == 0, enemy G0+0x18 == 31, as M41 isak).
   Delay slot = hW_go's `lw t0,0(sp)` (harmless); BEH61 uses only t1/t2 (restored after) and ra (restored at hW_go).
New code at 0x5a7800 (marker 'M61 SL AKIO'). +1 R_26 reloc (0x57ccf0).
"""
import json, struct, sys, hashlib
sys.path.insert(0, 'work/m19/c')
import m19_c_boot as C
OFF, R_26 = 0x54, 4
G0, AKFLAG = 0x490f08, 0x554180
SITE, RBA_SL, GT_SL = 0x57ccf0, 0x5a622c, 0x5a62c8
BASE = 0x5a7800
MARKER = b'M61 SL AKIO\0\0\0\0\0'
NEW = {RBA_SL: -1000.0, GT_SL + 16 * 4: 1.08, GT_SL + 17 * 4: 1.10}
OLD = {RBA_SL: 2.0, GT_SL + 16 * 4: 1.15, GT_SL + 17 * 4: 1.18}
SRC = """
BEH61:
    lui t1,%hi(G0)
    lw t2,%lo(G0)(t1)
    addiu t1,zero,2
    beq t2,t1,b_mul
    nop
    lui t1,%hi(AKFLAG)
    lbu t2,%lo(AKFLAG)(t1)
    bnez t2,b_mul
    nop
    lui t1,%hi(G0)
    lw t2,%lo(G0+0x18)(t1)
    addiu t1,zero,31
    bne t2,t1,b_mul
    nop
    jr ra
    nop
b_mul:
    jr ra
    mul.s $f3,$f3,$f0
"""
def build(src, dst, jpath=None):
    d = bytearray(open(src, 'rb').read())
    u32 = lambda va: struct.unpack_from('<I', d, va + OFF)[0]
    f32 = lambda va: struct.unpack_from('<f', d, va + OFF)[0]
    if MARKER[:11] in d: sys.exit('already patched')
    assert u32(SITE) == 0x460018C2, hex(u32(SITE))
    assert u32(0x1044e8) == (2 << 26) | (0x57cca8 >> 2)
    for a, v in OLD.items(): assert abs(f32(a) - v) < 1e-4, (hex(a), f32(a))
    assert not any(d[OFF + BASE:OFF + BASE + 0x100])
    shoff = struct.unpack_from('<I', d, 0x20)[0]
    shn, shstr = struct.unpack_from('<HH', d, 0x30)
    sh = [list(struct.unpack_from('<10I', d, shoff + 40 * i)) for i in range(shn)]
    names = sh[shstr][4]
    nm = lambda s: d[names + s[0]:d.index(b'\0', names + s[0])].decode()
    reldata = [i for i, s in enumerate(sh) if nm(s) == '.rel.data'][0]
    rel = {}
    for s in sh:
        if s[1] != 0x700000a0: continue
        for k in range(s[5] // 8):
            v, t = struct.unpack_from('<II', d, s[4] + 8 * k); rel[v] = t
    assert SITE not in rel
    CODE = BASE + 0x10
    words, crel, L = C.asm(SRC, CODE, dict(G0=G0, AKFLAG=AKFLAG))
    d[OFF + BASE:OFF + BASE + 16] = MARKER
    struct.pack_into('<%dI' % len(words), d, OFF + CODE, *words)
    struct.pack_into('<I', d, OFF + SITE, (3 << 26) | (L['BEH61'] >> 2))
    crel = list(crel) + [(SITE, R_26)]
    for a, v in NEW.items(): struct.pack_into('<f', d, OFF + a, v)
    relbytes = b''.join(struct.pack('<II', v, t) for v, t in crel)
    rd_end = sh[reldata][4] + sh[reldata][5]
    out = d[:rd_end] + relbytes + d[rd_end:]
    if shoff >= rd_end: shoff += len(relbytes)
    struct.pack_into('<I', out, 0x20, shoff)
    for i, s in enumerate(sh):
        if s[4] >= rd_end and i != reldata and s[1] != 8: s[4] += len(relbytes)
        if i == reldata: s[5] += len(relbytes)
        struct.pack_into('<10I', out, shoff + 40 * i, *s)
    open(dst, 'wb').write(out)
    info = dict(labels={k: hex(v) for k, v in L.items()}, new_relocs=[[hex(v), t] for v, t in crel],
                words=[f'{w:08x}' for w in words], md5=hashlib.md5(out).hexdigest())
    print(json.dumps(info, indent=1))
    if jpath: json.dump(info, open(jpath, 'w'), indent=1)
if __name__ == '__main__':
    build(sys.argv[1], sys.argv[2], sys.argv[4] if len(sys.argv) > 4 else None)
