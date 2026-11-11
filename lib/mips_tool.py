#!/usr/bin/env python3
"""Allegrex (MIPS32 LE) helpers for PSP BOOT.BIN / decrypted EBOOT ELFs.

  mips_tool.py info  BOOT.BIN                         # ELF type, segments, module info
  mips_tool.py dis   BOOT.BIN VADDR [COUNT]           # disassemble at virtual address
  mips_tool.py xref  BOOT.BIN VADDR                   # data pointers + lui/addiu|ori pairs that build VADDR
  mips_tool.py ptr   BOOT.BIN VADDR                   # raw u32 occurrences (pointer tables)
  mips_tool.py str   BOOT.BIN TEXT                    # find string, print file offset + vaddr

Addresses: for relocatable PRX-style executables (e_type 0xFFA0) the first PT_LOAD has
vaddr 0 and file offset p_offset; vaddr = file_off - p_offset. PPSSPP loads these at
0x08804000 by default, so a runtime address = 0x08804000 + vaddr (use --runtime to print it).
Code is in .text at the start of the segment; read sh headers with `info`.
Requires: pip install capstone
"""
import struct, sys

try:
    import capstone
except ImportError:
    capstone = None

PPSSPP_BASE = 0x08804000


class Elf:
    def __init__(self, path):
        self.d = open(path, 'rb').read()
        d = self.d
        if d[:4] != b'\x7fELF':
            raise SystemExit('not an ELF (encrypted ~PSP? decrypt via PPSSPP "Dump decrypted EBOOT" or use BOOT.BIN)')
        self.type = struct.unpack_from('<H', d, 0x10)[0]
        phoff, shoff = struct.unpack_from('<II', d, 0x1c)[0], struct.unpack_from('<I', d, 0x20)[0]
        phn = struct.unpack_from('<H', d, 0x2c)[0]
        self.ph = [struct.unpack_from('<8I', d, phoff + 32 * i) for i in range(phn)]
        load = [p for p in self.ph if p[0] == 1]
        self.seg_off, self.seg_va, self.seg_sz = load[0][1], load[0][2], load[0][4]
        shn, shstr = struct.unpack_from('<HH', d, 0x30)
        self.sh = []
        if shoff and shn:
            sh = [struct.unpack_from('<10I', d, shoff + 40 * i) for i in range(shn)]
            names = sh[shstr][4]
            for s in sh:
                nm = d[names + s[0]:d.index(b'\0', names + s[0])].decode('ascii', 'replace')
                self.sh.append((nm, s[1], s[3], s[4], s[5]))  # name, type, addr, offset, size

    def off(self, va):
        return va - self.seg_va + self.seg_off

    def va(self, off):
        return off - self.seg_off + self.seg_va

    def u32(self, va):
        return struct.unpack_from('<I', self.d, self.off(va))[0]


def text_range(e):
    for nm, t, addr, off, sz in e.sh:
        if nm == '.text':
            return addr, addr + sz
    return e.seg_va, e.seg_va + e.seg_sz


def dis(e, va, n=40):
    if not capstone:
        raise SystemExit('pip install capstone')
    md = capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS32 + capstone.CS_MODE_LITTLE_ENDIAN)
    code = e.d[e.off(va):e.off(va) + 4 * n]
    for ins in md.disasm(code, va):
        print(f'{ins.address:08x}  {ins.bytes[::-1].hex()}  {ins.mnemonic:8s} {ins.op_str}')


def xref(e, target):
    hits = []
    lo, hi = text_range(e)
    # pointer-sized data refs
    p = struct.pack('<I', target); i = e.d.find(p)
    while i != -1:
        hits.append(('data', e.va(i))); i = e.d.find(p, i + 1)
    # lui rX, hi16 ; addiu/ori/lw/sw rY, lo16(rX) within the next 16 instructions
    hi16 = (target + 0x8000) >> 16 & 0xffff; lo16 = target & 0xffff
    for va in range(lo, hi, 4):
        w = e.u32(va)
        if w >> 26 == 0x0f and (w & 0xffff) in (hi16, target >> 16):
            rt = (w >> 16) & 31
            for k in range(1, 16):
                w2 = e.u32(va + 4 * k)
                op = w2 >> 26; rs = (w2 >> 21) & 31
                if rs == rt and (w2 & 0xffff) == lo16 and op in (0x09, 0x0d, 0x23, 0x2b, 0x21, 0x25, 0x20, 0x24, 0x28, 0x29, 0x31, 0x39):
                    hits.append(('code', va)); break
    return hits


def main():
    cmd, path = sys.argv[1], sys.argv[2]
    e = Elf(path)
    rt = '--runtime' in sys.argv
    fmt = lambda va: f'{va:#010x}' + (f' (rt {PPSSPP_BASE + va:#010x})' if rt else '')
    if cmd == 'info':
        print(f'e_type={e.type:#x} load: off={e.seg_off:#x} va={e.seg_va:#x} filesz={e.seg_sz:#x}')
        for s in e.sh:
            print(f'  {s[0]:24s} type={s[1]:#x} addr={s[2]:#010x} off={s[3]:#x} size={s[4]:#x}')
    elif cmd == 'dis':
        dis(e, int(sys.argv[3], 0), int(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[4].isdigit() else 40)
    elif cmd in ('xref', 'ptr'):
        t = int(sys.argv[3], 0)
        for kind, va in (xref(e, t) if cmd == 'xref' else [('data', e.va(i)) for i in range(0, len(e.d) - 3, 4) if struct.unpack_from('<I', e.d, i)[0] == t]):
            print(kind, fmt(va))
    elif cmd == 'str':
        s = sys.argv[3].encode('shift_jis'); i = e.d.find(s)
        while i != -1:
            print(f'file {i:#x}  va {fmt(e.va(i))}'); i = e.d.find(s, i + 1)


if __name__ == '__main__':
    main()
