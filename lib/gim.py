#!/usr/bin/env python3
"""Sony GIM (MIG.00.1PSP) texture <-> PNG.

  gim.py topng  IN.gim OUT.png
  gim.py frompng IN.png TEMPLATE.gim OUT.gim   # re-encode using template's format/size/palette layout
  gim.py info   IN.gim

Supports RGBA5650/5551/4444/8888 and indexed 4/8-bit (palette in 5650/5551/4444/8888),
linear or swizzled ("faster") pixel order. DXT formats are decoded only.
frompng quantizes to the template's palette size for indexed images (new palette is written).
"""
import struct, sys
from PIL import Image

FMT_BPP = {0: 16, 1: 16, 2: 16, 3: 32, 4: 4, 5: 8, 6: 16, 7: 32}


def _blocks(d, off=16, end=None):
    end = end or len(d)
    while off < end:
        bid, _, bsize, nxt, doff = struct.unpack_from('<HHIII', d, off)
        yield bid, off, bsize, nxt, doff
        if bid in (2, 3):
            yield from _blocks(d, off + nxt, off + bsize)
        off += bsize
        if bsize == 0:
            break


def _imghdr(d, off):
    h = d[off + 16: off + 16 + 0x40]
    hl, _, fmt, order, w, hgt, bpp, palign, halign = struct.unpack_from('<HHHHHHHHH', h, 0)
    pix_start = struct.unpack_from('<I', h, 0x1C)[0]
    return dict(base=off + 16, fmt=fmt, order=order, w=w, h=hgt, bpp=bpp, palign=palign or 16,
                halign=halign or 8, pix=off + 16 + pix_start)


def parse(d):
    if not d.startswith(b'MIG.'):
        raise ValueError('not GIM')
    img = pal = None
    for bid, off, *_ in _blocks(d):
        if bid == 4 and img is None:
            img = _imghdr(d, off)
        elif bid == 5 and pal is None:
            pal = _imghdr(d, off)
    return img, pal


def pictures(d):
    """All pictures in a (possibly multi-picture) GIM: list of (img_hdr, pal_hdr)."""
    pics = []; cur = None
    for bid, off, *_ in _blocks(d):
        if bid == 3:
            cur = [None, None]; pics.append(cur)
        elif bid == 4 and cur is not None and cur[0] is None:
            cur[0] = _imghdr(d, off)
        elif bid == 5 and cur is not None and cur[1] is None:
            cur[1] = _imghdr(d, off)
    return [tuple(p) for p in pics if p[0]]


def _unswizzle(buf, wbytes, h):
    out = bytearray(len(buf))
    bw = wbytes // 16
    i = 0
    for by in range(0, h, 8):
        for bx in range(bw):
            for r in range(8):
                y = by + r
                if y < h:
                    dst = y * wbytes + bx * 16
                    out[dst:dst + 16] = buf[i:i + 16]
                i += 16
    return bytes(out)


def _swizzle(buf, wbytes, h):
    out = bytearray()
    bw = wbytes // 16
    for by in range(0, h, 8):
        for bx in range(bw):
            for r in range(8):
                y = by + r
                src = y * wbytes + bx * 16
                out += buf[src:src + 16] if y < h else b'\0' * 16
    return bytes(out)


def _px16(v, fmt):
    if fmt == 0:
        return ((v & 31) << 3, ((v >> 5) & 63) << 2, ((v >> 11) & 31) << 3, 255)
    if fmt == 1:
        return ((v & 31) << 3, ((v >> 5) & 31) << 3, ((v >> 10) & 31) << 3, 255 if v >> 15 else 0)
    return ((v & 15) * 17, ((v >> 4) & 15) * 17, ((v >> 8) & 15) * 17, ((v >> 12) & 15) * 17)


def _colors(raw, fmt, n):
    if fmt == 3:
        return [tuple(raw[i * 4:i * 4 + 4]) for i in range(n)]
    return [_px16(struct.unpack_from('<H', raw, i * 2)[0], fmt) for i in range(n)]


