#!/usr/bin/env python3
"""PSP UMD ISO tool: info, list, extract, rebuild (LBA-preserving patch-in-place).

Usage:
  iso_tool.py info    GAME.iso
  iso_tool.py list    GAME.iso [--json]
  iso_tool.py extract GAME.iso OUT_DIR
  iso_tool.py patch   GAME.iso OUT.iso --replace ISO_PATH=LOCAL_FILE [...] [--add ISO_PATH=LOCAL_FILE ...]
  iso_tool.py lbadat  LBA.DAT [--check]                # dump / verify a Sega lba.dat (XBB\x01) table
  iso_tool.py rebuild SRC_DIR OUT.iso --template GAME.iso

`patch` writes files back at their original LBAs when they fit (safest: game code
that hard-codes sector offsets keeps working). Files that grow are appended at the
end of the image and their directory record is repointed; PSP games that seek by
LBA inside big archives must be handled by the recompile step instead.
`--add` appends a NEW file at the end of the image, inserts an ISO9660 directory
record into its (existing) parent directory when the directory's allocated sectors
have room (otherwise it warns and skips the record: use --no-dirent to skip on
purpose), and, when the image has USRDIR/lba.dat, appends an lba.dat record
{offset, size, 0, xbb_hash(USRDIR-relative path with backslashes)} and rebuilds the
sorted hash LUT. lba.dat is moved to the end of the image if it outgrows its sectors.
`rebuild` produces a fresh ISO9660 image with PSP_GAME/SYSDIR/EBOOT.BIN placed
first, using the template for volume IDs. Only use it when LBA layout is not
hard-coded by the game.
"""
import argparse, hashlib, json, os, struct, sys
import pycdlib

SECTOR = 2048


def _open(path):
    iso = pycdlib.PyCdlib()
    iso.open(path)
    return iso


def walk(iso):
    out = []
    for dirname, dirlist, filelist in iso.walk(iso_path='/'):
        for f in filelist:
            raw = dirname.rstrip('/') + '/' + f
            rec = iso.get_record(iso_path=raw)
            out.append({'path': raw.replace(';1', ''), 'raw': raw, 'lba': rec.extent_location(), 'size': rec.get_data_length()})
    out.sort(key=lambda r: r['lba'])
    return out


def param_sfo(data):
    magic, ver, ktab, dtab, n = struct.unpack_from('<4sIIII', data, 0)
    if magic != b'\x00PSF':
        return {}
    res = {}
    for i in range(n):
        ko, fmt, ln, mx, do = struct.unpack_from('<HHIII', data, 20 + i * 16)
        key = data[ktab + ko:data.index(b'\0', ktab + ko)].decode()
        raw = data[dtab + do:dtab + do + ln]
        res[key] = struct.unpack('<I', raw)[0] if fmt == 0x0404 else raw.rstrip(b'\0').decode('utf-8', 'replace')
    return res


def _get(iso, fp, inner):
    for cand in (inner, inner + ';1'):
        try:
            iso.get_file_from_iso_fp(fp, iso_path=cand)
            return
        except pycdlib.pycdlibexception.PyCdlibInvalidInput:
            pass
    raise FileNotFoundError(inner)


def read_file(iso_path, inner):
    iso = _open(iso_path)
    import io
    b = io.BytesIO()
    _get(iso, b, inner)
    iso.close()
    return b.getvalue()


def cmd_info(a):
    iso = _open(a.iso)
    files = walk(iso)
    iso.close()
    sfo = param_sfo(read_file(a.iso, '/PSP_GAME/PARAM.SFO'))
    eboot = read_file(a.iso, '/PSP_GAME/SYSDIR/EBOOT.BIN')
    enc = eboot[:4] == b'~PSP'
    info = {
        'disc_id': sfo.get('DISC_ID'), 'title': sfo.get('TITLE'), 'disc_version': sfo.get('DISC_VERSION'),
        'firmware': sfo.get('PSP_SYSTEM_VER'), 'region': sfo.get('REGION'),
        'iso_bytes': os.path.getsize(a.iso), 'file_count': len(files),
        'eboot_encrypted': enc, 'eboot_bytes': len(eboot),
        'eboot_sha1': hashlib.sha1(eboot).hexdigest(),
        'largest_files': sorted(files, key=lambda r: -r['size'])[:15],
    }
    print(json.dumps(info, indent=2, ensure_ascii=False))


