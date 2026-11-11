# M46 TALK — blank / partial talk pages (build 46)
Cause: the talk runner (0xce3b8) dispatches every token on its FIRST BYTE; all A–Z and most a–z are script commands.
Japanese text starts with SJIS bytes, but the English tables (since build 12) start lines with ASCII letters, so
"Not tonight." ran N (page end, 0 chars), "Even an old GT-R…" ran E (end of talk) -> name shown, no text.
Same for "What…" (W), "All right," (A), and block scanners closing early on lines starting with y/v/s/z….
Kenji showed text only because his lines happen to start with a full-width space or '.'.
Emulated GOTO11 on BOOT45PRH ends at line 7 with E set = exactly QA's dump (+0xe8 = 7, +0xf8 = 1).

Fix (BOOT46T, m46_talk_boot.py, region 0x594250–0x5942bf, 3 patched words, 3 new R_26 relocs):
- 0xcdc0c token malloc len+1 -> len+2; 0xcdc40 strcpy -> TCPY: a text-shaped token (first byte 0x21–0x7e,
  second byte present and not '_' or '"') is stored as 0x01 + text, so dispatcher and scanners treat it as text.
- 0xcfa80 text queue 0xb7bac -> TMEAS: skips the 0x01 prefix before measuring/queueing glyphs.
Input BOOT45PRH 73311b21 -> BOOT46T 34eeb1b37393e4fb3bc82eaec4953450.

Verification (emu_talk46.py / sweep.py, game's own prerun 0xcfb34 + update 0xce174 + runner, text calls stubbed):
- old: GOTO11 ends at line 7 with 0 text lines; KENJI11 only " I won again!" (matches QA).
- new: GOTO11/KENJI11/BUNTA11/DAIKI11 queue every line. All 1210 tables: text lines queued 1107 -> 5791; tables with
  no text 776 -> 93 (all 93 contain no text tokens); 0 hangs/errors.
QA: SL vs Goto (Hakone) or Ninomiya (Happogahara), retire -> post-race talk shows full lines; pre-race talks now show
the lines that used to be missing (e.g. Kenji's "All right,").
