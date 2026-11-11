#!/usr/bin/env python3
"""M2: Devil Z (Wangan Midnight Portable, BUILD entry 744) into Initial D Street Stage's
nissan_s15 car slot. Produces new nissan_s15_race.bin(.gz) / nissan_s15_sel.bin(.gz).

Usage: build_devilz.py WMP_FILES_DIR IDSS_CAR_DIR OUT_DIR [--plain]
  WMP_FILES_DIR : output of wmp_build.py unpack (needs 00744/00745/00746.bin)
  IDSS_CAR_DIR  : folder with nissan_s15_race.bin, nissan_s15_sel.bin and their .gz
  --plain       : untextured paint body (pure Initial D style) instead of styled line texture
"""
import os, struct, sys, copy, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.environ.get('PSP_REMIX_SCRIPTS', 'plugin/scripts'))
import gmo, gim, xbb, psp_gz
import gmo_tree as G
from PIL import Image, ImageFilter

WHEEL_Y = 0.217          # WMP wheel-centre height (Initial D puts wheel centres at y = 0)
WHEELBASE_HALF = 1.153   # WMP wheel bones (±1.153 along length)
TRACK_HALF = 0.713       # WMP wheel bones (±0.713 across)

# WMP part groups (see FORMATS notes): texture index in the WMP model -> role
PAINT_BD, PAINT_BN, GLASS = [0, 4], [11], [17]
TRIM = {  # wmp tex idx: (wmp parts, IDSS material index in s15_099bodyetc, IDSS texture file to overwrite)
    'in':   ([1, 9],        6,  'h_car_s15_seatside.gim'),
    'en':   ([2, 3, 7, 8],  7,  'h_car_s15_seatfront.gim'),
    'muf':  ([5],           8,  'h_car_s15_syaken.gim'),
    'rs':   ([10],          9,  'y_car_handle.gim'),
    'fl':   ([12],          11, 'h_car_s15_dashboard.gim'),
    'flef': ([13, 14, 15, 16], 5, 'h_car_s15_meter.gim'),
}
# WMP picture index for each texture (745 = small sheet, 746 = body sheet)
PICS = {'bd': (746, 0), 'bn': (746, 28), 'in': (745, 14), 'en': (745, 0), 'muf': (745, 40),
        'fl': (745, 16), 'rs': (746, 32), 'flef': (745, 8)}
BODY_TEX, BONNET_TEX = 'h_car_s15_fs_ami', 'h_car_s15_fs_duct'   # S15 textures freed by hiding the stock bodykit


def xf_p(p):
    return (-p[2], p[1] - WHEEL_Y, p[0])


def xf_n(n):
    return (-n[2], n[1], n[0])


def wmp_geometry(wmp_dir):
    parts, _ = gmo.load(open(os.path.join(wmp_dir, '00744.bin'), 'rb').read())
    out = {}
    for i, pt in enumerate(parts):
        V = [(xf_p(v[0]), xf_n(v[2]), v[1]) for v in pt['verts']]
        out[i] = (V, pt['tris'])
    return out