def _dims(img):
    bpp = FMT_BPP.get(img['fmt'], 16)
    wbytes = (img['w'] * bpp // 8 + 15) // 16 * 16
    hh = (img['h'] + 7) // 8 * 8
    return bpp, wbytes, hh


def to_image(d, picture=None):
    img, pal = parse(d) if picture is None else pictures(d)[picture]
    if img['fmt'] >= 8:
        raise NotImplementedError('DXT GIM decode not implemented; use GimConv')
    bpp, wbytes, hh = _dims(img)
    raw = d[img['pix']: img['pix'] + wbytes * hh]
    if img['order'] == 1:
        raw = _unswizzle(raw, wbytes, hh)
    w, h = img['w'], img['h']
    if img['fmt'] in (4, 5):
        pbpp, pw, _ = _dims(pal)
        n = pal['w'] * pal['h']
        prow = d[pal['pix']: pal['pix'] + n * FMT_BPP[pal['fmt']] // 8]
        colors = _colors(prow, pal['fmt'], n)
        px = []
        for y in range(h):
            row = raw[y * wbytes:(y + 1) * wbytes]
            if img['fmt'] == 4:
                for x in range(w):
                    b = row[x >> 1]
                    px.append(colors[(b >> 4) if x & 1 else (b & 15)])
            else:
                px.extend(colors[row[x]] for x in range(w))
    else:
        px = []
        for y in range(h):
            row = raw[y * wbytes:(y + 1) * wbytes]
            px.extend(_colors(row, img['fmt'], w))
    im = Image.new('RGBA', (w, h)); im.putdata(px)
    return im


def _enc16(c, fmt):
    r, g, b, a = c
    if fmt == 0:
        return (r >> 3) | ((g >> 2) << 5) | ((b >> 3) << 11)
    if fmt == 1:
        return (r >> 3) | ((g >> 3) << 5) | ((b >> 3) << 10) | ((a >= 128) << 15)
    return (r >> 4) | ((g >> 4) << 4) | ((b >> 4) << 8) | ((a >> 4) << 12)


def from_image(im, tmpl):
    """Encode `im` into a copy of template GIM bytes (same dimensions/format)."""
    d = bytearray(tmpl)
    img, pal = parse(tmpl)
    im = im.convert('RGBA').resize((img['w'], img['h']), Image.LANCZOS)
    bpp, wbytes, hh = _dims(img)
    w, h = img['w'], img['h']
    lin = bytearray(wbytes * hh)
    if img['fmt'] in (4, 5):
        n = pal['w'] * pal['h']
        q = im.quantize(colors=min(n, 16 if img['fmt'] == 4 else 256), method=Image.Quantize.FASTOCTREE)
        qp = q.getpalette()[:3 * n]
        alpha = im.getchannel('A')
        idx = list(q.getdata())
        # palette entries carry alpha averaged from source pixels
        acc = {}
        for i, a in zip(idx, alpha.getdata()):
            acc.setdefault(i, []).append(a)
        cols = []
        for i in range(n):
            rgb = tuple(qp[i * 3:i * 3 + 3]) if i * 3 + 2 < len(qp) else (0, 0, 0)
            a = sum(acc[i]) // len(acc[i]) if i in acc else 255
            cols.append(rgb + (a,))
        pb = bytearray()
        for c in cols:
            pb += bytes(c) if pal['fmt'] == 3 else struct.pack('<H', _enc16(c, pal['fmt']))
        d[pal['pix']:pal['pix'] + len(pb)] = pb
        for y in range(h):
            for x in range(w):
                v = idx[y * w + x]
                if img['fmt'] == 4:
                    o = y * wbytes + (x >> 1)
                    lin[o] |= (v & 15) << (4 if x & 1 else 0)
                else:
                    lin[y * wbytes + x] = v
    else:
        px = list(im.getdata())
        for y in range(h):
            for x in range(w):
                c = px[y * w + x]
                o = y * wbytes + x * bpp // 8
                if img['fmt'] == 3:
                    lin[o:o + 4] = bytes(c)
                else:
                    struct.pack_into('<H', lin, o, _enc16(c, img['fmt']))
    out = _swizzle(bytes(lin), wbytes, hh) if img['order'] == 1 else bytes(lin)
    d[img['pix']:img['pix'] + len(out)] = out
    return bytes(d)


def _data_hdr(fmt, order, w, h, bpp, nbytes, levels=(1, 1, 3, 1)):
    hdr = struct.pack('<HHHHHHHHHH', 0x30, 0, fmt, order, w, h, bpp, 16, 1 if order else 1, 2)
    hdr += struct.pack('<IIIII', 0, 0x30, 0x40, 0x40 + nbytes, 0)
    hdr += struct.pack('<HHHHI', *levels, 0x40)
    return hdr + b'\0' * (0x40 - len(hdr))


def build(im, bits=4, swizzle=True, colors=None):
    """Make a single-picture GIM from a PIL image: indexed 4/8-bit, RGBA8888 palette
    (the layout Initial D Street Stage uses for car textures). Width/height must be powers of two."""
    im = im.convert('RGBA'); w, h = im.size
    n = colors or (16 if bits == 4 else 256)
    px = list(im.getdata()); uniq = sorted(set(px))
    palb = bytearray()
    if len(uniq) <= n:  # exact palette, alpha preserved
        lut = {c: i for i, c in enumerate(uniq)}; idx = [lut[c] for c in px]
        for c in uniq + [(0, 0, 0, 0)] * (n - len(uniq)):
            palb += bytes(c)
    else:
        q = im.convert('RGB').quantize(colors=n, method=Image.Quantize.MEDIANCUT)
        pal = q.getpalette()[:3 * n]; idx = list(q.getdata())
        acc = {}
        for i, a in zip(idx, im.getchannel('A').getdata()):
            acc.setdefault(i, []).append(a)
        for i in range(n):
            rgb = pal[i * 3:i * 3 + 3] if i * 3 + 2 < len(pal) else [0, 0, 0]
            palb += bytes(rgb) + bytes([sum(acc[i]) // len(acc[i]) if i in acc else 255])
    wbytes = (w * bits // 8 + 15) // 16 * 16; hh = (h + 7) // 8 * 8
    lin = bytearray(wbytes * hh)
    for y in range(h):
        for x in range(w):
            v = idx[y * w + x]
            if bits == 4:
                lin[y * wbytes + (x >> 1)] |= (v & 15) << (4 if x & 1 else 0)
            else:
                lin[y * wbytes + x] = v
    pix = _swizzle(bytes(lin), wbytes, hh) if swizzle else bytes(lin)
    fmt = 4 if bits == 4 else 5
    img_blk_data = _data_hdr(fmt, 1 if swizzle else 0, w, h, bits, len(pix)) + pix
    pal_blk_data = _data_hdr(3, 0, n, 1, 32, len(palb), (0, 1, 0, 1)) + bytes(palb)
    blk = lambda bid, payload, nxt=16: struct.pack('<HHIII', bid, 0, 16 + len(payload), 16 + len(payload) if nxt is None else nxt, 16) + payload
    img_b = struct.pack('<HHIII', 4, 0, 16 + len(img_blk_data), 16 + len(img_blk_data), 16) + img_blk_data
    pal_b = struct.pack('<HHIII', 5, 0, 16 + len(pal_blk_data), 16 + len(pal_blk_data), 16) + pal_blk_data
    pic = struct.pack('<HHIII', 3, 0, 16 + len(img_b) + len(pal_b), 16, 16) + img_b + pal_b
    info = struct.pack('<HHIII', 0xff, 0, 16, 16, 16)
    root = struct.pack('<HHIII', 2, 0, 16 + len(pic), 16, 16) + pic + info
    return b'MIG.00.1PSP\0' + b'\0' * 4 + root


def from_image_keep_palette(im, tmpl):
    """Re-encode an indexed GIM keeping its existing palette (nearest-colour match).
    Use for atlas edits so untouched glyphs stay bit-identical."""
    d = bytearray(tmpl)
    img, pal = parse(tmpl)
    if img['fmt'] not in (4, 5):
        return from_image(im, tmpl)
    n = pal['w'] * pal['h']
    colors = _colors(d[pal['pix']:pal['pix'] + n * FMT_BPP[pal['fmt']] // 8], pal['fmt'], n)
    im = im.convert('RGBA'); w, h = img['w'], img['h']
    bpp, wbytes, hh = _dims(img)
    cache = {}
    def near(c):
        if c not in cache:
            if c[3] == 0:
                zs = [i for i, p in enumerate(colors) if p[3] == 0]
                if zs:
                    cache[c] = zs[0]; return cache[c]
            cache[c] = min(range(n), key=lambda i: sum((a - b) ** 2 for a, b in zip(c, colors[i])))
        return cache[c]
    px = list(im.getdata())
    lin = bytearray(wbytes * hh)
    for y in range(h):
        for x in range(w):
            v = near(px[y * w + x])
            if img['fmt'] == 4:
                lin[y * wbytes + (x >> 1)] |= (v & 15) << (4 if x & 1 else 0)
            else:
                lin[y * wbytes + x] = v
    out = _swizzle(bytes(lin), wbytes, hh) if img['order'] == 1 else bytes(lin)
    d[img['pix']:img['pix'] + len(out)] = out
    return bytes(d)


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'topng':
        to_image(open(sys.argv[2], 'rb').read()).save(sys.argv[3])
    elif cmd == 'frompng':
        open(sys.argv[4], 'wb').write(from_image(Image.open(sys.argv[2]), open(sys.argv[3], 'rb').read()))
    elif cmd == 'info':
        print(parse(open(sys.argv[2], 'rb').read()))
