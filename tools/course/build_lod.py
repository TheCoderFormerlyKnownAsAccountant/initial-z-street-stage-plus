"""M47 STREAM: full-detail mid LOD for Wangan and Hakone (data only, no BOOT change).

Engine (BOOT 0x12e000-0x133000, CCourse): per section k three model files
  a  = full model (L slot, 3 slots: k-1..k+1)          size limit = round2K(max a size in gmo_size.tbl)
  S  = XBB {vh_bNN (entry 0, far LOD), vh_cNN (entry 1, mid LOD)} (5 S slots: k-2..k+2)
       slot = round2K(max vh_sub size in gmo_size.tbl) = 290,816 (stock max sub 290,176)
blk_k_d = a(k) padded to 2 KB + S XBB of the next section in direction d. Start archives carry vh_sub_NN.
Stock c = an exact subset of a (~46 % of the triangles, half the scenery). Wangan's c was a bare deck (6 % / 2.5 %),
so every building/light/wall appeared only when the section became an L section (~280 m ahead).
Fix: c(k) := a copy of a(k) (exact same bytes as the full model) wherever b + a fits the S slot; b(k) := a too where
2a fits (Wangan only; Hakone keeps the bent stock b). Zero memory cost: slot sizes (table max) unchanged.
Outputs out/<course>/... + manifest47s.json."""
import sys, os, gzip, zlib, json, hashlib, struct
sys.path.insert(0, 'lib')
import xbb, gmo_tree as G

LIM = 290176                     # stock max vh_sub size (table); S slot = 290,816
OUT = 'work/m47/stream/out'
NAMES = sorted(['a%02d' % i for i in range(29) if i not in (12, 15)] + ['a12b', 'a12c', 'a15a', 'a15b', 'a15c'])
W = 'work/m35/hw/vis/files/'
H = 'work/m45/hakone/vis/files/'
COURSES = {
    'wangan': dict(blk=W + 'vh_blk_%02d_%d.bin', disc_blk='course/happou/vh2/wg_blk_%02d_%d.bin',
                   sub=W + 'vh_sub_%s.bin', disc_sub='course/happou/vh2/wg_sub_%s.bin',
                   start=[(W + 'happou_night_start_data1.gz', 'course/happou/wangan_night_start_data1.gz'),
                          (W + 'happou_night_start_data2.gz', 'course/happou/wangan_night_start_data2.gz')],
                   nd=(W + 'happou_night_data.gz', 'course/happou/wangan_night_data.gz'), b_full=True),
    'hakone': dict(blk=H + 'hk_blk_%02d_%d.bin', disc_blk='course/happou/vh2/hk_blk_%02d_%d.bin', sub=None,
                   start=[(H + 'hakone_night_start_data1.gz', 'course/happou/hakone_night_start_data1.gz'),
                          (H + 'hakone_night_start_data2.gz', 'course/happou/hakone_night_start_data2.gz')],
                   nd=(H + 'hakone_night_data.gz', 'course/happou/hakone_night_data.gz'), b_full=False),
}


def real(g):
    """GMO bytes without trailing padding (header-declared tree only)."""
    t = G.GmoTree.load(g); out = t.head + b''.join(r.dump() for r in t.roots)
    assert g.startswith(out); return out


def _zopfli_deflate(data):
    import zopfli.gzip as ZG
    g = ZG.compress(data, numiterations=15)
    nul = 10
    flg = g[3]
    o = 10
    if flg & 8: o = g.index(b'\0', 10) + 1
    return g[o:-8]


def gz_exact(orig, data):
    nul = orig.index(b'\0', 10); fname = orig[10:nul]; body = None
    for lvl in (9, 8, 7, 6):
        for mem in (9, 8, 7):
            for strat in (zlib.Z_DEFAULT_STRATEGY, zlib.Z_FILTERED):
                c = zlib.compressobj(lvl, zlib.DEFLATED, -15, mem, strat); b = c.compress(data) + c.flush()
                if body is None or len(b) < len(body): body = b
    if len(body) > len(orig) - (10 + len(fname) + 1 + 8):
        import zopfli.zopfli as ZZ
        z = ZZ.compress(data, numiterations=15, gzip_mode=0, format=2) if False else _zopfli_deflate(data)
        if len(z) < len(body): body = z
    tail = (zlib.crc32(data) & 0xffffffff).to_bytes(4, 'little') + len(data).to_bytes(4, 'little')
    extra = len(orig) - (10 + len(fname) + 1 + len(body) + 8)
    if extra < 0: return None
    out = orig[:10] + fname + b'_' * extra + b'\0' + body + tail
    assert len(out) == len(orig) and gzip.decompress(out) == data; return out


def lod_xbb(old, A, b_full):
    """Rebuild one S XBB (entries kept in order with their hashes). Returns (bytes, info)."""
    ents = xbb.parse(old); blobs = [old[e['offset']:e['offset'] + e['size']] for e in ents]
    info = []
    names = [e['name'] for e in ents]
    for i, e in enumerate(ents):
        n = e['name']
        if n[:4] in ('vh_b', 'vh_c', 'vh_s') and n.endswith('.gmo'): blobs[i] = real(blobs[i])
    for i, e in enumerate(ents):
        n = e['name']
        if n[:4] == 'vh_c' and n.endswith('.gmo'):
            a = A.get('a' + n[4:-4])
            trial = list(blobs); trial[i] = a
            if a is not None and len(xbb.build(ents, trial)) <= LIM: blobs = trial; info.append(n + '=a')
    if b_full:
        for i, e in enumerate(ents):
            n = e['name']
            if n[:4] == 'vh_b' and n.endswith('.gmo'):
                a = A.get('a' + n[4:-4])
                trial = list(blobs); trial[i] = a
                if a is not None and len(xbb.build(ents, trial)) <= LIM: blobs = trial; info.append(n + '=a')
    new = xbb.build(ents, blobs)
    assert [x['name'] for x in xbb.parse(new)] == names and len(new) <= max(LIM, len(old))
    return new, info