def tri_soup(geo, idxs, uv_mode='keep'):
    """Flatten parts into (verts, tris). Per-triangle UV shift keeps UVs >= 0 for GE wrap."""
    verts, tris = [], []
    for i in idxs:
        V, T = geo[i]
        for a, b, c in T:
            tv = [V[a], V[b], V[c]]
            if uv_mode == 'side':  # planar side projection (glass)
                tv = [(p, n, (0.5 + p[2] / 4.4, 0.5 - p[1] / 1.6)) for p, n, _ in tv]
            elif uv_mode == 'zero':
                tv = [(p, n, (0.0, 0.0)) for p, n, _ in tv]
            else:
                su = min(int(v[2][0] // 1) for v in tv); sv = min(int(v[2][1] // 1) for v in tv)
                tv = [(p, n, (uv[0] - su, uv[1] - sv)) for p, n, uv in tv]
            base = len(verts); verts += tv; tris.append((base, base + 1, base + 2))
    return verts, tris


def pic(wmp_dir, key):
    f, k = PICS[key]
    d = open(os.path.join(wmp_dir, f'{f:05d}.bin'), 'rb').read()
    return gim.to_image(d, k).convert('RGBA'), gim.pictures(d)[k][0]['bpp']


def stylize_paint(im):
    """WMP bodies bake soft grey shading; Initial D uses flat paint with crisp dark lines.
    Posterize luminance into paint / soft shade / trim / line bands, keep alpha."""
    L = im.convert('L'); a = im.getchannel('A')
    lut = []
    for v in range(256):
        x = v / 255
        lut.append(255 if x > 0.50 else 205 if x > 0.32 else 120 if x > 0.18 else 30)
    P = L.point(lut).filter(ImageFilter.SMOOTH)
    out = Image.merge('RGBA', (P, P, P, a))
    return out


def degenerate(part):
    """Collapse a part to one zero-area triangle (keeps every index/table intact)."""
    meshes = [c for c in part.children if c.type == 6]
    mref = 0x82000
    if meshes:
        for c in meshes[0].children:
            if c.type == 0x8061:
                mref = struct.unpack_from('<I', c.payload)[0]
    z = ((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0))
    G.set_part_geometry(part, [z, z, z], [(mref, [(0, 1, 2)])])


def empty_gmo(data):
    t = G.GmoTree.load(data)
    for p in t.find(5):
        degenerate(p)
    return t.dump()


def tex_node_for(template_tex, name):
    n = copy.deepcopy(template_tex)
    raw = (name + '.pic').encode() + b'\0'
    raw += b'\0' * ((-len(raw)) % 4)
    for c in n.children:
        if c.type == 0x8012:
            c.payload = raw
    return n


def set_diffuse_white(mat):
    for c in mat.children:
        if c.type == 0x8082:
            c.payload = struct.pack('<4f', 1, 1, 1, 1)


def update_model_bbox(t, pts):
    m = t.model()
    for c in m.children:
        if c.type == 0x8014:
            c.payload = G.bbox_payload(pts)


def build_body(tpl, geo, plain):
    t = G.GmoTree.load(tpl)
    m = t.model()
    parts = [c for c in m.children if c.type == 5]
    mats = [c for c in m.children if c.type == 8]
    texs = [c for c in m.children if c.type == 0xA]
    win_vt = struct.unpack_from('<I', [c for c in parts[1].children if c.type == 7][0].pre)[0]
    bd_v, bd_t = tri_soup(geo, PAINT_BD, 'zero' if plain else 'keep')
    bn_v, bn_t = tri_soup(geo, PAINT_BN, 'zero' if plain else 'keep')
    off = len(bd_v); verts = bd_v + bn_v; bn_t = [(a + off, b + off, c + off) for a, b, c in bn_t]
    if plain:
        G.set_part_geometry(parts[0], verts, [(0x82000, bd_t + bn_t)])
    else:
        layer = copy.deepcopy([c for c in mats[1].children if c.type == 9][0])
        n_tex = len(texs)
        l_bd = copy.deepcopy(layer); [setattr(c, 'payload', struct.pack('<I', 0xa2000 | n_tex)) for c in l_bd.children if c.type == 0x8091]
        l_bn = copy.deepcopy(layer); [setattr(c, 'payload', struct.pack('<I', 0xa2000 | (n_tex + 1))) for c in l_bn.children if c.type == 0x8091]
        mat_bn = copy.deepcopy(mats[0]); mat_bn.children.append(l_bn)
        mats[0].children.append(l_bd)
        # insert new material after the last material, new textures after the last texture
        kids = m.children
        last_mat = max(i for i, c in enumerate(kids) if c.type == 8)
        kids.insert(last_mat + 1, mat_bn)
        last_tex = max(i for i, c in enumerate(kids) if c.type == 0xA)
        kids.insert(last_tex + 1, tex_node_for(texs[0], BONNET_TEX))
        kids.insert(last_tex + 1, tex_node_for(texs[0], BODY_TEX))
        bn_mat = 0x82000 | len(mats)
        G.set_part_geometry(parts[0], verts, [(0x82000, bd_t), (bn_mat, bn_t)], vt=win_vt)
    gv, gt = tri_soup(geo, GLASS, 'side')
    G.set_part_geometry(parts[1], gv, [(0x82001, gt)])
    update_model_bbox(t, [v[0] for v in verts + gv])
    return t.dump()


def build_env(tpl, geo, which):
    t = G.GmoTree.load(tpl)
    part = t.find(5)[0]
    v, tr = tri_soup(geo, (PAINT_BD + PAINT_BN) if which == 'body' else GLASS, 'zero')
    G.set_part_geometry(part, v, [(0x82000, tr)])
    update_model_bbox(t, [x[0] for x in v])
    return t.dump()


def build_trim(tpl, geo):
    t = G.GmoTree.load(tpl)
    m = t.model()
    parts = [c for c in m.children if c.type == 5]
    mats = [c for c in m.children if c.type == 8]
    for i in (0, 1, 2, 3):
        degenerate(parts[i])
    verts, groups = [], []
    for key, (wparts, mat_i, _) in TRIM.items():
        v, tr = tri_soup(geo, wparts, 'keep'); o = len(verts); verts += v
        groups.append((0x82000 | mat_i, [(a + o, b + o, c + o) for a, b, c in tr]))
        set_diffuse_white(mats[mat_i])
    G.set_part_geometry(parts[5], verts, groups)
    update_model_bbox(t, [x[0] for x in verts])
    return t.dump()


def shift_gmo(data, dy, dz):
    t = G.GmoTree.load(data)
    for a in t.find(7):
        vt, cnt = struct.unpack_from('<II', a.pre, 0)
        lay, stride = gmo.vtx_layout(vt)
        if lay['p'][1] != 4:
            continue
        b = bytearray(a.pre); po = 16 + lay['p'][0]
        for i in range(cnt):
            x, y, z = struct.unpack_from('<3f', b, po + i * stride)
            struct.pack_into('<3f', b, po + i * stride, x, y + dy, z + dz)
        a.pre = bytes(b)
    return t.dump()


def patch_params(raw):
    b = bytearray(raw)
    f = lambda o: struct.unpack_from('<f', b, o)[0]
    put = lambda o, v: struct.pack_into('<f', b, o, v)
    # wheels: 6 records {x, y, z} at 0x210 + 0x24*k
    for k in range(6):
        o = 0x210 + 0x24 * k
        x, z = f(o), f(o + 8)
        put(o, TRACK_HALF if x > 0 else -TRACK_HALF)
        put(o + 8, WHEELBASE_HALF if z > 0 else -WHEELBASE_HALF)
    # plates: front records (scale3, rot3, x, y, z) at 0x00 + 0x24*k, rear at 0xd8 + 0x24*k
    for k in range(4):
        o = 0x24 * k
        y, z = f(o + 0x1c), f(o + 0x20)
        put(o + 0x1c, y - 0.128 + 0.06); put(o + 0x20, z - 2.2335 + 1.99)
        o = 0xd8 + 0x24 * k
        y, z = f(o + 0x1c), f(o + 0x20)
        if z < -1:
            put(o + 0x1c, y - 0.1677 + 0.27); put(o + 0x20, z + 2.1851 - 2.035)
    return bytes(b)


BODYKIT_TAGS = ('bu', 'fs', 'bm', 'gk', 'rk', 'eb', 'ss', 'rb', 'rw', 'mu')


def is_bodykit(name):
    if not name.startswith('s15_') or not name.endswith('.gmo'):
        return False
    stem = name[4:-4]
    for suf in ('_race', '_sel', 'etc'):
        if stem.endswith(suf):
            stem = stem[:-len(suf)]
    return stem[:3].isdigit() and stem[3:] in BODYKIT_TAGS


def rebuild(container, geo, wmp_dir, plain, kind):
    d = open(container, 'rb').read()
    ents = xbb.parse(d)
    get = lambda n: d[[e for e in ents if e['name'] == n][0]['offset']:][:[e for e in ents if e['name'] == n][0]['size']]
    new = {}
    body_tpl = get('s15_000body.gmo')
    new['s15_000body.gmo'] = build_body(body_tpl, geo, plain)
    new[f's15_200envbody_{kind}.gmo'] = build_env(get(f's15_200envbody_{kind}.gmo'), geo, 'body')
    new[f's15_201envwin_{kind}.gmo'] = build_env(get(f's15_201envwin_{kind}.gmo'), geo, 'glass')
    new['s15_099bodyetc.gmo'] = build_trim(get('s15_099bodyetc.gmo'), geo)
    new['s15_098bodyetc.gmo'] = empty_gmo(get('s15_098bodyetc.gmo'))
    new['s15_100nmlight.gmo'] = shift_gmo(get('s15_100nmlight.gmo'), 0.10, 0.17)
    for e in ents:
        if is_bodykit(e['name']) and e['size']:
            new[e['name']] = empty_gmo(get(e['name']))
    new['nissan_s15.bin'] = patch_params(get('nissan_s15.bin'))
    # textures
    for key, (_, _, fname) in TRIM.items():
        im, bpp = pic(wmp_dir, key)
        new[fname] = gim.build(im, 8 if bpp == 8 else 4)
    if not plain:
        bd, _ = pic(wmp_dir, 'bd'); bn, _ = pic(wmp_dir, 'bn')
        new[BODY_TEX + '.gim'] = gim.build(stylize_paint(bd), 8)
        new[BONNET_TEX + '.gim'] = gim.build(stylize_paint(bn), 4)
    blobs = [new.get(e['name'], d[e['offset']:e['offset'] + e['size']]) if e['name'] != 'dummy' else b'' for e in ents]
    out = xbb.build(ents, blobs)
    # verify: untouched entries identical, replaced ones re-parse
    for e, e2 in zip(ents, xbb.parse(out)):
        blob = out[e2['offset']:e2['offset'] + e2['size']]
        if e['name'] in new:
            if e['name'].endswith('.gmo'):
                G.GmoTree.load(blob); gmo.load(blob)
            elif e['name'].endswith('.gim'):
                gim.to_image(blob)
        else:
            assert blob == d[e['offset']:e['offset'] + e['size']], e['name']
    return out, new


def main():
    wmp_dir, car_dir, out_dir = sys.argv[1:4]
    plain = '--plain' in sys.argv
    os.makedirs(out_dir, exist_ok=True)
    geo = wmp_geometry(wmp_dir)
    report = {}
    for kind, fn in (('race', 'nissan_s15_race.bin'), ('sel', 'nissan_s15_sel.bin')):
        out, new = rebuild(os.path.join(car_dir, fn), geo, wmp_dir, plain, kind)
        open(os.path.join(out_dir, fn), 'wb').write(out)
        gz = psp_gz.repack(open(os.path.join(car_dir, fn + '.gz'), 'rb').read(), out)
        open(os.path.join(out_dir, fn + '.gz'), 'wb').write(gz)
        report[fn] = {'bytes': len(out), 'gz_bytes': len(gz), 'replaced': sorted(new)}
        print(f'{fn}: {len(out)} bytes ({len(gz)} gz), {len(new)} entries replaced')
    json.dump(report, open(os.path.join(out_dir, 'build_report.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
