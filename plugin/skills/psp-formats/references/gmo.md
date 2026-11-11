# GMO (OMG.00.1PSP)

Chunk tree (long chunks have children; short chunks are leaves):
```
0x0002/0x0000 file
  0x0003 model
    0x0004 bone      → 0x8041 parent, 0x8048 translate, 0x804e draw-part index (bone→part), 0x8014 bbox
    0x8015 vertex offset/scale: u32 GE-format mask (0x180 = position, 0x3 = uv), then offsets[n], scales[n]
    0x0005 part
      0x0006 mesh   → 0x8061 material index, 0x8066 draw arrays {u32 array_index, u32 prim, u32 verts_per_prim, u32 prim_count}
      0x0007 vertex arrays: +0x10 {u32 GE vertex type, u32 count, u32 morphs, u32 0}, data @ +0x20
    0x0008 material  → 0x8081.. colors, 0x0009 layer → 0x8091 texture index, 0x8094 blend
    0x000A texture   → 0x8012 filename ("akio_bd_n_n_n.gim"), 0x80A0 index
    0x000B motion / 0x000C fcurve (animations)
```
GE vertex type bits: tc 0–1, color 2–4, normal 5–6, position 7–8, weight 9–10, index 11–12, weight count 14–16, morph count 18–20. Components ordered weights, uv, color, normal, position; each aligned to its own size; stride aligned to the largest.
Prim 4 = triangle strip, 3 = triangles. Strips are consecutive in the array (`prim_count` strips of `verts_per_prim`).

Positions: 16-bit normalized → world = n × scale + offset (0x8015). WMP stores (length, height, width) order in the scaled space; detect the long axis when rendering.

Observed in WMP:
- Player-grade cars: ~220–280 KB GMO + 21–25 GIMs (body variants `bd_a/b/c`, bonnet `bn_*`, rear spoiler `rs_*`, muffler `muf_*`, lights `fl_*`, numbers `num`) — the parts system for tuning visuals.
- Story/rival cars: ~45–85 KB GMO + 2 GIMs (e.g. `akio_*` = Akio's S30 "Devil Z", BUILD entry 744 with textures 745–746), about 2.5k triangles, includes a ground shadow quad.

## Initial D Street Stage variant
- Long chunks carry names: `u16 type, u16 hdr_len, u32 size, u32 child_off, u32 data_off, name…`; vertex-array header sits at `data_off − 16`.
- Short-chunk second u16 is 0 (not 8) — preserve it when rewriting.
- Refs are tagged: material `0x82000|i`, texture `0xa2000|i`, bone→part `0x51000|i`, arrays `0x71000|i`.
- 0x8066 has 5 fields: `{arrays_ref, prim|0x100, verts_per_prim, prim_count, start_vertex}`.
- `gmo_tree.py` parses/serializes losslessly (462/462 IDSS+WMP models byte-identical) and `set_part_geometry` swaps a part's mesh for triangle lists.
