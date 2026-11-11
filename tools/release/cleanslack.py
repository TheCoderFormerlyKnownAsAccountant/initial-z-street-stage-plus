"""Fill every byte of the image that no file, directory, path table or lba.dat record uses with the stock disc's byte
at the same offset (zero past the stock size), and zero the tail of each file's last sector. Leftovers of older builds
(e.g. earlier music) cannot survive in unused space."""
import os, sys
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import iso_tool as T
iso_p, stock_p = sys.argv[1], sys.argv[2]
S = 2048
iso = T._open(iso_p)
used = []                                   # (start_byte, end_byte) of real data
files = list(T.walk(iso))
for r in files:
    if r['size']: used.append((r['lba'] * S, r['lba'] * S + r['size']))
for dirpath, dirs, fs in iso.walk(iso_path='/'):
    rec = iso.get_record(iso_path=dirpath)
    used.append((rec.extent_location() * S, rec.extent_location() * S + rec.get_data_length()))
pvd = iso.pvd
used.append((0, 32 * S))                    # system area + volume descriptors
for loc in (pvd.path_table_location_le, pvd.path_table_location_be, getattr(pvd, 'optional_path_table_location_le', 0), getattr(pvd, 'optional_path_table_location_be', 0)):
    if loc: used.append((loc * S, loc * S + pvd.path_tbl_size))
iso.close()
lr = [r for r in files if r['path'].upper() == '/PSP_GAME/USRDIR/LBA.DAT'][0]
with open(iso_p, 'rb') as f:
    f.seek(lr['lba'] * S); tbl = f.read(lr['size'])
for o, s, z, h in T.lba_parse(tbl):
    if s: used.append((o, o + s))
size = os.path.getsize(iso_p); stock_size = os.path.getsize(stock_p)
used = [(max(0, a), min(b, size)) for a, b in used if 0 <= a < size]
used.sort(); free = []; pos = 0
for a, b in used:
    if a > pos: free.append((pos, a))
    pos = max(pos, b)
if pos < size: free.append((pos, size))
changed = 0; total = 0
with open(iso_p, 'r+b') as f, open(stock_p, 'rb') as st:
    big = sorted(free, key=lambda x: x[0] - x[1])[:5]
    print('largest unused ranges', [(a // S, (b - a)) for a, b in big])
    for a0, b0 in free:
        total += b0 - a0
        for a in range(a0, b0, 1 << 22):
            b = min(b0, a + (1 << 22))
            f.seek(a); cur = f.read(b - a)
            want = b''
            if a < stock_size:
                st.seek(a); want = st.read(max(0, min(b, stock_size) - a))
            want += b'\0' * ((b - a) - len(want))
            if cur != want:
                changed += b - a
                f.seek(a); f.write(want)
print('unused ranges', len(free), 'bytes', total, 'bytes in rewritten chunks', changed)
