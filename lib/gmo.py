#!/usr/bin/env python3
"""Sony GMO (OMG.00.1PSP) model tools.

  gmo.py tree   IN.gmo                 # chunk tree dump
  gmo.py obj    IN.gmo OUT.obj         # export geometry (triangle strips -> tris) with UVs
  gmo.py render IN.gmo OUT.png [--views 3q,side,top,front]   # flat-shaded preview

Chunk rules: long chunk (type < 0x8000): u16 type, u16 flags, u32 size, u32 child_off, u32 data_off.
Short chunk (type & 0x8000): u16 type, u16 hdr(8), u32 size, payload.
Known: 0x0003 model, 0x0004 bone, 0x0005 part, 0x0006 mesh, 0x0007 vertex arrays
(u32 GE vertex type, u32 count, u32 morphs, u32 0, data @+0x20), 0x0008 material,
0x000A texture (0x8012 filename), 0x8061 mesh material ref, 0x8066 draw arrays
(u32 array index within part, u32 GE prim, u32 verts per prim, u32 prim count),
0x804e part->bone, 0x8014 bounding box, 0x8048 bone translate, 0x8041 bone parent.
"""
import math, struct, sys

TC_SZ = [0, 1, 2, 4]; COL_SZ = [0, 0, 0, 0, 2, 2, 2, 4]; NRM_SZ = [0, 1, 2, 4]; POS_SZ = [0, 1, 2, 4]


def chunks(d, off=16, end=None, depth=0):
    end = end or len(d)
    end = min(end, len(d))
    while off + 8 <= end:
        t, f, sz = struct.unpack_from('<HHI', d, off)
        if sz < 8 or off + sz > end:
            break
        yield depth, off, t, sz
        if not t & 0x8000 and t != 7:
            co, do = struct.unpack_from('<II', d, off + 8)
            yield from chunks(d, off + co, off + sz, depth + 1)
        off += sz


def vtx_layout(vt):
    tc, col, nrm, pos = vt & 3, (vt >> 2) & 7, (vt >> 5) & 3, (vt >> 7) & 3
    wt, wc = (vt >> 9) & 3, ((vt >> 14) & 7) + 1
    off = 0; lay = {}; align = 1

    def add(name, csz, n):
        nonlocal off, align
        if csz:
            off = (off + csz - 1) // csz * csz
            lay[name] = (off, csz, n); off += csz * n; align = max(align, csz)
    add('w', [0, 1, 2, 4][wt], wc if wt else 0)
    add('uv', TC_SZ[tc], 2)
    if COL_SZ[col]:
        add('col', COL_SZ[col], 1)
    add('n', NRM_SZ[nrm], 3)
    add('p', POS_SZ[pos], 3)
    stride = (off + align - 1) // align * align
    return lay, stride


def _comp(d, o, csz, n, signed=True, norm=True):
    fmt = {1: 'b', 2: 'h', 4: 'f'}[csz]
    if not signed and csz != 4:
        fmt = fmt.upper()
    v = struct.unpack_from('<' + fmt * n, d, o)
    if csz == 4 or not norm:
        return v
    s = 127.0 if csz == 1 else 32767.0
    return tuple(x / s for x in v)


