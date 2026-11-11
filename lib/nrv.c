/* NRV2B/2D/2E (UCL) decompressors, 8-bit or LE32 bit buffers. Build: gcc -O2 -shared -fPIC nrv.c -o libnrv.so
 * Returns output length, or negative on error. Port of UCL's n2*_d.c (GPL algorithm, clean reimplementation). */
#include <stdint.h>
#include <stddef.h>

#define GETBIT8(bb) (((bb = (bb & 0x7f) ? bb * 2 : ((unsigned)src[ilen++] * 2 + 1)) >> 8) & 1)
#define GETBIT32(bb) (bc > 0 ? ((bb >> --bc) & 1) : (bc = 31, bb = (uint32_t)src[ilen] | ((uint32_t)src[ilen+1] << 8) | ((uint32_t)src[ilen+2] << 16) | ((uint32_t)src[ilen+3] << 24), ilen += 4, (bb >> 31) & 1))
#define GETBIT(bb) (bits32 ? GETBIT32(bb) : GETBIT8(bb))
#define CHK_IN  if (ilen > slen) return -1;
#define CHK_OUT(n) if (olen + (n) > dlen) return -2;

long nrv_decompress(int method, int bits32, const uint8_t *src, size_t slen, uint8_t *dst, size_t dlen)
{
    uint32_t bb = 0, last_m_off = 1; int bc = 0;
    size_t ilen = 0, olen = 0;
    for (;;) {
        uint32_t m_off, m_len;
        while (GETBIT(bb)) { CHK_IN; CHK_OUT(1); dst[olen++] = src[ilen++]; }
        m_off = 1;
        if (method == 0x2b) {
            do { m_off = m_off * 2 + GETBIT(bb); CHK_IN; } while (!GETBIT(bb));
            if (m_off == 2) m_off = last_m_off;
            else {
                m_off = (m_off - 3) * 256 + src[ilen++];
                if (m_off == 0xffffffffu) break;
                last_m_off = ++m_off;
            }
            m_len = GETBIT(bb); m_len = m_len * 2 + GETBIT(bb);
            if (m_len == 0) { m_len++; do { m_len = m_len * 2 + GETBIT(bb); CHK_IN; } while (!GETBIT(bb)); m_len += 2; }
            m_len += (m_off > 0xd00);
        } else {
            for (;;) { m_off = m_off * 2 + GETBIT(bb); CHK_IN; if (GETBIT(bb)) break; m_off = (m_off - 1) * 2 + GETBIT(bb); }
            if (m_off == 2) { m_off = last_m_off; m_len = GETBIT(bb); }
            else {
                m_off = (m_off - 3) * 256 + src[ilen++];
                if (m_off == 0xffffffffu) break;
                m_len = (m_off ^ 0xffffffffu) & 1; m_off >>= 1; last_m_off = ++m_off;
            }
            if (method == 0x2d) {
                m_len = m_len * 2 + GETBIT(bb);
                if (m_len == 0) { m_len++; do { m_len = m_len * 2 + GETBIT(bb); CHK_IN; } while (!GETBIT(bb)); m_len += 2; }
            } else { /* 0x2e NRV2E */
                if (m_len) m_len = 1 + GETBIT(bb);
                else if (GETBIT(bb)) m_len = 3 + GETBIT(bb);
                else { m_len++; do { m_len = m_len * 2 + GETBIT(bb); CHK_IN; } while (!GETBIT(bb)); m_len += 3; }
            }
            m_len += (m_off > 0x500);
        }
        if (m_off > olen) return -3;
        CHK_OUT(m_len + 1);
        { const uint8_t *p = dst + olen - m_off; dst[olen++] = *p++; do dst[olen++] = *p++; while (--m_len > 0); }
    }
    return (long)olen;
}
