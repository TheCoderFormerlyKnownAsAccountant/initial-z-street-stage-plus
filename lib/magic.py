"""File-type guesser for PSP game data blobs."""
import struct

MAGICS = [
    (b'MIG.00.1PSP', 'gim-texture'), (b'MIG.', 'gim-texture'), (b'OMG.00.1PSP', 'gmo-model'),
    (b'\x89PNG', 'png'), (b'RIFF', 'riff-at3/wav'), (b'PSMF', 'pmf-video'), (b'\x00PSF', 'sfo'),
    (b'\x7fELF', 'elf'), (b'~PSP', 'prx-encrypted'), (b'XMD\x00', 'xmd-container'),
    (b'\x00\xe9UCL', 'ucl-packed'), (b'PPHD', 'sony-phd-soundbank'), (b'VAGp', 'vag-audio'),
    (b'SSCF', 'sscf-audio'), (b'MWo3', 'mwo3-font'), (b'PGF0', 'pgf-font'), (b'AFS\x00', 'afs-archive'),
    (b'CPK ', 'cri-cpk'), (b'@UTF', 'cri-utf'), (b'TIM2', 'tim2-texture'), (b'GIM ', 'gim-texture'),
    (b'MThd', 'midi'), (b'SEQp', 'sony-seq'), (b'pBAV', 'sony-bav'), (b'NJTL', 'ninja-model'),
    (b'GJCM', 'ninja-model'), (b'NJCM', 'ninja-model'), (b'GBIX', 'ninja-texture'), (b'PVRT', 'pvr-texture'),
    (b'GVRT', 'gvr-texture'), (b'MTL\x00', 'material'), (b'DDS ', 'dds'), (b'FPAC', 'fpac'), (b'PAK', 'pak'),
]


def sjis_ratio(data, n=4096):
    s = data[:n]
    if not s:
        return 0.0
    hits, i = 0, 0
    while i < len(s) - 1:
        b = s[i]
        if (0x81 <= b <= 0x9f or 0xe0 <= b <= 0xef) and (0x40 <= s[i + 1] <= 0xfc):
            hits += 2; i += 2
        elif 0x20 <= b < 0x7f:
            hits += 1; i += 1
        else:
            i += 1
    return hits / len(s)


def guess(data):
    for m, name in MAGICS:
        if data.startswith(m):
            return name
    if len(data) >= 8:
        # offset-table container: first u32 is a small count followed by ascending offsets
        n = struct.unpack_from('<I', data, 0)[0]
        if 0 < n < 4096 and len(data) >= 4 + 4 * n:
            offs = struct.unpack_from(f'<{min(n, 64)}I', data, 4)
            if all(offs[i] <= offs[i + 1] for i in range(len(offs) - 1)) and offs[-1] <= len(data) and offs[0] >= 4 + 4 * min(n, 64) - 4 * (min(n, 64) - n if n < 64 else 0):
                return f'offset-table({n})'
    if sjis_ratio(data) > 0.85:
        return 'text-sjis'
    return 'unknown:' + data[:4].hex()