def load(d):
    """Return list of parts: {'bone': idx, 'arrays': [verts...], 'tris': [(a,b,c)...], 'verts': [...]}"""
    parts = []; cur = None; textures = []; materials = []
    voff = {'p': ((0, 0, 0), (1, 1, 1)), 'uv': ((0, 0), (1, 1))}
    for depth, off, t, sz in chunks(d):
        if t == 0x8015:  # vertex offset/scale: u32 GE-format mask, offsets..., scales...
            mask = struct.unpack_from('<I', d, off + 8)[0]
            n = (sz - 12) // 8
            vals = struct.unpack_from(f'<{2 * n}f', d, off + 12)
            key = 'p' if mask & 0x180 else 'uv' if mask & 3 else None
            if key:
                voff[key] = (vals[:n], vals[n:])
        if t == 5:
            cur = {'arrays': [], 'draws': [], 'bone': None, 'mat': None}; parts.append(cur)
        elif t == 0x8061 and cur is not None:
            cur['mat'] = struct.unpack_from('<I', d, off + 8)[0] & 0xfff
        elif t == 8:
            materials.append(None)
        elif t == 0x8091 and materials:
            materials[-1] = struct.unpack_from('<I', d, off + 8)[0] & 0xfff
        elif t == 0x804e and cur is not None:
            cur['bone'] = struct.unpack_from('<I', d, off + 8)[0]
        elif t == 7 and cur is not None:
            data_off = struct.unpack_from('<I', d, off + 12)[0] or 0x20
            vt, cnt, morph, _ = struct.unpack_from('<4I', d, off + data_off - 16)
            lay, stride = vtx_layout(vt)
            base = off + data_off; vs = []
            for i in range(cnt):
                o = base + i * stride
                p = _comp(d, o + lay['p'][0], lay['p'][1], 3) if 'p' in lay else (0, 0, 0)
                uv = _comp(d, o + lay['uv'][0], lay['uv'][1], 2, signed=False) if 'uv' in lay else (0, 0)
                if lay.get('p', (0, 4))[1] != 4:
                    po, ps = voff['p']; p = tuple(p[k] * ps[k] + po[k] for k in range(3))
                if lay.get('uv', (0, 4))[1] != 4:
                    uo, us = voff['uv']; uv = tuple(uv[k] * us[k] + uo[k] for k in range(2))
                nrm = _comp(d, o + lay['n'][0], lay['n'][1], 3) if 'n' in lay else (0.0, 0.0, 0.0)
                vs.append((p, uv, nrm))
            cur['arrays'].append(vs)
        elif t == 0x8066 and cur is not None:
            ai, prim, per, n = struct.unpack_from('<4I', d, off + 8)
            start = struct.unpack_from('<I', d, off + 24)[0] if sz >= 28 else 0
            if start >= 0x10000000:  # 0xCDCD padding in older exporters
                start = 0
            cur['draws'].append((ai & 0xfff, prim & 0xff, per, n, start, cur['mat']))
        elif t == 0x8012:
            textures.append(d[off + 8:off + sz].split(b'\0')[0].decode('ascii', 'replace'))
    for pt in parts:
        verts = []; tris = []; tmat = []
        for ai, prim, per, n, start, mat in pt['draws']:
            t0 = len(tris)
            if ai >= len(pt['arrays']):
                continue
            arr = pt['arrays'][ai][start:start + per * n]; b = len(verts); verts += arr
            for s in range(n):
                o = b + s * per
                if prim == 3:  # triangle list
                    tris += [(o + k, o + k + 1, o + k + 2) for k in range(0, per - 2, 3) if o + k + 2 < len(verts)]
                    continue
                for k in range(per - 2):  # 4 = strip, 5 = fan
                    a, c, e = (o, o + k + 1, o + k + 2) if prim == 5 else (o + k, o + k + 1, o + k + 2)
                    if e >= len(verts):
                        break
                    tris.append((c, a, e) if prim == 4 and k % 2 else (a, c, e))
            tmat += [mat] * (len(tris) - t0)
        pt['verts'] = verts; pt['tris'] = tris; pt['tri_mat'] = tmat
    for pt in parts:
        pt['tri_tex'] = [materials[m] if m is not None and m < len(materials) else None for m in pt['tri_mat']]
    return parts, textures


def write_obj(parts, path):
    with open(path, 'w') as f:
        vo = 1
        for i, pt in enumerate(parts):
            f.write(f'o part{i}_bone{pt["bone"]}\n')
            for (p, uv) in pt['verts']:
                f.write(f'v {p[0]:.5f} {p[1]:.5f} {p[2]:.5f}\nvt {uv[0]:.5f} {1 - uv[1]:.5f}\n')
            for a, b, c in pt['tris']:
                f.write(f'f {a+vo}/{a+vo} {b+vo}/{b+vo} {c+vo}/{c+vo}\n')
            vo += len(pt['verts'])


def render(parts, path, views=('3q', 'side', 'front', 'top'), size=360):
    from PIL import Image, ImageDraw
    tris = []
    for pt in parts:
        V = [v[0] for v in pt['verts']]
        if V and max(v[1] for v in V) - min(v[1] for v in V) < 1e-3:
            continue  # flat ground-shadow quad
        tris += [(V[a], V[b], V[c]) for a, b, c in pt['tris']]
    if tris:
        ax = [max(p[i] for t in tris for p in t) - min(p[i] for t in tris for p in t) for i in range(3)]
        if ax[0] > ax[2]:  # length stored on x -> swap to z so views are car-relative
            tris = [tuple((p[2], p[1], p[0]) for p in t) for t in tris]
    if not tris:
        raise SystemExit('no triangles')
    allp = [p for t in tris for p in t]
    mn = [min(p[i] for p in allp) for i in range(3)]; mx = [max(p[i] for p in allp) for i in range(3)]
    ctr = [(a + b) / 2 for a, b in zip(mn, mx)]; ext = max(b - a for a, b in zip(mn, mx)) or 1
    rots = {'3q': (35, -30), 'side': (90, 0), 'front': (0, 0), 'top': (0, -90), 'rear': (180, 0)}
    sheet = Image.new('RGB', (size * len(views), size), (40, 44, 52))
    light = (0.3, 0.8, 0.5)
    for vi, name in enumerate(views):
        yaw, pitch = [math.radians(x) for x in rots[name]]
        cy, sy, cp, sp = math.cos(yaw), math.sin(yaw), math.cos(pitch), math.sin(pitch)

        def xf(p):
            x, y, z = [(p[i] - ctr[i]) / ext for i in range(3)]
            x, z = x * cy + z * sy, -x * sy + z * cy
            y, z = y * cp - z * sp, y * sp + z * cp
            return x, y, z
        img = Image.new('RGB', (size, size), (40, 44, 52)); dr = ImageDraw.Draw(img)
        proj = []
        for t in tris:
            a, b, c = [xf(p) for p in t]
            ux, uy, uz = [b[i] - a[i] for i in range(3)]; vx, vy, vz = [c[i] - a[i] for i in range(3)]
            nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
            ln = math.sqrt(nx * nx + ny * ny + nz * nz) or 1
            sh = abs(nx * light[0] + ny * light[1] + nz * light[2]) / ln
            proj.append(((a[2] + b[2] + c[2]) / 3, [(size / 2 + p[0] * size * 0.85, size / 2 - p[1] * size * 0.85) for p in (a, b, c)], sh))
        proj.sort(key=lambda r: -r[0])
        for _, pts, sh in proj:
            g = int(70 + 170 * sh)
            dr.polygon(pts, fill=(g, int(g * 0.95), int(g * 0.9)))
        dr.text((6, 6), name, fill='white')
        sheet.paste(img, (vi * size, 0))
    sheet.save(path)


