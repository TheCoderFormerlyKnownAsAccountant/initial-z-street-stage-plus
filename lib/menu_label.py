#!/usr/bin/env python3
"""Render English menu labels in Initial D Street Stage's menu style and write them
back into the GIM textures embedded in an @ANA layout.

  menu_label.py list  LAYOUT.ana OUT_SHEET.png             # numbered contact sheet of every texture
  menu_label.py render "TIME ATTACK" --accent 5 --style plain|glow --size 512x64 OUT.png
  menu_label.py patch LAYOUT.ana OUT.ana --set 8="TIME ATTACK":5:plain --set 11="TIME ATTACK":5:glow
      (index:"text":accent_char_index:style). Textures keep their original size and format.

Styles: shadow = flat grey silhouette (locked item); plain = white italic heavy type, black outline, one red accent letter (main menu idle);
        glow  = orange outer glow, pale fill (selected state). Text is right/left anchored
        to match the bbox of the original label's opaque pixels so layout code needs no change.
"""
import argparse, os, re, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gim

FONT_CANDIDATES = ['/usr/share/fonts/opentype/inter/Inter-BlackItalic.otf',
                   '/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyreheros-bolditalic.otf',
                   '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf']


def _font(px):
    for f in FONT_CANDIDATES:
        if os.path.exists(f):
            return ImageFont.truetype(f, px)
    return ImageFont.load_default()


