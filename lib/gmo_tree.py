#!/usr/bin/env python3
"""Lossless GMO chunk tree: parse -> edit -> serialize (sizes/offsets recomputed).

Long chunk (type < 0x8000):  u16 type, u16 hdr_len (0 means 16), u32 size, u32 child_off, u32 data_off,
                             then hdr_len-16 bytes (usually a NUL-padded name), then
                             `pre` bytes (vertex-array header + data for type 7), then children.
Short chunk (type & 0x8000): u16 type, u16 8, u32 size, payload.

    t = GmoTree.load(bytes); t.find(5) -> parts; node.name; t.dump() -> bytes
Round-trips byte-identically on Initial D Street Stage and Wangan Midnight Portable models.
Also provides `encode_part_geometry` to replace a part's mesh with a triangle list.
"""
import struct

MAGIC = b'OMG.00.1PSP\0'


class Node:
    __slots__ = ('type', 'hdr', 'pre', 'children', 'payload', 'data_rel', 'flags')

    def __init__(self, type_, hdr=b'', pre=b'', children=None, payload=b'', data_rel=None, flags=0):
        self.type, self.hdr, self.pre = type_, hdr, pre
        self.children = children if children is not None else []
        self.payload, self.data_rel, self.flags = payload, data_rel, flags

    @property
    def short(self):
        return bool(self.type & 0x8000)

    @property
    def name(self):
        return self.hdr[16:].split(b'\0')[0].decode('ascii', 'replace') if len(self.hdr) > 16 else ''

    def u32s(self):
        return list(struct.unpack_from(f'<{len(self.payload) // 4}I', self.payload))

    def walk(self, depth=0):
        yield depth, self
        for c in self.children:
            yield from c.walk(depth + 1)

    def find(self, t):
        return [n for _, n in self.walk() if n.type == t]

    def size(self):
        if self.short:
            return 8 + len(self.payload)
        return len(self.hdr) + len(self.pre) + sum(c.size() for c in self.children)

    def dump(self):
        if self.short:
            return struct.pack('<HHI', self.type, self.flags, 8 + len(self.payload)) + self.payload
        body = b''.join(c.dump() for c in self.children)
        size = len(self.hdr) + len(self.pre) + len(body)
        child_off = len(self.hdr) + len(self.pre) if self.children or not self.pre else size
        if self.data_rel is None:
            data_off = 0
        elif self.data_rel == 'child':
            data_off = child_off
        else:
            data_off = self.data_rel
        hl = struct.unpack_from('<H', self.hdr, 2)[0]
        h = bytearray(self.hdr)
        struct.pack_into('<HHIII', h, 0, self.type, hl, size, child_off, data_off)
        return bytes(h) + self.pre + body


def _parse(d, off, end):
    out = []
    while off + 8 <= end:
        t, hl, sz = struct.unpack_from('<HHI', d, off)
        if sz < 8 or off + sz > end:
            break
        if t & 0x8000:
            out.append(Node(t, payload=d[off + 8:off + sz], flags=hl))
        else:
            hlen = hl if hl else 16
            co, do = struct.unpack_from('<II', d, off + 8)
            hdr = d[off:off + hlen]
            co = co if co else hlen
            pre = d[off + hlen:off + co] if co > hlen else b''
            if co >= sz:  # leaf with raw data (vertex arrays)
                pre = d[off + hlen:off + sz]; kids = []
            else:
                kids = _parse(d, off + co, off + sz)
            data_rel = None if do == 0 else ('child' if do == co and co < sz else do)
            out.append(Node(t, hdr, pre, kids, data_rel=data_rel))
        off += sz
    return out


class GmoTree:
    def __init__(self, head, roots, tail):
        self.head, self.roots, self.tail = head, roots, tail

    @classmethod
    def load(cls, d):
        if not d.startswith(b'OMG.'):
            raise ValueError('not GMO')
        roots = _parse(d, 16, len(d))
        used = 16 + sum(r.size() for r in roots)
        return cls(d[:16], roots, d[used:])

    def dump(self):
        return self.head + b''.join(r.dump() for r in self.roots) + self.tail

    def walk(self):
        for r in self.roots:
            yield from r.walk()

    def find(self, t):
        return [n for _, n in self.walk() if n.type == t]

    def model(self):
        return self.find(3)[0]