def cmd_list(a):
    iso = _open(a.iso)
    files = walk(iso)
    iso.close()
    if a.json:
        print(json.dumps(files, indent=1))
    else:
        for r in files:
            print(f"{r['lba']:>8}  {r['size']:>11}  {r['path']}")


def cmd_extract(a):
    iso = _open(a.iso)
    for r in walk(iso):
        dst = os.path.join(a.out, r['path'].lstrip('/'))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, 'wb') as fp:
            _get(iso, fp, r['path'])
    iso.close()
    with open(os.path.join(a.out, '_iso_layout.json'), 'w') as fp:
        iso = _open(a.iso); json.dump(walk(iso), fp, indent=1); iso.close()
    print('extracted to', a.out)


def xbb_hash(name, seed=0):
    """Sega XBB / lba.dat name hash (IDSS BOOT.BIN 0x140d6c). lba.dat uses the
    USRDIR-relative path with backslashes, e.g. data\\rivaldemo\\rivaldemo.bin.gz."""
    h = acc = 0
    for ch in (name.encode('shift_jis') if isinstance(name, str) else name):
        c = ch - 256 if ch >= 128 else ch
        acc = (acc + c) & 0xffffffff
        s = acc & 31
        t = (((c & 0xffffffff) << s) & 0xffffffff) | ((c >> ((32 - s) & 31)) & 0xffffffff)
        s2 = c & 31
        r = seed if s2 == 0 else (((seed << s2) & 0xffffffff) | (seed >> (32 - s2)))
        h = (h + t + r) & 0xffffffff
    return h


def lba_parse(tbl):
    n = struct.unpack_from('<I', tbl, 4)[0]
    return [struct.unpack_from('<4I', tbl, 0x20 + 16 * i) for i in range(n)]


def lba_build(recs, hdr=None):
    """hdr = original 32-byte header (word 0x08 is 1 in IDSS); count at 0x04 is rewritten."""
    out = bytearray(hdr[:0x20] if hdr else b'XBB\x01' + b'\0' * 28)
    struct.pack_into('<I', out, 4, len(recs))
    for r in recs:
        out += struct.pack('<4I', *r)
    for h, i in sorted((r[3], i) for i, r in enumerate(recs)):
        out += struct.pack('<II', h, i)
    return bytes(out)


def lba_check(tbl):
    """Raise if the table is inconsistent: size, LUT sorted, LUT <-> records."""
    n = struct.unpack_from('<I', tbl, 4)[0]
    assert tbl[:4] == b'XBB\x01' and len(tbl) == 0x20 + 24 * n, 'lba.dat size'
    recs = lba_parse(tbl)
    lut = [struct.unpack_from('<II', tbl, 0x20 + 16 * n + 8 * k) for k in range(n)]
    assert [h for h, _ in lut] == sorted(h for h, _ in lut), 'LUT not sorted'
    assert sorted(i for _, i in lut) == list(range(n)), 'LUT index set'
    for h, i in lut:
        assert recs[i][3] == h, f'LUT entry {h:#x} -> record {i} mismatch'
    return n


def cmd_lbadat(a):
    tbl = open(a.file, 'rb').read()
    n = lba_check(tbl)
    print(f'{a.file}: {n} records, LUT sorted and consistent')
    if not a.check:
        for i, (o, s, z, h) in enumerate(lba_parse(tbl)):
            print(f'{i:5d} lba {o // SECTOR:8d} size {s:10d} hash {h:08x}')


