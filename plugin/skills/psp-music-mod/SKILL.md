---
name: psp-music-mod
description: Replace, add, or let players pick custom music in PSP games — AT3/ATRAC3plus encoding requirements, swapping tracks in place, extending BGM path tables, unlock flags, and building a custom-song loader/player. Use for "add more music", "custom songs", "update the track player".
---

# Music modding

## Audio format
- `.at3` = RIFF WAVE with ATRAC3 (fmt tag 0x0270) or ATRAC3plus (0xFFFE + GUID). Check the original: bitrate, channels, sample rate (44.1 kHz), and the `smpl` chunk loop points — copy loop settings so race BGM loops.
- Decode for reference: `ffmpeg -i in.at3 out.wav`. Encode: Sony `at3tool` (`at3tool -e -br 132 in.wav out.at3`, plus `-wholeloop` or `-loop start end` when needed). It is not redistributable; the user provides it. Keep bitrates equal to the originals (memory and streaming budgets).

## Levels of change
1. **Replace** (no code): new song encoded to the same codec/bitrate, written under the original filename. Keep duration in a similar range; file size may grow if the disc layout allows (`iso_tool.py patch` relocates when needed).
2. **Add songs** (code): extend the BGM path pointer table + count, the display-name list, and unlock/selection data (psp-code-patcher). Initial D: race BGM paths at BOOT.BIN file ~0x2426dc (pointer table ~0x1eb56c), short "S" previews in `bgm/hp/` for the Project D homepage sound test, and an existing "song added to BGM" unlock message to reuse.
3. **Custom songs** (code + PRX): a loader that scans `ms0:/PSP/COMMON/<GAME>/BGM/*.at3` (or `USRDIR/custom/`) at boot, appends entries to the in-memory table, and shows filenames in the player UI. Implement as a small PRX hooking the table builder and the player's draw routine.

## Initial D Street Stage inventory
`data/sound/bgm/race/` 19 Super Eurobeat tracks (~400–540 KB each), `bgm/hp/` 19 preview versions, `bgm/rival/` 29 rival themes, `bgm/misc/` menu/result/win/lose jingles, engine banks in `se/engine/`.
