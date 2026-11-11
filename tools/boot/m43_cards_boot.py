#!/usr/bin/env python3
"""M41 CARDS: new card-earning rules + 10-card card-get screen.
   m41_cards_boot.py IN OUT [--json patch41c.json]
IN = BOOT41A.BIN (build 40 release BOOT 4080f8a2... + M41 AURA, md5 7d9ecc7f...). Region [0x58a800, 0x58c000).

Rules (data block DB, all tunable words):
  * Street Legends / Challenge (Bunta, Akio) / any rival race:  WIN -> NWIN (10) cards, LOSE -> NLOSE (3) cards.
  * Time Attack finish -> NTA (10) cards.
  * Every card is awarded (no more "choose 1 of 3").
  * Each card: with AURA_PCT % (5) an aura card (0-based 185..190, uniform) -- never on a loss; otherwise the stock
    weighted row of card_probability.txt for that race (SL rival row WIN/LOSE, TA course/direction row, Challenge
    course WIN/LOSE row). Duplicates are allowed. A pick is rejected when the card's count (save + same batch)
    would exceed 99, when it is out of range, or (loss) an aura; after MAXTRY (16) rejected picks a uniform scan
    from a random start finds any non-maxed card; if every card is maxed the batch just has fewer cards. No loop
    can spin forever.
  * Row clamps (old variant H / Miki fixes are inside the replaced block, so redone here): rival 17 (Miki) -> 16,
    rival >= 31 (Akio) -> 30; course >= 8 (Akina Snow) -> 3; direction > 1 -> 0.
  * Card-scene gate 0x8c3c0: stock = (outcome < 2 and mode != 3). New: also mode 2 (Challenges) on any outcome
    (a lost Challenge has outcome >= 2, which stock skipped) when MODE2ALL = 1.
Screen:
  * card list allocated for 10 entries (was 3): 0x18b5e4 size 0x64 -> 0x128, 0x18b604 count 3 -> 10, 0x18b7f8 loop 3 -> 10.
  * 0x18b898 (jal 0xe7b18 just before the stock pick loops) -> PRE: same call, then PICK (picks, loads the N card
    pictures data/card/pic/PSP_%03d.gim exactly like the stock loop) -> 0x18bac4 (stock specials etc. unchanged).
  * state 0 handler 0x18bf60 jal 0x18c0f4 -> MYST0: lays the N cards out (N <= 3: one row, 86x130 at x 90/240/390;
    N > 3: 5x2 grid 66x101), awards all of them (0x14e788), flips them face-up one after another, waits for O
    (0x2000) or 600 frames, then leaves exactly like stock (specials -> state 2, else 0x18df88 -> 2/5).
  * draw state 0 loop 0x18c03c -> MYDRAW (draws NCARDS entries); fade loops 0x18cf08/0x18cf58 3 -> 10.
  * kousai (selection glow) moved off-screen; the "Please choose a card." bar (PSP_cardget2 tex 0) is relabelled
    "You got these cards!" in result.bin (assets script).
"""
import json, struct, sys
sys.path.insert(0, 'work/m19/c')
import m19_c_boot as C
OFF = 0x54
R_26 = 4
REGION_START, REGION_END = 0x593000, 0x594000
MARKER = b'M43 CARDS THUMB\0'
G0, SAVE = 0x490f08, 0x491ef8
MSGLST, MSGPFX = 0x23eecc, 0x23eed8   # 'msg_lst.txt', 'msg' (result.bin message font)

SRC = open(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "m43_cards.s")).read()

import json as _j
NAMES = {int(k): v for k, v in _j.load(open(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "names12.json"))).items()}
DEFAULTS = dict(NWIN=10, NLOSE=5, NTA=10, AURA_PCT=5, MAXTRY=16, MODE2ALL=1, FLIPF=12, STAG=3, MINWAIT=45)
# one row (N <= 5): thumbnail x1.5; grid (N > 5): thumbnail x1 (card 55x81 inside the 64x128 PSP_s_NNN.gim)
ONE = dict(w=82, h=121, cy=96, namey=160, tagy=104)
GRID = dict(w=55, h=81, cy=(48, 150), namey=(91, 193), tagy=(52, 154))
NAMEFILE = 'cardname12.bin'   # new result.bin XBB entry: 191 x 12-byte centred ASCII name fields
OLD = dict(PRE=0x58a910, MYST0=0x58ace8, MYDRAW=0x58af54, GATE=0x58af9c)   # M41 targets in BOOT42K