def _dir_records(blob):
    out = []; p = 0
    while p < len(blob):
        ln = blob[p]
        if ln == 0:
            p = (p // SECTOR + 1) * SECTOR; continue
        out.append(bytes(blob[p:p + ln])); p += ln
    return out


def _dir_insert(fp, ext, length, name, lba, size):
    """Insert a file record into directory extent `ext` (length bytes). Records keep their
    order; the new one goes in identifier order after '.'/'..'. Returns False if no room."""
    fp.seek(ext * SECTOR); blob = fp.read(length)
    recs = _dir_records(blob)
    files = [r for r in recs[2:] if not r[25] & 2] or [r for r in recs[2:]]
    if not files:
        return False
    tmpl = files[0]
    tnl = tmpl[32]; tname = tmpl[33:33 + tnl]
    ident = name.encode('ascii')
    if tname.endswith(b';1') and not ident.endswith(b';1'):
        ident += b';1'
    su = tmpl[33 + tnl + (1 - tnl % 2):]               # system-use area (XA etc.), copied as is
    rec = bytearray(33 + len(ident) + (1 - len(ident) % 2)) + su
    rec[0] = len(rec)
    rec[18:33] = tmpl[18:33]
    rec[25] = tmpl[25] & ~2 & 0xff
    struct.pack_into('<I', rec, 2, lba); struct.pack_into('>I', rec, 6, lba)
    struct.pack_into('<I', rec, 10, size); struct.pack_into('>I', rec, 14, size)
    rec[32] = len(ident); rec[33:33 + len(ident)] = ident
    key = lambda r: r[33:33 + r[32]].split(b';')[0]       # ISO9660: byte-wise identifier order
    pos = len(recs)
    for i in range(2, len(recs)):
        if key(recs[i]) > key(bytes(rec)):
            pos = i; break
    recs.insert(pos, bytes(rec))
    out = bytearray()
    for r in recs:
        if len(out) // SECTOR != (len(out) + len(r) - 1) // SECTOR:
            out += b'\0' * ((-len(out)) % SECTOR)
        out += r
    if len(out) > length:
        return False
    out += b'\0' * (length - len(out))
    fp.seek(ext * SECTOR); fp.write(out)
    return True


def _dir_grow(fp, dirs, dpath, extra, end_lba):
    """Move directory `dpath` (upper-case ISO path) to end_lba with `extra` more sectors; fix '.', the
    parent's record and both path tables. Returns the new end_lba."""
    ext, length = dirs[dpath]
    fp.seek(ext * SECTOR); blob = bytearray(fp.read(length))
    nlen = length + extra * SECTOR; next_ = end_lba
    # '.' record
    struct.pack_into('<I', blob, 2, next_); struct.pack_into('>I', blob, 6, next_)
    struct.pack_into('<I', blob, 10, nlen); struct.pack_into('>I', blob, 14, nlen)
    fp.seek(next_ * SECTOR); fp.write(bytes(blob) + b'\0' * (nlen - length))
    # parent record
    parent, name = dpath.rsplit('/', 1)
    pext, plen = dirs[parent or '/']
    fp.seek(pext * SECTOR); pb = bytearray(fp.read(plen)); p = 0; hit = 0
    while p < len(pb):
        ln = pb[p]
        if ln == 0:
            p = (p // SECTOR + 1) * SECTOR; continue
        nl = pb[p + 32]
        if bytes(pb[p + 33:p + 33 + nl]).upper() == name.encode() and struct.unpack_from('<I', pb, p + 2)[0] == ext:
            struct.pack_into('<I', pb, p + 2, next_); struct.pack_into('>I', pb, p + 6, next_)
            struct.pack_into('<I', pb, p + 10, nlen); struct.pack_into('>I', pb, p + 14, nlen); hit += 1
        p += ln
    assert hit == 1, ('parent record', dpath, hit)
    fp.seek(pext * SECTOR); fp.write(pb)
    # path tables (L little-endian, M big-endian)
    fp.seek(16 * SECTOR); pvd = fp.read(SECTOR)
    ptsize = struct.unpack_from('<I', pvd, 132)[0]
    for off, fmt in ((140, '<I'), (144, '<I'), (148, '>I'), (152, '>I')):
        tl = struct.unpack_from(fmt, pvd, off)[0]
        if not tl: continue
        fp.seek(tl * SECTOR); pt = bytearray(fp.read(ptsize)); q = 0; n = 0
        while q < ptsize:
            dl = pt[q]
            if dl == 0: break
            if struct.unpack_from(fmt, pt, q + 2)[0] == ext:
                struct.pack_into(fmt, pt, q + 2, next_); n += 1
            q += 8 + dl + (dl & 1)
        fp.seek(tl * SECTOR); fp.write(pt)
    dirs[dpath] = (next_, nlen)
    print(f'  directory {dpath} moved to LBA {next_} ({nlen} bytes)')
    return end_lba + nlen // SECTOR


def _dir_update(fp, rec, lba, size):
    parent = rec.parent
    pl = parent.extent_location(); plen = parent.get_data_length()
    fp.seek(pl * SECTOR); blob = bytearray(fp.read(plen))
    name = rec.file_identifier(); p = 0
    while p < len(blob):
        ln = blob[p]
        if ln == 0:
            p = (p // SECTOR + 1) * SECTOR; continue
        if bytes(blob[p + 33:p + 33 + blob[p + 32]]) == name:
            struct.pack_into('<I', blob, p + 2, lba); struct.pack_into('>I', blob, p + 6, lba)
            struct.pack_into('<I', blob, p + 10, size); struct.pack_into('>I', blob, p + 14, size)
            fp.seek(pl * SECTOR); fp.write(blob); return
        p += ln
    sys.exit('could not find dir record for ' + name.decode())


def cmd_patch(a):
    """Byte-level patch: copy ISO, overwrite file extents in place."""
    iso = _open(a.iso)
    layout = {r['path'].upper(): r for r in walk(iso)}
    # locate directory records so we can update size / LBA
    recs = {}
    for p, r in layout.items():
        recs[p] = iso.get_record(iso_path=r['raw'])
    dirs = {}
    for dirname, _, _ in iso.walk(iso_path='/'):
        dr = iso.get_record(iso_path=dirname)
        dirs[dirname.rstrip('/').upper() or '/'] = (dr.extent_location(), dr.get_data_length())
    iso.close()
    import shutil
    if os.path.abspath(a.iso) != os.path.abspath(a.out):
        shutil.copyfile(a.iso, a.out)
    end_lba = (os.path.getsize(a.out) + SECTOR - 1) // SECTOR
    moved = []
    lbaonly = []   # files that exist only in lba.dat (added earlier without a directory record)
    with open(a.out, 'r+b') as fp:
        for spec in a.replace:
            inner, local = spec.split('=', 1)
            if inner.upper() not in layout:
                lbaonly.append((inner if inner.startswith('/') else '/' + inner, local)); continue
            inner = inner.upper()
            data = open(local, 'rb').read()
            r = layout[inner]
            alloc = (r['size'] + SECTOR - 1) // SECTOR * SECTOR
            if len(data) <= alloc:
                lba = r['lba']
            else:
                lba = end_lba
                end_lba += (len(data) + SECTOR - 1) // SECTOR
                print(f'WARNING {inner} grew {r["size"]}->{len(data)}; relocated to LBA {lba}. '
                      'Verify the game does not hard-code its sector.', file=sys.stderr)
            fp.seek(lba * SECTOR); fp.write(data)
            pad = (-len(data)) % SECTOR
            fp.write(b'\0' * pad)
            # rewrite directory record (both-endian LBA @2, size @10)
            rec = recs[inner]
            # pycdlib keeps the parent directory extent + offset of the record
            parent = rec.parent
            # scan parent directory extent for this record's name
            pl = parent.extent_location(); plen = parent.get_data_length()
            fp.seek(pl * SECTOR); blob = bytearray(fp.read(plen))
            name = rec.file_identifier()
            off = None; p = 0
            while p < len(blob):
                ln = blob[p]
                if ln == 0:  # records never straddle sectors; skip to next sector
                    p = (p // SECTOR + 1) * SECTOR; continue
                nl = blob[p + 32]
                if bytes(blob[p + 33:p + 33 + nl]) == name:
                    off = p; break
                p += ln
            if off is None:
                sys.exit('could not find dir record for ' + inner)
            struct.pack_into('<I', blob, off + 2, lba); struct.pack_into('>I', blob, off + 6, lba)
            struct.pack_into('<I', blob, off + 10, len(data)); struct.pack_into('>I', blob, off + 14, len(data))
            fp.seek(pl * SECTOR); fp.write(blob)
            moved.append((r['lba'], r['size'], lba, len(data), inner))
            print(f'patched {inner} @LBA {lba} ({len(data)} bytes)')
        # --add: brand-new files appended at the end of the image
        added = []
        for spec in getattr(a, 'add', []) or []:
            inner, local = spec.split('=', 1)
            if not inner.startswith('/'):
                inner = '/' + inner
            if inner.upper() in layout:
                sys.exit(f'already in ISO (use --replace): {inner}')
            data = open(local, 'rb').read()
            lba = end_lba
            end_lba += max(1, (len(data) + SECTOR - 1) // SECTOR)
            fp.seek(lba * SECTOR); fp.write(data); fp.write(b'\0' * ((-len(data)) % SECTOR))
            if not len(data):
                fp.write(b'\0' * SECTOR)
            parent, name = inner.rsplit('/', 1)
            ok = False
            if not getattr(a, 'no_dirent', False):
                d = dirs.get(parent.upper() or '/')
                if d is None:
                    print(f'WARNING no directory {parent} in ISO; {inner} gets no directory record '
                          '(creating directories is not supported)', file=sys.stderr)
                else:
                    ok = _dir_insert(fp, d[0], d[1], name, lba, len(data))
                    if not ok:
                        # directory full: move it to the end of the image with 4 more sectors and retry
                        end_lba = _dir_grow(fp, dirs, parent.upper(), 4, end_lba)
                        d = dirs[parent.upper()]
                        ok = _dir_insert(fp, d[0], d[1], name, lba, len(data))
                        if not ok:
                            sys.exit(f'ERROR directory {parent} still full after growing; {inner} has no directory record')
            added.append((inner, lba, len(data)))
            layout[inner.upper()] = {'path': inner, 'raw': inner, 'lba': lba, 'size': len(data)}
            print(f'added {inner} @LBA {lba} ({len(data)} bytes){"" if ok else " [no directory record]"}')
        # Some games (Sega's Initial D Street Stage) read files through their own sector
        # table instead of the ISO directory: USRDIR/lba.dat = XBB\x01 with 16-byte records
        # {byte offset on disc, size, 0, name hash}. Keep it in sync with every patched file.
        for tp in [p for p in layout if p.endswith('/LBA.DAT')]:
            t = layout[tp]
            fp.seek(t['lba'] * SECTOR); tbl = bytearray(fp.read(t['size']))
            if tbl[:4] != b'XBB\x01':
                continue
            n = struct.unpack_from('<I', tbl, 4)[0]
            for old_lba, old_size, new_lba, new_size, name in moved:
                hit = 0
                for i in range(n):
                    o = 0x20 + 16 * i
                    off, sz = struct.unpack_from('<II', tbl, o)
                    if off == old_lba * SECTOR and sz == old_size:
                        struct.pack_into('<II', tbl, o, new_lba * SECTOR, new_size); hit += 1
                print(f'  {tp}: {name} -> {"updated" if hit else "not listed"}')
            if lbaonly:
                root = tp[:-len('LBA.DAT')]
                recs_ = lba_parse(bytes(tbl))
                for inner, local in lbaonly:
                    if not inner.upper().startswith(root):
                        sys.exit(f'not in ISO: {inner}')
                    rel = inner[len(root):].replace('/', '\\')
                    h = xbb_hash(rel)
                    k = [i for i, r_ in enumerate(recs_) if r_[3] == h]
                    if not k:
                        sys.exit(f'not in ISO or lba.dat: {inner}')
                    off, size, z, _ = recs_[k[0]]
                    data = open(local, 'rb').read()
                    if len(data) <= (size + SECTOR - 1) // SECTOR * SECTOR:
                        noff = off
                    else:
                        noff = end_lba * SECTOR; end_lba += (len(data) + SECTOR - 1) // SECTOR
                    fp.seek(noff); fp.write(data); fp.write(b'\0' * ((-len(data)) % SECTOR))
                    recs_[k[0]] = (noff, len(data), z, h)
                    print(f'patched (lba.dat only) {inner} @LBA {noff // SECTOR} ({len(data)} bytes)')
                    # give it an ISO directory record too (the game stats the file before reading it)
                    par, nm = inner.rsplit('/', 1)
                    d_ = dirs.get(par.upper())
                    if d_ is not None and not _dir_insert(fp, d_[0], d_[1], nm, noff // SECTOR, len(data)):
                        end_lba = _dir_grow(fp, dirs, par.upper(), 1, end_lba)
                        d_ = dirs[par.upper()]
                        if not _dir_insert(fp, d_[0], d_[1], nm, noff // SECTOR, len(data)):
                            sys.exit('directory still full: ' + par)
                    print(f'  + directory record {nm}')
                tbl = bytearray(lba_build(recs_, bytes(tbl[:0x20])))
                lba_check(bytes(tbl))
            if added:
                root = tp[:-len('LBA.DAT')]  # '/PSP_GAME/USRDIR/'
                recs_ = lba_parse(bytes(tbl))
                have = {h for _, _, _, h in recs_}
                for inner, lba, size in added:
                    if not inner.upper().startswith(root):
                        print(f'  {tp}: {inner} is outside {root}; not added to lba.dat'); continue
                    rel = inner[len(root):].replace('/', '\\')
                    h = xbb_hash(rel)
                    if h in have:
                        sys.exit(f'lba.dat hash collision for {rel} ({h:#010x})')
                    have.add(h)
                    recs_.append((lba * SECTOR, size, 0, h))
                    print(f'  {tp}: + {rel} hash {h:#010x} -> record {len(recs_) - 1}')
                tbl = bytearray(lba_build(recs_, bytes(tbl[:0x20])))
                lba_check(bytes(tbl))
            alloc = max(1, (t['size'] + SECTOR - 1) // SECTOR) * SECTOR
            if len(tbl) <= alloc:
                new_lba = t['lba']
            else:
                new_lba = end_lba; end_lba += (len(tbl) + SECTOR - 1) // SECTOR
                print(f'  {tp} grew {t["size"]}->{len(tbl)}; relocated to LBA {new_lba}', file=sys.stderr)
            fp.seek(new_lba * SECTOR); fp.write(tbl); fp.write(b'\0' * ((-len(tbl)) % SECTOR))
            if len(tbl) != t['size'] or new_lba != t['lba']:
                _dir_update(fp, recs[tp], new_lba, len(tbl))
        # update volume space size in PVD (sector 16)
        fp.seek(0, 2); total = (fp.tell() + SECTOR - 1) // SECTOR
        fp.truncate(total * SECTOR)
        fp.seek(16 * SECTOR + 80); fp.write(struct.pack('<I', total) + struct.pack('>I', total))
    print('wrote', a.out)
    _verify_added(a.out, [x[0] for x in added])


def _verify_added(out, added):
    """Re-open the patched ISO: every added file must have an ISO directory record and an lba.dat
    record (by name hash) with the same sector and size. Exit non-zero otherwise."""
    if not added:
        return
    iso = _open(out)
    lay = {r['path'].upper(): r for r in walk(iso)}
    iso.close()
    recs = {}; root = None
    for tp in [p for p in lay if p.endswith('/LBA.DAT')]:
        t = lay[tp]
        with open(out, 'rb') as f:
            f.seek(t['lba'] * SECTOR); tbl = f.read(t['size'])
        if tbl[:4] == b'XBB\x01':
            root = tp[:-len('LBA.DAT')]
            recs = {h: (off, sz) for off, sz, _, h in lba_parse(tbl)}
    bad = 0
    for inner in added:
        r = lay.get(inner.upper())
        if r is None:
            print(f'VERIFY FAIL no directory record: {inner}', file=sys.stderr); bad += 1; continue
        if root and inner.upper().startswith(root):
            e = recs.get(xbb_hash(inner[len(root):].replace('/', '\\')))
            if e is None:
                print(f'VERIFY FAIL no lba.dat record: {inner}', file=sys.stderr); bad += 1
            elif e[0] != r['lba'] * SECTOR or e[1] != r['size']:
                print(f'VERIFY FAIL lba.dat/dir mismatch: {inner}', file=sys.stderr); bad += 1
    print(f'VERIFY added files: {len(added)} checked, {bad} failed')
    if bad:
        sys.exit(f'VERIFY FAILED: {bad} added file(s) missing directory/lba.dat records')


def cmd_rebuild(a):
    tmpl = _open(a.template)
    vol = tmpl.pvd.volume_identifier.decode().strip()
    tmpl.close()
    iso = pycdlib.PyCdlib()
    iso.new(interchange_level=3, vol_ident=vol, sys_ident='PSP GAME')
    files = []
    for root, dirs, fl in os.walk(a.src):
        rel = os.path.relpath(root, a.src).replace(os.sep, '/')
        for d in sorted(dirs):
            iso.add_directory('/' + (rel + '/' if rel != '.' else '') + d.upper())
        for f in fl:
            if f.startswith('_iso_layout'):
                continue
            files.append(((rel + '/' if rel != '.' else '') + f))
    pri = lambda p: (0 if 'SYSDIR' in p.upper() else 1, p)
    for p in sorted(files, key=pri):
        iso.add_file(os.path.join(a.src, p), '/' + p.upper() + ';1')
    iso.write(a.out)
    iso.close()
    print('wrote', a.out)


def main():
    ap = argparse.ArgumentParser(fromfile_prefix_chars='@', description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest='cmd', required=True)
    p = sp.add_parser('info'); p.add_argument('iso'); p.set_defaults(f=cmd_info)
    p = sp.add_parser('list'); p.add_argument('iso'); p.add_argument('--json', action='store_true'); p.set_defaults(f=cmd_list)
    p = sp.add_parser('extract'); p.add_argument('iso'); p.add_argument('out'); p.set_defaults(f=cmd_extract)
    p = sp.add_parser('patch'); p.add_argument('iso'); p.add_argument('out'); p.add_argument('--replace', action='append', default=[])
    p.add_argument('--add', action='append', default=[]); p.add_argument('--no-dirent', action='store_true'); p.set_defaults(f=cmd_patch)
    p = sp.add_parser('lbadat'); p.add_argument('file'); p.add_argument('--check', action='store_true'); p.set_defaults(f=cmd_lbadat)
    p = sp.add_parser('rebuild'); p.add_argument('src'); p.add_argument('out'); p.add_argument('--template', required=True); p.set_defaults(f=cmd_rebuild)
    a = ap.parse_args(); a.f(a)


if __name__ == '__main__':
    main()