def r2k(n): return (n + 0x7ff) & ~0x7ff


def table_of(nd_path):
    d = gzip.decompress(open(nd_path, 'rb').read()); ents = xbb.parse(d)
    te = [e for e in ents if e['name'] == 'gmo_size.tbl'][0]
    return {e['name']: e['size'] for e in xbb.parse(d[te['offset']:te['offset'] + te['size']])}


def run(c):
    cfg = COURSES[c]; od = os.path.join(OUT, c); os.makedirs(od, exist_ok=True)
    man = []; A = {}; log = []
    T_old = table_of(cfg['nd'][0])
    for k in range(32):
        b = open(cfg['blk'] % (k, 0), 'rb').read(); i = b.find(b'XBB\x01'); A[NAMES[k]] = real(b[:i])
        assert i == r2k(T_old['vh_' + NAMES[k] + '.gmo']), (k, i)        # head = table a size, 2 KB padded
    # one new LOD XBB per section (the same bytes go into both direction tails and the standalone sub)
    LOD = {}; INFO = {}
    for k in range(32):
        for d in (0, 1):
            b = open(cfg['blk'] % (k, d), 'rb').read(); i = b.find(b'XBB\x01'); tail = b[i:]
            sid = [e['name'][4:-4] for e in xbb.parse(tail) if e['name'].startswith('vh_c')][0]
            assert len(tail) == r2k(T_old['vh_sub_' + sid + '.bin']), (k, d, sid, len(tail))   # read size = table sub size
            new, info = lod_xbb(tail, A, cfg['b_full'])
            if sid in LOD: assert LOD[sid] == new, sid
            LOD[sid] = new; INFO[sid] = info
    T_new = {sid: max(T_old['vh_sub_' + sid + '.bin'], len(x)) for sid, x in LOD.items()}
    assert max(T_new.values()) <= LIM
    for k in range(32):
        for d in (0, 1):
            src = cfg['blk'] % (k, d); b = open(src, 'rb').read(); i = b.find(b'XBB\x01')
            sid = [e['name'][4:-4] for e in xbb.parse(b[i:]) if e['name'].startswith('vh_c')][0]
            tail = LOD[sid] + b'\0' * (r2k(T_new[sid]) - len(LOD[sid]))
            nb = b[:i] + tail; fn = os.path.join(od, os.path.basename(cfg['disc_blk'] % (k, d)))
            open(fn, 'wb').write(nb); man.append((cfg['disc_blk'] % (k, d), fn, len(b), len(nb)))
            log.append((k, d, sid, len(b) - i, len(tail), INFO[sid]))
    if cfg['sub']:
        for nm in NAMES:
            sid = nm[1:]; src = cfg['sub'] % sid; old = open(src, 'rb').read()
            new = LOD[sid] + b'\0' * (T_new[sid] - len(LOD[sid]))
            fn = os.path.join(od, os.path.basename(cfg['disc_sub'] % sid))
            open(fn, 'wb').write(new); man.append((cfg['disc_sub'] % sid, fn, len(old), len(new)))
    # start archives stay as they are (their subs <= table size; the S slots they fill are replaced by
    # the full LOD as soon as the window moves).  gmo_size.tbl: sub sizes = T_new (max unchanged).
    src, disc = cfg['nd']; orig = open(src, 'rb').read(); d = bytearray(gzip.decompress(orig))
    ents = xbb.parse(bytes(d)); te = [e for e in ents if e['name'] == 'gmo_size.tbl'][0]
    tb = bytearray(d[te['offset']:te['offset'] + te['size']]); tents = xbb.parse(bytes(tb))
    off = tents[0]['offset']
    for i, e in enumerate(tents):
        sz = e['size']
        if e['name'].startswith('vh_sub_'): sz = T_new[e['name'][7:-4]]
        struct.pack_into('<II', tb, 0x20 + 16 * i, off, sz); off += sz
    d[te['offset']:te['offset'] + te['size']] = tb
    gz = gz_exact(orig, bytes(d)); assert gz
    fn = os.path.join(od, os.path.basename(disc)); open(fn, 'wb').write(gz); man.append((disc, fn, len(orig), len(gz)))
    json.dump({'T_old': T_old, 'T_new': T_new}, open(os.path.join(OUT, c + '_table.json'), 'w'), indent=0)
    return man, log, {}


if __name__ == '__main__':
    M = {}
    for c in COURSES:
        man, log, starts = run(c)
        nc = sum(1 for l in log for x in l[5] if x.startswith('vh_c')); nb = sum(1 for l in log for x in l[5] if x.startswith('vh_b'))
        print(c, 'files', len(man), 'blk tails with c=a:', nc, '/64, b=a:', nb, '/64; max tail', max(l[4] for l in log))
        for s, v in starts.items(): print('  ', s, v)
        M[c] = [dict(iso_path='PSP_GAME/USRDIR/data/' + d, src=f, md5=hashlib.md5(open(f, 'rb').read()).hexdigest(),
                     bytes=nb_, old_bytes=ob) for d, f, ob, nb_ in man]
        json.dump(log, open(os.path.join(OUT, c + '_log.json'), 'w'))
    json.dump({'build': 47, 'part': 'STREAM', 'what': 'Wangan + Hakone mid LOD = full section model (no pop-in of scenery)',
               'replace_or_add': M, 'boot': 'unchanged (BOOT46 final 0d76eadf)'}, open('work/m47/stream/manifest47s.json', 'w'), indent=1)