def build(src, dst, jpath=None):
    d = bytearray(open(src, 'rb').read())
    u32 = lambda va: struct.unpack_from('<I', d, va + OFF)[0]
    patches, newrel = [], []
    phoff = struct.unpack_from('<I', d, 0x1c)[0]
    p = list(struct.unpack_from('<8I', d, phoff))
    filesz, memsz = p[4], p[5]
    assert filesz == memsz
    seg_end = OFF + filesz
    if MARKER in d[OFF:seg_end]: sys.exit('already patched')
    for mk in (b'M28 W RSV', b'M41 AURA KMH', b'M41 CARDS10', b'M42 CHALLENGE AKIO'):
        if mk not in d[OFF:seg_end]: sys.exit(f'input lacks {mk}')
    if memsz > REGION_START: sys.exit('input already extends into the M43 cards region')
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

    def put(va, new, why, expect, keeprel=False, addrel=False):
        old = u32(va)
        if old != expect: raise SystemExit(f'{va:#x}: expected {expect:08x} found {old:08x} ({why})')
        if keeprel: assert rel.get(va) == R_26, (hex(va), rel.get(va))
        elif va in rel: raise SystemExit(f'{va:#x} is relocated ({why})')
        if addrel: newrel.append((va, R_26))
        struct.pack_into('<I', d, va + OFF, new)
        patches.append({'vaddr': f'{va:#x}', 'old': f'{old:08x}', 'new': f'{new:08x}', 'why': why})

    region = bytearray()
    def alloc(n, align=16):
        while (REGION_START + len(region)) % align: region.append(0)
        a = REGION_START + len(region); region.extend(b'\0' * n); return a
    alloc(16); region[0:len(MARKER)] = MARKER
    DB = alloc(0x240)
    def dbw(off, v, fmt='<I'): struct.pack_into(fmt, region, DB - REGION_START + off, v)
    for k, o in (('NWIN', 0), ('NLOSE', 4), ('NTA', 8), ('AURA_PCT', 0xc), ('MAXTRY', 0x10), ('MODE2ALL', 0x14),
                 ('FLIPF', 0x34), ('STAG', 0x38), ('MINWAIT', 0x3c)): dbw(o, DEFAULTS[k])
    dbw(0x30, 3.14, '<f')
    fmt = b'data/card/pic/PSP_s_%03d.gim\0'; region[DB - REGION_START + 0xb0:DB - REGION_START + 0xb0 + len(fmt)] = fmt
    dbw(0xd0, ONE['w']); dbw(0xd4, ONE['h']); dbw(0xd8, ONE['namey']); dbw(0xdc, ONE['tagy'])
    dbw(0xe0, GRID['w']); dbw(0xe4, GRID['h'])
    dbw(0xe8, GRID['namey'][0]); dbw(0xec, GRID['tagy'][0]); dbw(0xf0, GRID['namey'][1]); dbw(0xf4, GRID['tagy'][1])
    dbw(0xf8, 55.0, '<f'); dbw(0xfc, 81.0, '<f'); dbw(0x100, 2000.0, '<f'); dbw(0x104, -13.5, '<f')
    dbw(0x108, ONE['cy']); dbw(0x110, GRID['cy'][0]); dbw(0x114, GRID['cy'][1])
    nb = NAMEFILE.encode() + b'\0'; region[DB - REGION_START + 0x220:DB - REGION_START + 0x220 + len(nb)] = nb
    region[DB - REGION_START + 0x230:DB - REGION_START + 0x23c] = b' ' * 12
    NW = 900
    CODE = alloc(4 * NW)
    syms = dict(DB=DB, G0=G0, SAVE=SAVE, MSGLST=MSGLST, MSGPFX=MSGPFX)
    words, crel, L = C.asm(SRC, CODE, syms)
    assert len(words) <= NW, len(words)
    region[CODE - REGION_START:CODE - REGION_START + 4 * len(words)] = struct.pack('<%dI' % len(words), *words)
    region = region[:CODE - REGION_START + 4 * len(words)]
    newrel += crel
    J = lambda op, t: (op << 26) | ((t >> 2) & 0x3ffffff)
    put(0x18b898, J(3, L['PRE']), 'pick/load -> M43 PRE (thumbnails, tags, fonts)', J(3, OLD['PRE']), keeprel=True)
    put(0x18bf60, J(3, L['MYST0']), 'card state 0 -> M43 MYST0 (layout, names, NEW tags)', J(3, OLD['MYST0']), keeprel=True)
    put(0x18c03c, J(2, L['MYDRAW']), 'draw state 0 -> M43 MYDRAW', J(2, OLD['MYDRAW']), keeprel=True)
    put(0x8c3c0, J(2, L['GATE']), 'card-scene gate -> M43 GATE', J(2, OLD['GATE']), keeprel=True)
    put(0x18be04, J(3, L['HFREE']), 'card scene dtor font delete -> HFREE (+ our 8 fonts)', J(3, 0xb765c), keeprel=True)
    region_end = (REGION_START + len(region) + 15) & ~15
    assert region_end <= REGION_END
    region += b'\0' * (region_end - REGION_START - len(region))

    relbytes = b''.join(struct.pack('<II', v, t) for v, t in newrel)
    rd_end = sh[reldata][4] + sh[reldata][5]
    seg = bytes(d[OFF:seg_end]) + bytes(REGION_START - memsz) + bytes(region)
    tail_start = seg_end; new_memsz = region_end
    tail = bytes(d[tail_start:])
    new_tail_start = (OFF + new_memsz + 15) & ~15
    delta = new_tail_start - tail_start
    out = bytearray(d[:OFF]) + seg
    out += b'\0' * (new_tail_start - len(out))
    ins_at = rd_end - tail_start
    out += tail[:ins_at] + relbytes + tail[ins_at:]
    new_shoff = shoff + delta + (len(relbytes) if shoff >= rd_end else 0)
    struct.pack_into('<I', out, 0x20, new_shoff)
    p[4] = p[5] = new_memsz
    struct.pack_into('<8I', out, phoff, *p)
    for i, s in enumerate(sh):
        o = s[4]
        if s[1] != 8 and o >= tail_start: s[4] = o + delta + (len(relbytes) if o >= rd_end else 0)
        if i == reldata: s[5] += len(relbytes)
        struct.pack_into('<10I', out, new_shoff + 40 * i, *s)
    open(dst, 'wb').write(out)
    info = {'input_end': f'{memsz:#x}', 'region': f'{REGION_START:#x}-{region_end - 1:#x}', 'next_free': f'{region_end:#x}',
            'syms': {k: hex(v) for k, v in syms.items()}, 'db': {'NWIN': '+0x00', 'NLOSE': '+0x04', 'NTA': '+0x08',
            'AURA_PCT': '+0x0c', 'MAXTRY': '+0x10', 'MODE2ALL': '+0x14', 'NCARDS': '+0x18', 'MINWAIT': '+0x3c', 'PICKS': '+0x40',
            'TAGN': '+0x68', 'FONTS': '+0x90', 'FMT': '+0xb0', 'ONE': '+0xd0', 'GRID': '+0xe0', 'NAMESP': '+0x118', 'ROWS': '+0x120', 'NAMEFILE': '+0x220', 'BLANK': '+0x230'}, 'defaults': DEFAULTS, 'code_words': len(words),
            'labels': {k: hex(v) for k, v in L.items()}, 'patches': len(patches), 'new_relocs': len(newrel)}
    if jpath:
        json.dump({'info': info, 'code_patches': patches, 'new_relocs': [[hex(v), t] for v, t in newrel]}, open(jpath, 'w'), indent=1)
    return info


if __name__ == '__main__':
    a = sys.argv[1:]; jp = None
    if '--json' in a: i = a.index('--json'); jp = a[i + 1]; del a[i:i + 2]
    print(json.dumps(build(a[0], a[1], jp), indent=1))