def render(text, size, accent=None, style='plain', box=None):
    if style == 'shadow':  # flat dark silhouette of the glow label (locked / inactive state)
        g = render(text, size, None, 'glow', box)
        a = g.getchannel('A')
        flat = Image.new('RGBA', size, (60, 60, 60, 255)); flat.putalpha(a)
        return flat
    W, H = size
    box = box or (0, 0, W, H)
    bw, bh = box[2] - box[0], box[3] - box[1]
    px = int(bh * 0.95)
    while px > 8:
        f = _font(px)
        l, t, r, b = f.getbbox(text, stroke_width=max(1, px // 12))
        if r - l <= bw and b - t <= bh:
            break
        px -= 1
    sw = max(1, px // 12)
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    l, t, r, b = f.getbbox(text, stroke_width=sw)
    x = box[0] + (bw - (r - l)) // 2 - l
    y = box[1] + (bh - (b - t)) // 2 - t
    if style == 'glow':
        glow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(glow).text((x, y), text, font=f, fill=(255, 120, 20, 255), stroke_width=sw * 3, stroke_fill=(255, 90, 0, 255))
        glow = glow.filter(ImageFilter.GaussianBlur(px / 6))
        layer.alpha_composite(glow)
        d.text((x, y), text, font=f, fill=(255, 236, 200, 255), stroke_width=sw, stroke_fill=(255, 150, 40, 255))
    else:
        d.text((x, y), text, font=f, fill=(255, 255, 255, 255), stroke_width=sw, stroke_fill=(0, 0, 0, 255))
        if accent is not None and 0 <= accent < len(text):
            pre = text[:accent]
            ax = x + f.getlength(pre)
            d.text((ax, y), text[accent], font=f, fill=(230, 20, 20, 255), stroke_width=sw, stroke_fill=(0, 0, 0, 255))
    return layer


def gim_offsets(ana):
    return [m.start() for m in re.finditer(b'MIG.00.1PSP', ana)]


def opaque_bbox(im):
    a = im.getchannel('A').point(lambda v: 255 if v > 24 else 0)
    return a.getbbox()


def main():
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest='cmd', required=True)
    p = sp.add_parser('list'); p.add_argument('ana'); p.add_argument('out')
    p = sp.add_parser('render'); p.add_argument('text'); p.add_argument('--accent', type=int); p.add_argument('--style', default='plain')
    p.add_argument('--size', default='512x64'); p.add_argument('out')
    p = sp.add_parser('patch'); p.add_argument('ana'); p.add_argument('out'); p.add_argument('--set', action='append', default=[])
    p = sp.add_parser('atlas', help='replace one text cell inside a text-atlas texture')
    p.add_argument('ana'); p.add_argument('out'); p.add_argument('--tex', type=int, required=True)
    p.add_argument('--rect', required=True, help='x0,y0,x1,y1 cell to clear and redraw')
    p.add_argument('--text', required=True); p.add_argument('--font', default='/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf')
    p.add_argument('--align', default='left'); p.add_argument('--size', type=int, default=0, help='font px (default: fit cell)')
    a = ap.parse_args()
    if a.cmd == 'render':
        W, H = map(int, a.size.split('x')); render(a.text, (W, H), a.accent, a.style).save(a.out); return
    data = bytearray(open(a.ana, 'rb').read()); offs = gim_offsets(data)
    if a.cmd == 'atlas':
        import struct
        o = offs[a.tex]; glen = struct.unpack_from('<I', data, o + 16 + 4)[0] + 16
        tmpl = bytes(data[o:o + glen]); im = gim.to_image(tmpl)
        x0, y0, x1, y1 = map(int, a.rect.split(','))
        im.paste((0, 0, 0, 0), (x0, y0, x1, y1))
        H = y1 - y0; px = a.size or H
        while px > 6:
            f = ImageFont.truetype(a.font, px); l, t, r, b = f.getbbox(a.text, stroke_width=1)
            if r - l <= (x1 - x0) - 2 and b - t <= H:
                break
            px -= 1
        dr = ImageDraw.Draw(im)
        x = x0 + 1 - l if a.align == 'left' else x0 + ((x1 - x0) - (r - l)) // 2 - l
        dr.text((x, y0 + (H - (b - t)) // 2 - t), a.text, font=f, fill=(254, 254, 254, 255), stroke_width=1, stroke_fill=(3, 3, 3, 255))
        enc = gim.from_image_keep_palette(im, tmpl); assert len(enc) == len(tmpl)
        data[o:o + glen] = enc
        open(a.out, 'wb').write(data); print(f'texture {a.tex}: rect {a.rect} -> "{a.text}" ({px}px)'); return
    if a.cmd == 'list':
        sheet = Image.new('RGBA', (1024, 48 * ((len(offs) + 1) // 2)), (30, 30, 40, 255)); dr = ImageDraw.Draw(sheet)
        for k, o in enumerate(offs):
            im = gim.to_image(bytes(data[o:])); t = im.copy(); t.thumbnail((400, 40))
            x, y = (k % 2) * 512, (k // 2) * 48
            sheet.alpha_composite(t, (x + 70, y)); dr.text((x + 2, y + 10), f'{k} {im.size[0]}x{im.size[1]}', fill='yellow')
        sheet.save(a.out); return
    for spec in a.set:
        idx, rest = spec.split('=', 1)
        m = re.match(r'"?(.*?)"?:(-?\d*):(\w+)$', rest)
        text, acc, style = m.group(1), m.group(2), m.group(3)
        o = offs[int(idx)]
        # GIM length: next GIM start or block size from header
        import struct
        glen = struct.unpack_from('<I', data, o + 16 + 4)[0] + 16
        tmpl = bytes(data[o:o + glen])
        orig = gim.to_image(tmpl)
        box = opaque_bbox(orig) or (0, 0) + orig.size
        if style in ('glow', 'shadow'):  # glow textures carry ~20% padding around the glyphs
            pad = int(orig.size[1] * 0.18); box = (box[0] + pad, box[1] + pad, box[2] - pad, box[3] - pad)
        # English runs longer than kanji/kana: widen the box around its centre (up to 92% of the texture)
        cx = (box[0] + box[2]) // 2; half = max((box[2] - box[0]) // 2, int(orig.size[0] * 0.46))
        box = (max(2, cx - half), box[1], min(orig.size[0] - 2, cx + half), box[3])
        new = render(text, orig.size, int(acc) if acc not in ('', '-1') else None, style, box)
        enc = gim.from_image(new, tmpl)
        assert len(enc) == len(tmpl)
        data[o:o + glen] = enc
        print(f'texture {idx}: "{text}" ({style}) {orig.size}')
    open(a.out, 'wb').write(data)


if __name__ == '__main__':
    main()