def mk_short(t, payload):
    return Node(t, payload=payload)


def bbox_payload(pts):
    mn = [min(p[i] for p in pts) for i in range(3)]; mx = [max(p[i] for p in pts) for i in range(3)]
    return struct.pack('<6f', *mn, *mx)


def encode_vertices(vt, verts, uv_off=(0.0, 0.0), uv_scale=(1.0, 1.0)):
    """verts: list of (pos(3), normal(3), uv(2)). Supports tc 16-bit, normal 16-bit, pos float (Initial D layout)."""
    import gmo
    lay, stride = gmo.vtx_layout(vt)
    out = bytearray(stride * len(verts))
    for i, (p, n, uv) in enumerate(verts):
        o = i * stride
        if 'uv' in lay:
            off, csz, _ = lay['uv']
            vals = [min(max((uv[k] - uv_off[k]) / (uv_scale[k] or 1), 0.0), 1.9999) for k in range(2)]
            if csz == 2:
                struct.pack_into('<HH', out, o + off, *[int(round(v * 32768)) & 0xffff for v in vals])
            elif csz == 4:
                struct.pack_into('<2f', out, o + off, *vals)
        if 'n' in lay:
            off, csz, _ = lay['n']
            if csz == 2:
                struct.pack_into('<3h', out, o + off, *[int(max(-1, min(1, c)) * 32767) for c in n])
            elif csz == 1:
                struct.pack_into('<3b', out, o + off, *[int(max(-1, min(1, c)) * 127) for c in n])
            else:
                struct.pack_into('<3f', out, o + off, *n)
        off, csz, _ = lay['p']
        if csz != 4:
            raise ValueError('only float positions supported for writing')
        struct.pack_into('<3f', out, o + off, *p)
    return bytes(out)


def set_part_geometry(part, verts, tris_by_mat, vt=None):
    """Replace a 0x0005 part's mesh/arrays with indexed-free triangle lists.
    tris_by_mat: [(material_ref_u32, [(i,j,k), ...]), ...]. Each material becomes one 0x0006 mesh."""
    meshes = [c for c in part.children if c.type == 6]
    arrays = [c for c in part.children if c.type == 7]
    if not meshes or not arrays:
        raise ValueError('part has no mesh/arrays to use as template')
    arr_t = arrays[0]
    old_vt, _, morph, z = struct.unpack_from('<4I', arr_t.pre, 0)
    vt = vt if vt is not None else old_vt
    mesh_t = meshes[0]
    ref_draw = [c for c in mesh_t.children if c.type == 0x8066][0]
    arr_ref = struct.unpack_from('<I', ref_draw.payload, 0)[0] & ~0xfff
    new_kids = []
    for c in part.children:
        if c.type == 0x8014:
            pts = [v[0] for v in verts] or [(0, 0, 0)]
            new_kids.append(mk_short(0x8014, bbox_payload(pts)))
        elif c.type in (6, 7):
            continue
        else:
            new_kids.append(c)
    flat = []
    for mi, (mref, tris) in enumerate(tris_by_mat):
        start = len(flat)
        for tri in tris:
            flat += [verts[k] for k in tri]
        m = Node(6, mesh_t.hdr, mesh_t.pre, [], data_rel=mesh_t.data_rel)
        for c in mesh_t.children:
            if c.type == 0x8061:
                m.children.append(mk_short(0x8061, struct.pack('<I', mref)))
            elif c.type == 0x8066:
                continue
            else:
                m.children.append(c)
        m.children.append(mk_short(0x8066, struct.pack('<5I', arr_ref | 0, 0x103, len(tris) * 3, 1, start)))
        new_kids.append(m)
    data = encode_vertices(vt, flat)
    a = Node(7, arr_t.hdr, struct.pack('<4I', vt, len(flat), morph, z) + data, [], data_rel=arr_t.data_rel)
    new_kids.append(a)
    part.children = new_kids
    return len(flat)
