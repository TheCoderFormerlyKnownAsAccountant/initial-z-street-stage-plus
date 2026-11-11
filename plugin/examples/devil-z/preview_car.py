#!/usr/bin/env python3
"""Assemble an Initial D car container (stage-0 parts + wheels) and render a textured preview.
Usage: preview_car.py CAR.bin OUT.png [--race|--sel]"""
import os, struct, sys
sys.path.insert(0, os.environ.get('PSP_REMIX_SCRIPTS', 'plugin/scripts'))
import gmo, gim, xbb

src, outp = sys.argv[1], sys.argv[2]
d = open(src, 'rb').read(); ents = xbb.parse(d)
files = {e['name']: d[e['offset']:e['offset'] + e['size']] for e in ents if e['size']}
code = [n for n in files if n.endswith('.bin')][0]
prm = files[code]
wheels = [struct.unpack_from('<3f', prm, 0x258 + 0x24 * k) for k in range(4)]
pre = [n for n in files if n.endswith('000body.gmo')][0].split('_')[0]
stage0 = [n for n in files if n.endswith('.gmo') and n.startswith(pre + '_') and (
    n[len(pre) + 1:len(pre) + 4] in ('000', '001', '005', '018', '022', '026', '032', '038', '042', '046', '052', '098', '099', '100'))]
tire = [n for n in files if n.startswith(pre + '_062ti')][0]
texcache = {}


def texture(name):
    key = name.rsplit('.', 1)[0] + '.gim'
    for k in files:
        if k.lower() == key.lower():
            if k not in texcache:
                try:
                    texcache[k] = gim.to_image(files[k]).convert('RGBA')
                except Exception:
                    texcache[k] = None
            return texcache[k]
    return None


allparts, textures, tex_id = [], {}, {}


def add(name, offset=(0, 0, 0), mirror=False):
    parts, texnames = gmo.load(files[name])
    for p in parts:
        V = []
        for (pos, uv, n) in p['verts']:
            x, y, z = pos
            if mirror:
                x = -x
            V.append(((x + offset[0], y + offset[1], z + offset[2]), uv, n))
        p['verts'] = V
        tt = []
        for t in p['tri_tex']:
            if t is None or t >= len(texnames):
                tt.append(None); continue
            nm = texnames[t]
            if nm not in tex_id:
                tex_id[nm] = len(tex_id); im = texture(nm)
                if im is not None:
                    textures[tex_id[nm]] = im
            tt.append(tex_id[nm])
        p['tri_tex'] = tt
        allparts.append(p)


for n in sorted(stage0):
    add(n)
for (x, y, z) in wheels:
    add(tire, (x, y, z), mirror=x < 0)
PAINT = (38, 62, 128)  # Devil Z midnight blue
for nm, k in tex_id.items():
    low = nm.lower()
    if ('fs_ami' in low or 'fs_duct' in low) and k in textures:
        from PIL import ImageChops, Image
        im = textures[k]; tint = Image.new('RGBA', im.size, PAINT + (255,))
        textures[k] = ImageChops.multiply(im, tint)
# untextured paint triangles -> paint colour too
gmo_paint = PAINT
gmo.render_textured(allparts, textures, outp, views=('3q', 'side', 'front', 'rear', '3qr'), size=360)
print('rendered', outp, len(allparts), 'parts', 'wheels', [tuple(round(c, 3) for c in w) for w in wheels])