def render_textured(parts, textures, path, views=('3q', 'side', 'front', 'rear'), size=400, skip_flat=True, axis_map=None, bg=(40, 44, 52)):
    """Software preview with per-triangle texture sampling (centroid UV, nearest).
    textures: {texture_index: PIL.Image RGBA}. Untextured triangles use `paint` grey."""
    from PIL import Image, ImageDraw
    tris = []
    for pt in parts:
        V = pt['verts']
        if skip_flat and V and max(v[0][1] for v in V) - min(v[0][1] for v in V) < 1e-3:
            continue
        for (a, b, c), tx in zip(pt['tris'], pt.get('tri_tex', [None] * len(pt['tris']))):
            P = [V[a][0], V[b][0], V[c][0]]
            if axis_map:
                P = [axis_map(p) for p in P]
            uv = [(V[a][1][k] + V[b][1][k] + V[c][1][k]) / 3 for k in range(2)]
            col = (200, 200, 205, 255)
            if tx is not None and tx in textures:
                im = textures[tx]; w, h = im.size
                col = im.getpixel((int(uv[0] % 1 * w) % w, int(uv[1] % 1 * h) % h))
            tris.append((P, col))
    allp = [p for t, _ in tris for p in t]
    mn = [min(p[i] for p in allp) for i in range(3)]; mx = [max(p[i] for p in allp) for i in range(3)]
    ctr = [(a + b) / 2 for a, b in zip(mn, mx)]; ext = max(b - a for a, b in zip(mn, mx)) or 1
    rots = {'3q': (35, -25), 'side': (90, 0), 'front': (0, 0), 'top': (0, -90), 'rear': (180, 0), '3qr': (145, -20)}
    sheet = Image.new('RGB', (size * len(views), size), bg)
    light = (0.35, 0.8, 0.45)
    for vi, name in enumerate(views):
        yaw, pitch = [math.radians(x) for x in rots[name]]
        cy, sy, cp, sp = math.cos(yaw), math.sin(yaw), math.cos(pitch), math.sin(pitch)

        def xf(p):
            x, y, z = [(p[i] - ctr[i]) / ext for i in range(3)]
            x, z = x * cy + z * sy, -x * sy + z * cy
            y, z = y * cp - z * sp, y * sp + z * cp
            return x, y, z
        img = Image.new('RGB', (size, size), bg); dr = ImageDraw.Draw(img)
        proj = []
        for P, col in tris:
            a, b, c = [xf(p) for p in P]
            ux, uy, uz = [b[i] - a[i] for i in range(3)]; vx, vy, vz = [c[i] - a[i] for i in range(3)]
            nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
            ln = math.sqrt(nx * nx + ny * ny + nz * nz) or 1
            sh = 0.45 + 0.55 * abs(nx * light[0] + ny * light[1] + nz * light[2]) / ln
            proj.append(((a[2] + b[2] + c[2]) / 3, [(size / 2 + q[0] * size * 0.88, size / 2 - q[1] * size * 0.88) for q in (a, b, c)], tuple(int(ch * sh) for ch in col[:3])))
        proj.sort(key=lambda r: -r[0])
        for _, pts, col in proj:
            dr.polygon(pts, fill=col)
        dr.text((6, 6), name, fill='white')
        sheet.paste(img, (vi * size, 0))
    sheet.save(path)


if __name__ == '__main__':
    cmd, src = sys.argv[1], sys.argv[2]
    d = open(src, 'rb').read()
    if cmd == 'tree':
        for depth, off, t, sz in chunks(d):
            print('  ' * depth + f'{off:06x} {t:#06x} {sz:#x}')
    else:
        parts, tex = load(d)
        if cmd == 'obj':
            write_obj(parts, sys.argv[3])
        elif cmd == 'render':
            v = sys.argv[sys.argv.index('--views') + 1].split(',') if '--views' in sys.argv else ('3q', 'side', 'front', 'top')
            render(parts, sys.argv[3], v)
        print(f'parts={len(parts)} verts={sum(len(p["verts"]) for p in parts)} tris={sum(len(p["tris"]) for p in parts)} textures={tex}')
